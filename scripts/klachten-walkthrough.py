#!/usr/bin/env python3
"""
Walks the Den Haag eerstelijns-klachten process end to end through the GZAC REST API,
the same way the frontend does, as the demo user that owns each task.

Usage:
  scripts/klachten-walkthrough.py --route informeel-coordinator [--dienst SZW] [--terugkoppeling off]
  scripts/klachten-walkthrough.py --route all

Routes:
  informeel-coordinator  coordinator handles the complaint (--zaakbehandelaar MIJZELF|ANDERE_KLACHTENCOORDINATOR)
  informeel-behandelaar  behandelaar of the dienst handles it, coordinator checks it
  formeel                melder disagrees with the informal solution, so it is handled formally
  commissie              coordinator hands the complaint over to the klachtencommissie

Needs: python3, docker (the demo stack running via ./run.sh). Only the standard library is used.
"""

import argparse
import base64
import datetime
import hashlib
import hmac
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

GZAC = "http://localhost:8080"
KEYCLOAK = "http://localhost:8081/auth/realms/valtimo/protocol/openid-connect/token"
OPEN_ZAAK = "http://localhost:8001"
OPEN_ZAAK_CLIENT_ID = "valtimo_client"
OPEN_ZAAK_SECRET = "e09b8bc5-5831-4618-ab28-41411304309d"
CASE = "eerstelijns-klachten"
MAIN_PROCESS = "klachten-registratie-en-afhandeling-eerstelijns-klachten"
BACKEND_CONTAINER = "authzen-gzac-backend"
DB_CONTAINER = "authzen-gzac-database"

ROUTES = ["informeel-coordinator", "informeel-behandelaar", "formeel", "commissie"]
DIENSTEN = ["OCW", "SZW", "DPZ", "DSB", "DSO", "DBV", "BSD", "GGD", "VTH"]
AUTORISATIEGROEPEN_OCW = {
    "JGZ": "AUTORISATIEGROEPEN_OCW_JGZ_JEUGDGEZONDHEIDSZORG",
    "JH": "AUTORISATIEGROEPEN_OCW_JEUGDHULP",
}
# Same mapping as the calculated field pv.klachtteam in the toewijzen-zaak-aan-zaakbehandelaar form.
KLACHTTEAM = {"BSD": "BSD_BESTUURSDIENST", "DBV": "DBV", "DPZ": "DPZ", "DSB": "DSB_DIENST_STADSBEHEER", "DSO": "DSO", "SZW": "SZW"}
BEHANDELAAR_USER = {
    "BSD_BESTUURSDIENST": "klachten-behandelaar-bsd", "DBV": "klachten-behandelaar-dbv",
    "DPZ": "klachten-behandelaar-dpz", "DSB_DIENST_STADSBEHEER": "klachten-behandelaar-dsb",
    "DSO": "klachten-behandelaar-dso", "SZW": "klachten-behandelaar-szw",
    "OCW_ALGEMEEN": "klachten-behandelaar-ocw", "OCW_JGZ": "klachten-behandelaar-ocw-jgz",
    "OCW_JH": "klachten-behandelaar-ocw-jh",
}
STEP_TIMEOUT = 45
# Backend ERROR lines that come from Valtimo itself, not from the klachten configuration.
KNOWN_BACKEND_NOISE = {
    "TaskUpdateListener": "Valtimo SSE TaskUpdateListener looks up a process instance that has just ended",
}
MAX_STEPS = 40


class StepError(Exception):
    pass


# ---- output -------------------------------------------------------------------------------------

class Report:
    def __init__(self, verbose):
        self.verbose = verbose
        self.failures = []
        self.warnings = []

    def ok(self, msg):
        print(f"  ✅ {msg}")

    def fail(self, msg):
        self.failures.append(msg)
        print(f"  ❌ {msg}")

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)
            print(f"  ⚠️  {msg}")

    def debug(self, msg):
        if self.verbose:
            print(f"     {msg}")


# ---- HTTP ---------------------------------------------------------------------------------------

def http(method, url, token=None, body=None, headers=None, raw=None, content_type=None):
    hdrs = dict(headers or {})
    data = None
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    if raw is not None:
        data = raw
        hdrs["Content-Type"] = content_type
    elif body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            text = resp.read().decode()
            return resp.status, (json.loads(text) if text.strip() else None)
    except urllib.error.HTTPError as e:
        text = e.read().decode()
        try:
            return e.code, json.loads(text)
        except ValueError:
            return e.code, text


_tokens = {}


def token(user):
    if user not in _tokens:
        form = urllib.parse.urlencode({
            "client_id": "valtimo-console", "grant_type": "password", "username": user, "password": user,
        }).encode()
        status, body = http("POST", KEYCLOAK, raw=form, content_type="application/x-www-form-urlencoded")
        if status != 200:
            raise StepError(f"login as {user} failed: {status} {body}")
        _tokens[user] = body["access_token"]
    return _tokens[user]


def user_id(user):
    """Keycloak id of the user (the token subject), which task assignment expects."""
    payload = token(user).split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))["sub"]


def api(method, path, user, body=None, **kw):
    return http(method, GZAC + path, token(user), body, **kw)


def api_ok(method, path, user, body=None, **kw):
    status, resp = api(method, path, user, body, **kw)
    if status >= 300:
        raise StepError(f"{method} {path} as {user} → {status}: {short(resp)}")
    return resp


def short(obj, limit=400):
    text = obj if isinstance(obj, str) else json.dumps(obj)
    return text if len(text) <= limit else text[:limit] + "…"


# ---- database / docker --------------------------------------------------------------------------

def psql(sql):
    env = subprocess.run(["docker", "exec", DB_CONTAINER, "sh", "-c", 'echo "$POSTGRES_USER $POSTGRES_DB"'],
                         capture_output=True, text=True, check=True).stdout.split()
    out = subprocess.run(["docker", "exec", DB_CONTAINER, "psql", "-U", env[0], "-d", env[1], "-At", "-F", "\t", "-c", sql],
                         capture_output=True, text=True, check=True).stdout
    return [line.split("\t") for line in out.splitlines() if line]


def open_tasks(document_id):
    """Open tasks of all process instances (incl. call activities) of the case: (taskId, processKey, taskKey)."""
    rows = psql(f"""
        select t.id_, d.key_, t.task_def_key_
        from act_ru_task t
        join act_re_procdef d on d.id_ = t.proc_def_id_
        join act_ru_execution e on e.id_ = t.proc_inst_id_
        left join act_ru_execution r on r.id_ = e.root_proc_inst_id_
        where e.business_key_ = '{document_id}' or r.business_key_ = '{document_id}'
        order by t.create_time_""")
    return [tuple(r) for r in rows]


def running_processes(document_id):
    rows = psql(f"""
        select distinct d.key_
        from act_ru_execution e
        join act_re_procdef d on d.id_ = e.proc_def_id_
        left join act_ru_execution r on r.id_ = e.root_proc_inst_id_
        where e.parent_id_ is null and (e.business_key_ = '{document_id}' or r.business_key_ = '{document_id}')""")
    return [r[0] for r in rows]


def incidents(document_id):
    return psql(f"""
        select i.activity_id_, regexp_replace(coalesce(i.incident_msg_, ''), '\\s+', ' ', 'g')
        from act_ru_incident i
        join act_ru_execution e on e.id_ = i.proc_inst_id_
        left join act_ru_execution r on r.id_ = e.root_proc_inst_id_
        where e.business_key_ = '{document_id}' or r.business_key_ = '{document_id}'""")


def backend_errors(since):
    """ERROR log entries since the given time, each with its stack trace (lines up to the next log entry)."""
    logs = subprocess.run(["docker", "logs", "--since", since, BACKEND_CONTAINER], capture_output=True, text=True)
    blocks, current = [], None
    for line in (logs.stdout + logs.stderr).splitlines():
        if line[:4].isdigit() and line[4:5] == "-":
            current = [line] if " ERROR " in line else None
            if current:
                blocks.append(current)
        elif current is not None:
            current.append(line)
    return ["\n".join(block) for block in blocks]


# ---- Open Zaak ----------------------------------------------------------------------------------

def open_zaak_token():
    def b64(data):
        return base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode()).rstrip(b"=")
    header = b64({"alg": "HS256", "typ": "JWT"})
    payload = b64({"iss": OPEN_ZAAK_CLIENT_ID, "client_id": OPEN_ZAAK_CLIENT_ID, "iat": int(time.time()),
                   "user_id": "klachten-walkthrough", "user_representation": "klachten-walkthrough"})
    signature = base64.urlsafe_b64encode(
        hmac.new(OPEN_ZAAK_SECRET.encode(), header + b"." + payload, hashlib.sha256).digest()).rstrip(b"=")
    return (header + b"." + payload + b"." + signature).decode()


def open_zaak_get(url):
    url = url.replace("host.docker.internal", "localhost")
    status, body = http("GET", url, open_zaak_token(), headers={"Accept-Crs": "EPSG:4326"})
    if status != 200:
        raise StepError(f"Open Zaak GET {url} → {status}: {short(body)}")
    return body


def zaak_state(document_id):
    rows = psql(f"select zaak_instance_url from zaak_instance_link where document_id = '{document_id}'")
    if not rows:
        return None
    zaak = open_zaak_get(rows[0][0])
    status = resultaat = None
    if zaak.get("status"):
        status = open_zaak_get(open_zaak_get(zaak["status"])["statustype"])["omschrijving"]
    if zaak.get("resultaat"):
        resultaat = open_zaak_get(open_zaak_get(zaak["resultaat"])["resultaattype"])["omschrijving"]
    return {"url": rows[0][0], "identificatie": zaak.get("identificatie"), "status": status, "resultaat": resultaat}


# ---- form helpers -------------------------------------------------------------------------------

def now(days=0):
    return (datetime.datetime.now().astimezone() + datetime.timedelta(days=days)).isoformat(timespec="seconds")


def set_path(data, path, value):
    parts = path.split(".")
    for part in parts[:-1]:
        data = data.setdefault(part, {})
    data[parts[-1]] = value


def nest(flat):
    """{'a.b': 1, 'pv.x': 2} → {'a': {'b': 1}, 'pv': {'x': 2}}; keys like 'pv:x' stay as they are."""
    data = {}
    for key, value in flat.items():
        if value is not None:
            set_path(data, key, value)
    return data


def merge(base, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def prefilled_data(form):
    """Collects the values Valtimo prefilled into the form definition (defaultValue), nested like Form.io data."""
    data = {}

    def walk(components, prefix):
        for c in components or []:
            if not isinstance(c, dict):
                continue
            key = c.get("key")
            path = prefix
            if c.get("type") == "container" and key:
                path = prefix + [key]
            elif c.get("input") and key and c.get("type") not in ("button", "datagrid"):
                value = c.get("defaultValue")
                if value not in (None, "", [], {}):
                    set_path(data, ".".join(prefix + [key]), value)
            walk(c.get("components"), path)
            for col in c.get("columns") or []:
                walk(col.get("components"), path)
    walk(form.get("components"), [])
    return data


class Context:
    def __init__(self, args, report):
        self.args = args
        self.report = report
        self.route = args.route
        self.dienst = args.dienst
        self.terugkoppeling = args.terugkoppeling == "on"
        self.document_id = None
        self.choice_cache = {}
        self.coordinator = {"GGD": "klachten-coordinator-ggd", "VTH": "klachten-coordinator-vth"}.get(
            self.dienst, "klachten-coordinator")
        self.autorisatiegroep = AUTORISATIEGROEPEN_OCW.get(args.autorisatiegroep) if self.dienst == "OCW" else None
        if self.dienst == "OCW":
            self.klachtteam = {"JGZ": "OCW_JGZ", "JH": "OCW_JH"}.get(args.autorisatiegroep, "OCW_ALGEMEEN")
        else:
            self.klachtteam = KLACHTTEAM.get(self.dienst)
        self.behandelaar = BEHANDELAAR_USER.get(self.klachtteam)
        self.zaakbehandelaar = "EEN_KLACHTENBEHANDELAAR_VAN_DE_DIENST" if self.route == "informeel-behandelaar" \
            else args.zaakbehandelaar
        self.melder_akkoord = "NEE" if self.route == "formeel" else "JA"
        self.commissie_started = False

    # Choice fields (dataSrc url, no valueProperty) store the whole choice-field value object.
    def choice(self, key, preferred=None, required=False):
        if key not in self.choice_cache:
            status, body = api("GET", f"/api/v1/choice-fields/name/{urllib.parse.quote(key)}", self.coordinator)
            self.choice_cache[key] = body.get("choiceFieldValues", []) if status == 200 and isinstance(body, dict) else None
            if self.choice_cache[key] is None:
                self.report.warn(f"choice field {key} not found (HTTP {status})")
            elif len(self.choice_cache[key]) <= 1:
                self.report.warn(f"choice field {key} has only {len(self.choice_cache[key])} value(s)")
        values = self.choice_cache[key] or []
        for v in values:
            if preferred and v.get("name") == preferred:
                return v
        if preferred and values:
            self.report.warn(f"choice field {key} has no value {preferred}, using {values[0].get('name')}")
        if not values and required:
            raise StepError(f"required choice field {key} has no values")
        return values[0] if values else None

    def user_by_role(self, role, prop):
        status, body = api("GET", f"/api/v1/users/authority/{role}", self.coordinator)
        if status != 200 or not body:
            self.report.warn(f"no users with role {role} (HTTP {status})")
            return None
        return body[0].get(prop)

    def upload(self, name, process_instance_id=None):
        """Uploads a small text file the way the documenten-api-file component does (POST /resource/temp)."""
        status, types = api("GET", f"/api/v1/document/{self.document_id}/zaaktype/documenttype", self.coordinator)
        iot = next((t["url"] for t in types or [] if t.get("name") == "Bijlage"), (types or [{}])[0].get("url")) \
            if status == 200 else None
        boundary = uuid.uuid4().hex
        fields = {
            "bestandsnaam": f"{name}.txt", "titel": name, "beschrijving": f"{name} (walkthrough)",
            "informatieobjecttype": iot, "vertrouwelijkheidaanduiding": "zaakvertrouwelijk",
            "taal": "nld", "status": "definitief", "auteur": "Klachten walkthrough",
            "creatiedatum": datetime.date.today().isoformat(), "processInstanceId": process_instance_id,
        }
        parts = []
        for k, v in fields.items():
            if v:
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}.txt"\r\n'
                     f'Content-Type: text/plain\r\n\r\n'.encode() + f"{name}\nGegenereerd door de klachten walkthrough.\n".encode()
                     + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        status, body = api("POST", "/api/v1/resource/temp", self.coordinator, raw=b"".join(parts),
                           content_type=f"multipart/form-data; boundary={boundary}")
        if status >= 300:
            raise StepError(f"upload {name} → {status}: {short(body)}")
        return [body]


# ---- form data per task -------------------------------------------------------------------------
# Each builder returns the data the user would enter. Values the browser calculates (calculateValue)
# are set here as well, because the API does not run the form logic.

def onderzoek(ctx, prefix, oordeel="ONGEGROND"):
    return {
        f"{prefix}.oordeel": ctx.choice("OORDEEL", oordeel, required=True),
        f"{prefix}.gemotiveerdOordeel.omschrijving": "De gemeente heeft de afspraak niet nagekomen. Excuses aangeboden.",
    }


def data_start(ctx):
    return nest({
        "klacht.datumOntvangst": now(-1),
        "klacht.korteOmschrijvingMelding": "Afvalcontainer al drie weken niet geleegd",
        "klacht.toelichtingMelding": "Ondanks twee meldingen is de ondergrondse container in de Spuistraat niet geleegd.",
        "melder.soortMelder": "INWONER",
        "melder.personalia.voornaam": "Jan",
        "melder.personalia.achternaam": "Jansen",
        "melder.contactgegevens.communicatieViaPost": False,
        "melder.contactgegevens.email": "jan.jansen@example.com",
        "melder.contactgegevens.telefoonnummer": "0612345678",
        "melder.adres.straat": "Spuistraat", "melder.adres.huisnummer": 70,
        "melder.adres.postcode": "2511BT", "melder.adres.woonplaats": "Den Haag",
        "routeBurgemeesterWethouderkenmerk": False,
        "pv.geenOntvangstNaarMelder": False,
        "pv.isKlachtHandmatigAangemaakt": True,
    })


def data_toewijzen_dienst(ctx, task):
    return nest({
        "rapportageCategorieen.toegewezenDienst.dienst": ctx.choice("DIENSTEN", ctx.dienst, required=True),
        "rapportageCategorieen.toegewezenDienst.toelichtingVastleggenDienst": f"Klacht hoort bij {ctx.dienst}.",
    })


def data_eerste_beoordeling(ctx, task):
    role = {"GGD": "ROLE_KLACHTEN_KLACHTENCOORDINATOR_GGD", "VTH": "ROLE_KLACHTEN_KLACHTENCOORDINATOR_VTH"}.get(
        ctx.dienst, "ROLE_KLACHTEN_KLACHTENCOORDINATOR")
    return nest({
        "eersteBeoordeling.resultaat": "KLACHT_BETREFT_KLACHT_EN_VERDERE_VERKENNING_IS_BENODIGD",
        "eersteBeoordeling.toelichting": "Betreft een klacht, verdere verkenning nodig.",
        "klachtencoordinator": ctx.user_by_role(role, "fullName"),
    })


def data_verkenning(ctx, task):
    klachtenteam = task["prefill"].get("pv", {}).get("klachtenteam")
    datum = task["prefill"].get("klacht", {}).get("datumOntvangst") or now(-1)
    autorisatiegroep = None
    if klachtenteam:
        autorisatiegroep = ctx.choice(f"AUTORISATIEGROEPEN_{klachtenteam}", ctx.autorisatiegroep)
    if autorisatiegroep is None and ctx.autorisatiegroep:
        ctx.report.warn(f"sending synthetic autorisatieGroep {ctx.autorisatiegroep}")
        autorisatiegroep = {"name": ctx.autorisatiegroep, "value": ctx.autorisatiegroep}
    sector = ctx.choice(f"{klachtenteam}_SECTOR") if klachtenteam else None
    afdeling = ctx.choice(sector["name"]) if sector else None
    afhandeltermijn = (datetime.datetime.fromisoformat(datum.replace("Z", "+00:00")) + datetime.timedelta(weeks=6)).isoformat()
    return nest({
        "verkenning.resultaat": "KLACHT_BEHANDELEN",
        "verkenning.autorisatieGroep": autorisatiegroep,
        "verkenning.toelichting": "Klacht wordt in behandeling genomen.",
        "verkenning.telefonischContactGeweest": True,
        "verkenning.teVerwachteAfhandeltermijn": 6,
        "verkenning.formeelAfhandelenKlacht": False,
        "rapportageCategorieen.sector": sector,
        "rapportageCategorieen.afdeling": afdeling,
        "rapportageCategorieen.producten": ctx.choice("PRODUCTEN"),
        "rapportageCategorieen.themas": ctx.choice("THEMAS"),
        "pv.geenTerugkoppelingNaarDeMelder": not ctx.terugkoppeling,
        "pv.resultaatVerkenning": "KLACHT_BEHANDELEN",
        "pv.afhandeltermijnDatum": afhandeltermijn,
        "pv.formeelAfhandelenKlacht": False,
    })


def data_toewijzen_zaakbehandelaar(ctx, task):
    if ctx.zaakbehandelaar == "EEN_KLACHTENBEHANDELAAR_VAN_DE_DIENST":
        email = ctx.user_by_role(f"ROLE_KLACHTEN_KLACHTBEHANDELAAR_{ctx.klachtteam}", "email")
    elif ctx.zaakbehandelaar == "ANDERE_KLACHTENCOORDINATOR":
        role = {"GGD": "ROLE_KLACHTEN_KLACHTENCOORDINATOR_GGD", "VTH": "ROLE_KLACHTEN_KLACHTENCOORDINATOR_VTH"}.get(
            ctx.dienst, "ROLE_KLACHTEN_KLACHTENCOORDINATOR")
        email = ctx.user_by_role(role, "email")
    else:
        email = None  # MIJZELF: the form reads it from localStorage 'userIdentity', which the frontend never sets
    return nest({
        "pv.zaakbehandelaarKlacht": ctx.zaakbehandelaar,
        "pv.zaakbehandelaarEmail": email,
        "pv.klachtteam": ctx.klachtteam,
        "informeleAfhandeling.overdrachtPlaatsgevondenOp":
            now() if ctx.zaakbehandelaar == "EEN_KLACHTENBEHANDELAAR_VAN_DE_DIENST" else None,
    })


def data_coordinator_onderzoek(ctx, task):
    p = "informeleAfhandeling.afhandelingDoorKlachtcoordinator.onderzoek"
    akkoord = ctx.melder_akkoord
    return nest({
        **onderzoek(ctx, p),
        f"{p}.oplossing.voorstel": "Container wordt deze week geleegd en het ophaalschema is aangepast.",
        f"{p}.oplossing.datumBesprokenMetMelder": now(),
        f"{p}.oplossing.melderAkkoordMetVoorstel": akkoord,
        f"{p}.oplossing.melderAkkoordMetVoorstelToelichting": "Telefonisch besproken met de melder.",
        f"{p}.gemotiveerdOordeel.overnemenNaarFormeleAfhandeling": "NEE" if akkoord == "NEE" else None,
        "pv.zaakresultaat": "Afgehandeld" if akkoord == "JA" else None,
        "afhandeldatumIntern": now() if akkoord == "JA" else None,
        "pv.melderAkkoordMetOplossing": akkoord == "JA",
        "pv.oordeelOvernemen": False,
    })


def data_behandelaar_onderzoek(ctx, task):
    p = "informeleAfhandeling.afhandelingDoorKlachtbehandelaar.onderzoek"
    return nest({
        **onderzoek(ctx, p),
        f"{p}.oplossing.voorstel": "Container wordt deze week geleegd en het ophaalschema is aangepast.",
        f"{p}.oplossing.datumBesprokenMetMelder": now(),
        f"{p}.oplossing.melderAkkoordMetVoorstel": ctx.melder_akkoord,
        "pv.melderAkkoordMetOplossing": ctx.melder_akkoord == "JA",
    })


def data_controleren(ctx, task):
    p = "informeleAfhandeling.afhandelingDoorKlachtcoordinator.onderzoek"
    akkoord = ctx.melder_akkoord
    # pv.zaakresultaat is a hidden field on this form, so the browser never submits it.
    return nest({
        "informeleAfhandeling.afhandelingDoorKlachtbehandelaar.akkoordTerugkoppeling": True,
        **onderzoek(ctx, p),
        f"{p}.oplossing.melderAkkoordMetVoorstel": akkoord,
        f"{p}.oplossing.melderAkkoordMetVoorstelToelichting": "Behandelaar heeft dit met de melder besproken.",
        f"{p}.gemotiveerdOordeel.overnemenNaarFormeleAfhandeling": "NEE",
        "afhandeldatumIntern": now(),
        "pv.melderAkkoordMetOplossing": akkoord in ("JA", "ONBEKEND"),
        "pv.oordeelOvernemen": False,
    })


def data_eindbrief_informeel(ctx, task):
    return nest({
        "pv:deKlagerIsTelefonischAkkoordGegaanMetDeAfrondingVanDeKlacht": "ja",
        "informeleAfhandeling.eindbrief.document": ctx.upload("Eindbrief informeel", task["processInstanceId"]),
        "informeleAfhandeling.eindbrief.toelichting": "Eindbrief verstuurd per e-mail.",
    })


def data_hoor_wederhoor(ctx, task):
    p = "formeleAfhandeling.verslagHoorwederhoor"
    return nest({
        f"{p}.gespreksvorm": "INDIVIDUEEL",
        f"{p}.datumGesprek": now(),
        f"{p}.verslagDocument": ctx.upload("Verslag hoor en wederhoor", task["processInstanceId"]),
        f"{p}.toelichting": "Gesprek met melder en behandelaar gevoerd.",
    })


def data_formeel_onderzoek(ctx, task):
    p = "formeleAfhandeling.onderzoek"
    overnemen = (task["prefill"].get("informeleAfhandeling", {}).get("afhandelingDoorKlachtcoordinator", {})
                 .get("onderzoek", {}).get("gemotiveerdOordeel", {}).get("overnemenNaarFormeleAfhandeling"))
    return nest({
        f"{p}.onderzoekUitgevoerd": "JA",
        f"{p}.verslagDocument": ctx.upload("Onderzoeksverslag", task["processInstanceId"]),
        f"{p}.toelichting": "Onderzoek uitgevoerd door de klachtencoördinator.",
        **onderzoek(ctx, p),
        f"{p}.oplossing.datumBesprokenMetMelder": now(),
        "pv.zaakresultaat": "Afgehandeld",
        "afhandeldatumIntern": now(),
        "pv.oordeelOvernemen": overnemen == "JA",
    })


def data_eindbrief_formeel(ctx, task):
    return nest({
        "formeleAfhandeling.eindbrief.document": ctx.upload("Eindbrief formeel", task["processInstanceId"]),
        "formeleAfhandeling.aardigheidje.isVerstuurd": "NEE",
    })


def data_commissie_start(ctx):
    return nest({
        "behandelingDoorKlachtencommissie.overdracht.datum": now(),
        "behandelingDoorKlachtencommissie.overdracht.toelichting": "Melder wil een oordeel van de klachtencommissie.",
    })


def data_commissie_resultaat(ctx, task):
    p = "behandelingDoorKlachtencommissie.klachtencommissie"
    return nest({
        f"{p}.resultaat.datumOntvangst": now(),
        f"{p}.resultaat.toelichting": "Advies van de klachtencommissie ontvangen.",
        f"{p}.resultaat.versturenEindbriefNaarMelder": True,
        f"{p}.beoordeling.oordeel": ctx.choice("OORDEEL", "ONGEGROND", required=True),
        f"{p}.beoordeling.gemotiveerdOordeel.omschrijving": "De commissie acht de klacht ongegrond.",
        "behandelingDoorKlachtencommissie.afwijkendOordeel": False,
        "behandelingDoorKlachtencommissie.aardigheidje.isVerstuurd": "NEE",
        "pv.zaakresultaat": "Afgehandeld",
        "afhandeldatumIntern": now(),
    })


def data_eindbrief_commissie(ctx, task):
    return nest({
        "behandelingDoorKlachtencommissie.eindbrief.document": ctx.upload("Eindbrief klachtencommissie", task["processInstanceId"]),
    })


def data_prefill_only(ctx, task):
    return {}


# (process key, task key) → (builder, user resolver)
COORDINATOR = lambda ctx: ctx.coordinator
TASKS = {
    (MAIN_PROCESS, "ToewijzenKlachtAanKlachtenteamDienstTask"): (data_toewijzen_dienst, lambda ctx: "klachten-ibpost"),
    ("klachten-beoordelen-nieuwe-klacht", "VastleggenResultaatEersteBeoordelingTask"): (data_eerste_beoordeling, COORDINATOR),
    ("klachten-verkennen-klacht", "VastleggenResultaatVerkenningTask"): (data_verkenning, COORDINATOR),
    ("klachten-informeren-externe-betrokkenen", "AfdrukkenBriefTask"): (data_prefill_only, lambda ctx: "klachten-ibpost"),
    ("klachten-informeel-afhandelen-klacht", "ToewijzenZaakAanZaakbehandelaarTask"): (data_toewijzen_zaakbehandelaar, COORDINATOR),
    ("klachten-informeel-afhandelen-klacht", "VastleggenEindresultaatOnderzoekOplossingsmogelijkhedenTask"): (data_coordinator_onderzoek, COORDINATOR),
    ("klachten-informeel-afhandelen-klacht", "VastleggenEindresultaatOnderzoekOplossingsmogelijkhedenTask1"): (data_behandelaar_onderzoek, lambda ctx: ctx.behandelaar or ctx.coordinator),
    ("klachten-informeel-afhandelen-klacht", "ControlerenAfhandelingEnVastleggenEindresultaatTask"): (data_controleren, COORDINATOR),
    ("klachten-informeel-afhandelen-klacht", "VastleggenDefinitiefEindbriefTask"): (data_eindbrief_informeel, COORDINATOR),
    ("klachten-formeel-afhandelen-klacht", "VastleggenGespreksverslagHoorEnWederhoorTask"): (data_hoor_wederhoor, COORDINATOR),
    ("klachten-formeel-afhandelen-klacht", "VastleggenOnderzoeksverslagEnofGemotiveerdOordeelTask"): (data_formeel_onderzoek, COORDINATOR),
    ("klachten-formeel-afhandelen-klacht", "VastleggenDefinitiefEindbriefTask"): (data_eindbrief_formeel, COORDINATOR),
    ("klachten-verwerken-behandeling-door-klachtencommissie", "VastleggenResultaatKlachtencommissieTask"): (data_commissie_resultaat, COORDINATOR),
    ("klachten-verwerken-behandeling-door-klachtencommissie", "VastleggenDefinitiefEindbriefTask"): (data_eindbrief_commissie, COORDINATOR),
    ("klachten-verwerken-behandeling-door-klachtencommissie", "ControleFormulierAfsluitenZaak"): (data_prefill_only, COORDINATOR),
    (MAIN_PROCESS, "ControleFormulierAfsluitenZaak"): (data_prefill_only, COORDINATOR),
}


# ---- engine -------------------------------------------------------------------------------------

def start_link(user, process_key):
    links = api_ok("GET", f"/api/v1/case-definition/{CASE}/case-process-link", user)
    pd = next((l for l in links if l["processDefinitionKey"] == process_key), None)
    if not pd:
        raise StepError(f"{user} cannot see process {process_key} on case {CASE}")
    return pd["id"]["processDefinitionId"]


def submit_start_form(user, process_key, data, document_id=None):
    pd_id = start_link(user, process_key)
    query = f"documentId={document_id}" if document_id else f"documentDefinitionName={CASE}"
    form = api_ok("GET", f"/api/v1/process-definition/{pd_id}/start-form?{query}", user)
    body = api_ok("POST", f"/api/v1/process-link/{form['processLinkId']}/form/submission?{query}", user,
                  merge(prefilled_data(form["properties"]["prefilledForm"]), data))
    return body


def wait_for_change(ctx, previous_task_ids):
    deadline = time.time() + STEP_TIMEOUT
    while time.time() < deadline:
        if incidents(ctx.document_id):
            return
        tasks = open_tasks(ctx.document_id)
        if not running_processes(ctx.document_id):
            return
        # An empty task list while processes still run means async service tasks are still busy.
        if tasks and {t[0] for t in tasks} != previous_task_ids:
            return
        time.sleep(1)


def complete_task(ctx, task_id, process_key, task_key):
    entry = TASKS.get((process_key, task_key))
    if not entry:
        raise StepError(f"no form data defined for {process_key}/{task_key}")
    builder, user_of = entry
    user = user_of(ctx)
    api_ok("POST", f"/api/v1/task/{task_id}/assign", user, {"assignee": user_id(user)})
    link = api_ok("GET", f"/api/v2/process-link/task/{task_id}", user)
    form = (link.get("properties") or {}).get("prefilledForm") or {}
    process_instance_id = psql(f"select proc_inst_id_ from act_ru_task where id_ = '{task_id}'")[0][0]
    task = {"prefill": prefilled_data(form), "processInstanceId": process_instance_id}
    data = merge(task["prefill"], builder(ctx, task))
    ctx.report.debug(f"submit {short(data, 2000)}")
    api_ok("POST", f"/api/v1/process-link/{link['processLinkId']}/form/submission"
                   f"?documentId={ctx.document_id}&taskInstanceId={task_id}", user, data)
    return user


def run_route(args):
    report = Report(args.verbose)
    ctx = Context(args, report)
    since = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    label = f"{ctx.route} · dienst {ctx.dienst}" + (f" ({args.autorisatiegroep})" if ctx.autorisatiegroep else "") \
        + f" · terugkoppeling {args.terugkoppeling}" \
        + (f" · {ctx.zaakbehandelaar}" if ctx.route == "informeel-coordinator" else "")
    print(f"\n=== {label}")

    try:
        result = submit_start_form("klachten-ibpost", MAIN_PROCESS, data_start(ctx))
        ctx.document_id = result.get("documentId")
        report.ok(f"registered complaint as klachten-ibpost (document {ctx.document_id})")
    except StepError as e:
        report.fail(f"register complaint: {e}")
        return report

    previous = set()
    wait_for_change(ctx, previous)
    for _ in range(MAX_STEPS):
        found = incidents(ctx.document_id)
        if found:
            for activity, msg in found:
                report.fail(f"incident at {activity}: {short(msg, 300)}")
            break
        tasks = open_tasks(ctx.document_id)
        if ctx.route == "commissie" and not ctx.commissie_started and \
                any(t[2] == "ToewijzenZaakAanZaakbehandelaarTask" for t in tasks):
            try:
                submit_start_form(ctx.coordinator, "start-klachtencomissie", data_commissie_start(ctx), ctx.document_id)
                report.ok(f"started user action 'Start klachtencomissie' as {ctx.coordinator}")
            except StepError as e:
                report.fail(f"start klachtencommissie: {e}")
                break
            ctx.commissie_started = True
            wait_for_change(ctx, {t[0] for t in tasks})
            continue
        if not tasks:
            if running_processes(ctx.document_id):
                report.fail(f"process stuck without user task in {running_processes(ctx.document_id)}")
            break
        task_id, process_key, task_key = tasks[0]
        try:
            user = complete_task(ctx, task_id, process_key, task_key)
            report.ok(f"{process_key} / {task_key} as {user}")
        except StepError as e:
            report.fail(f"{process_key} / {task_key}: {e}")
            break
        previous = {t[0] for t in tasks}
        wait_for_change(ctx, previous)
    else:
        report.fail(f"no end after {MAX_STEPS} steps")

    check_end_state(ctx, report, since)
    return report


def check_end_state(ctx, report, since):
    if not ctx.document_id:
        return
    status, document = api("GET", f"/api/v1/document/{ctx.document_id}", ctx.coordinator)
    internal = (document or {}).get("internalStatus") if isinstance(document, dict) else None
    try:
        zaak = zaak_state(ctx.document_id)
    except StepError as e:
        zaak = None
        report.fail(f"read zaak: {e}")
    print("  --- end state")
    checks = [
        ("process ended", not running_processes(ctx.document_id), running_processes(ctx.document_id)),
        ("internal status 'afgehandeld'", internal == "afgehandeld", internal),
        ("zaak status 'Afgehandeld'", bool(zaak) and zaak["status"] == "Afgehandeld", zaak and zaak["status"]),
        ("zaak resultaat set", bool(zaak) and bool(zaak["resultaat"]), zaak and zaak["resultaat"]),
        ("no incidents", not incidents(ctx.document_id), len(incidents(ctx.document_id))),
    ]
    errors = []
    for error in backend_errors(since):
        noise = next((why for key, why in KNOWN_BACKEND_NOISE.items() if key in error), None)
        if noise:
            report.warn(f"known Valtimo log noise: {noise}")
        else:
            errors.append(error)
    checks.append(("no ERROR lines in backend log", not errors, len(errors)))
    for name, passed, actual in checks:
        (report.ok if passed else report.fail)(f"{name}" + ("" if passed else f" (got: {actual})"))
    for line in errors[:5]:
        print(f"     {short(line.splitlines()[0], 300)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--route", choices=ROUTES + ["all"], default="all")
    parser.add_argument("--dienst", choices=DIENSTEN, default="SZW")
    parser.add_argument("--autorisatiegroep", choices=list(AUTORISATIEGROEPEN_OCW), help="only for --dienst OCW")
    parser.add_argument("--zaakbehandelaar", choices=["MIJZELF", "ANDERE_KLACHTENCOORDINATOR"],
                        default="ANDERE_KLACHTENCOORDINATOR", help="for the informeel-coordinator route")
    parser.add_argument("--terugkoppeling", choices=["on", "off"], default="off")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    routes = ROUTES if args.route == "all" else [args.route]
    results = []
    for route in routes:
        args.route = route
        results.append((route, run_route(args)))

    print("\n=== summary")
    for route, report in results:
        state = "✅ passed" if not report.failures else f"❌ {len(report.failures)} failure(s)"
        print(f"  {route:24} {state}" + (f", {len(report.warnings)} warning(s)" if report.warnings else ""))
    sys.exit(1 if any(r.failures for _, r in results) else 0)


if __name__ == "__main__":
    main()
