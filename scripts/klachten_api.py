"""
Shared code for the klachten scripts: GZAC/Keycloak/Open Zaak access, the form data per task and the
engine that walks a complaint through the process as the demo user of each task.

Used by klachten-walkthrough.py and klachten-authz-check.py. The GZAC, Open Zaak and start-form helpers
are also used by the bezwaar scripts. Only the standard library is used.
"""

import argparse
import base64
import datetime
import hashlib
import hmac
import json
import subprocess
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
    "ALG": "AUTORISATIEGROEPEN_OCW_ALGEMEEN",
    "JGZ": "AUTORISATIEGROEPEN_OCW_JGZ_JEUGDGEZONDHEIDSZORG",
    "JH": "AUTORISATIEGROEPEN_OCW_JEUGDHULP",
}
# Same mapping as the calculated field pv.klachtteam in the toewijzen-zaak-aan-zaakbehandelaar form.
# GGD/VTH have no behandelaar role: their coordinator handles the complaint.
KLACHTTEAM = {
    "BSD": "KLACHTBEHANDELAAR_BSD_BESTUURSDIENST", "DBV": "KLACHTBEHANDELAAR_DBV", "DPZ": "KLACHTBEHANDELAAR_DPZ",
    "DSB": "KLACHTBEHANDELAAR_DSB_DIENST_STADSBEHEER", "DSO": "KLACHTBEHANDELAAR_DSO", "SZW": "KLACHTBEHANDELAAR_SZW",
    "GGD": "KLACHTENCOORDINATOR_GGD", "VTH": "KLACHTENCOORDINATOR_VTH",
}
BEHANDELAAR_USER = {
    "KLACHTBEHANDELAAR_BSD_BESTUURSDIENST": "klachten-behandelaar-bsd", "KLACHTBEHANDELAAR_DBV": "klachten-behandelaar-dbv",
    "KLACHTBEHANDELAAR_DPZ": "klachten-behandelaar-dpz", "KLACHTBEHANDELAAR_DSB_DIENST_STADSBEHEER": "klachten-behandelaar-dsb",
    "KLACHTBEHANDELAAR_DSO": "klachten-behandelaar-dso", "KLACHTBEHANDELAAR_SZW": "klachten-behandelaar-szw",
    "KLACHTBEHANDELAAR_OCW_ALGEMEEN": "klachten-behandelaar-ocw", "KLACHTBEHANDELAAR_OCW_JGZ": "klachten-behandelaar-ocw-jgz",
    "KLACHTBEHANDELAAR_OCW_JH": "klachten-behandelaar-ocw-jh",
    "KLACHTENCOORDINATOR_GGD": "klachten-coordinator-ggd", "KLACHTENCOORDINATOR_VTH": "klachten-coordinator-vth",
}
STEP_TIMEOUT = 45
# Backend ERROR lines that come from Valtimo itself, not from the klachten configuration.
KNOWN_BACKEND_NOISE = {
    "TaskUpdateListener": "Valtimo SSE TaskUpdateListener looks up a process instance that has just ended",
    "AsyncRequestNotUsableException": "a browser dropped an async/SSE request (an open GZAC tab, not this script)",
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


def zaak_document_types(zaak_url):
    """Informatieobjecttype omschrijving of every document linked to the zaak."""
    query = urllib.parse.urlencode({"zaak": zaak_url.replace("host.docker.internal", "localhost")})
    links = open_zaak_get(f"{OPEN_ZAAK}/zaken/api/v1/zaakinformatieobjecten?{query}")
    return [open_zaak_get(open_zaak_get(link["informatieobject"])["informatieobjecttype"])["omschrijving"]
            for link in links]


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
        self.post = args.post
        self.document_id = None
        self.choice_cache = {}
        self.coordinator = {"GGD": "klachten-coordinator-ggd", "VTH": "klachten-coordinator-vth"}.get(
            self.dienst, "klachten-coordinator")
        self.autorisatiegroep = AUTORISATIEGROEPEN_OCW.get(args.autorisatiegroep) if self.dienst == "OCW" else None
        if self.dienst == "OCW":
            self.klachtteam = {"JGZ": "KLACHTBEHANDELAAR_OCW_JGZ", "JH": "KLACHTBEHANDELAAR_OCW_JH"}.get(
                args.autorisatiegroep, "KLACHTBEHANDELAAR_OCW_ALGEMEEN")
        else:
            self.klachtteam = KLACHTTEAM.get(self.dienst)
        self.behandelaar = BEHANDELAAR_USER.get(self.klachtteam)
        self.zaakbehandelaar = "EEN_KLACHTENBEHANDELAAR_VAN_DE_DIENST" if self.route == "informeel-behandelaar" \
            else args.zaakbehandelaar
        self.melder_akkoord = "NEE" if self.route == "formeel" else (args.melder_akkoord or "JA")
        self.afkeuren = args.terugkoppeling_afkeuren  # reject the behandelaar's terugkoppeling once
        self.oordeel = args.oordeel
        self.oordeel_overnemen = args.oordeel_overnemen
        self.commissie_started = False
        self.commissie_stoppen = args.commissie_stoppen

    # Choice fields (dataSrc url, no valueProperty) store the whole choice-field value object.
    def choice(self, key, preferred=None, required=False):
        if key not in self.choice_cache:
            status, body = api("GET", f"/api/v1/choice-fields/name/{urllib.parse.quote(key)}", self.coordinator)
            self.choice_cache[key] = body.get("choiceFieldValues", []) if status == 200 and isinstance(body, dict) else None
            if self.choice_cache[key] is None:
                self.report.warn(f"choice field {key} not found (HTTP {status})")
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

# Principes picked for a (deels) gegrond oordeel; each cascades into its own list of geschonden vereisten.
PRINCIPES = ["KERNWAARDE_GOED_CONTACT", "KERNWAARDE_VOOR_ALLE_BURGERS", "KERNWAARDE_EERLIJK"]


def onderzoek(ctx, prefix):
    data = {
        f"{prefix}.oordeel": ctx.choice("OORDEEL", ctx.oordeel, required=True),
        f"{prefix}.gemotiveerdOordeel.omschrijving": "De gemeente heeft de afspraak niet nagekomen. Excuses aangeboden.",
    }
    return {**data, **principes(ctx, prefix)}


def principes(ctx, prefix, key="dienstverleningsprincipe"):
    """For a (deels) gegrond oordeel: 3 principes, each with the first geschonden vereiste of its cascaded list."""
    if ctx.oordeel not in ("GEGROND", "DEELS_GEGROND"):
        return {}
    data = {}
    for i, name in enumerate(PRINCIPES):
        suffix = "" if i == 0 else str(i + 1)
        principe = ctx.choice("DIENSTVERLENINGSPRINCIPES", name, required=True)
        data[f"{prefix}.{key}{suffix}"] = principe
        data[f"{prefix}.geschondenDienstverleningsprincipes{suffix}"] = [ctx.choice(principe["name"], required=True)]
    data[f"{prefix}.nogEenDienstverleningsprincipeBehoorlijkheidsnormToevoegen"] = "JA"
    data[f"{prefix}.nogEenDienstverleningsprincipeBehoorlijkheidsnormToevoegen2"] = "JA"
    return data


def data_start(ctx):
    return nest({
        "klacht.datumOntvangst": now(-1),
        "klacht.korteOmschrijvingMelding": "Afvalcontainer al drie weken niet geleegd",
        "klacht.toelichtingMelding": "Ondanks twee meldingen is de ondergrondse container in de Spuistraat niet geleegd.",
        "melder.soortMelder": "INWONER",
        "melder.personalia.voornaam": "Jan",
        "melder.personalia.achternaam": "Jansen",
        "melder.contactgegevens.communicatieViaPost": ctx.post,
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
    autorisatiegroep = ctx.choice(f"AUTORISATIEGROEPEN_{klachtenteam}", ctx.autorisatiegroep, required=True) if klachtenteam else None
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
        email = ctx.user_by_role(f"ROLE_KLACHTEN_{ctx.klachtteam}", "email")
    elif ctx.zaakbehandelaar == "ANDERE_KLACHTENCOORDINATOR":
        role = {"GGD": "ROLE_KLACHTEN_KLACHTENCOORDINATOR_GGD", "VTH": "ROLE_KLACHTEN_KLACHTENCOORDINATOR_VTH"}.get(
            ctx.dienst, "ROLE_KLACHTEN_KLACHTENCOORDINATOR")
        email = ctx.user_by_role(role, "email")
    else:
        email = None  # MIJZELF: the form's defaultValue (prefilled) is used
    data = {
        "pv.zaakbehandelaarKlacht": ctx.zaakbehandelaar,
        "pv.klachtteam": ctx.klachtteam,
        "informeleAfhandeling.overdrachtPlaatsgevondenOp":
            now() if ctx.zaakbehandelaar == "EEN_KLACHTENBEHANDELAAR_VAN_DE_DIENST" else None,
    }
    if email:
        data["pv.zaakbehandelaarEmail"] = email
    return nest(data)


def data_coordinator_onderzoek(ctx, task):
    p = "informeleAfhandeling.afhandelingDoorKlachtcoordinator.onderzoek"
    akkoord = ctx.melder_akkoord
    # ONBEKEND counts as akkoord, like the form's calculated pv.melderAkkoordMetOplossing.
    afgehandeld = akkoord in ("JA", "ONBEKEND")
    overnemen = "JA" if ctx.oordeel_overnemen else "NEE"
    return nest({
        **onderzoek(ctx, p),
        f"{p}.oplossing.voorstel": "Container wordt deze week geleegd en het ophaalschema is aangepast.",
        f"{p}.oplossing.datumBesprokenMetMelder": now(),
        f"{p}.oplossing.melderAkkoordMetVoorstel": akkoord,
        f"{p}.oplossing.melderAkkoordMetVoorstelToelichting": "Telefonisch besproken met de melder.",
        f"{p}.gemotiveerdOordeel.overnemenNaarFormeleAfhandeling": overnemen if akkoord == "NEE" else None,
        "pv.zaakresultaat": "Afgehandeld" if afgehandeld else None,
        "afhandeldatumIntern": now() if afgehandeld else None,
        "pv.melderAkkoordMetOplossing": afgehandeld,
        "pv.oordeelOvernemen": akkoord == "NEE" and ctx.oordeel_overnemen,
    })


def data_behandelaar_onderzoek(ctx, task):
    p = "informeleAfhandeling.afhandelingDoorKlachtbehandelaar.onderzoek"
    return nest({
        **onderzoek(ctx, p),
        f"{p}.oplossing.voorstel": "Container wordt deze week geleegd en het ophaalschema is aangepast.",
        f"{p}.oplossing.datumBesprokenMetMelder": now(),
        # This form only offers JA/NEE; the coordinator records ONBEKEND when checking it.
        f"{p}.oplossing.melderAkkoordMetVoorstel": "NEE" if ctx.melder_akkoord == "NEE" else "JA",
        "pv.melderAkkoordMetOplossing": ctx.melder_akkoord != "NEE",
    })


def data_controleren(ctx, task):
    p = "informeleAfhandeling.afhandelingDoorKlachtcoordinator.onderzoek"
    if ctx.afkeuren:
        ctx.afkeuren = False
        return nest({
            "informeleAfhandeling.afhandelingDoorKlachtbehandelaar.akkoordTerugkoppeling": False,
            "informeleAfhandeling.afhandelingDoorKlachtbehandelaar.toelichting": "Graag het oordeel beter motiveren.",
        })
    akkoord = ctx.melder_akkoord
    afgehandeld = akkoord in ("JA", "ONBEKEND")
    return nest({
        "informeleAfhandeling.afhandelingDoorKlachtbehandelaar.akkoordTerugkoppeling": True,
        **onderzoek(ctx, p),
        f"{p}.oplossing.melderAkkoordMetVoorstel": akkoord,
        f"{p}.oplossing.melderAkkoordMetVoorstelToelichting": "Behandelaar heeft dit met de melder besproken.",
        f"{p}.gemotiveerdOordeel.overnemenNaarFormeleAfhandeling": "JA" if ctx.oordeel_overnemen else "NEE",
        "afhandeldatumIntern": now(),
        "pv.zaakresultaat": "Afgehandeld" if afgehandeld else None,
        "pv.melderAkkoordMetOplossing": afgehandeld,
        "pv.oordeelOvernemen": ctx.oordeel_overnemen,
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
        f"{p}.beoordeling.oordeel": ctx.choice("OORDEEL", ctx.oordeel, required=True),
        f"{p}.beoordeling.gemotiveerdOordeel.omschrijving": "Advies van de commissie overgenomen.",
        # The commissie fields use a capital D, as in the schema.
        **principes(ctx, f"{p}.beoordeling", "Dienstverleningsprincipe"),
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

def start_link(user, process_key, document_id=None, case=CASE):
    """The process definition id of a process the user may start: a user action on a case (the case's
    startable items, checked against that case, as the frontend does), or a new case."""
    if document_id:
        items = api_ok("GET", f"/api/v1/case/startable-item?caseDocumentId={document_id}", user)
        pd_id = next((i["processDefinitionId"] for i in items if i["key"] == process_key), None)
    else:
        links = api_ok("GET", f"/api/v1/case-definition/{case}/case-process-link", user)
        pd_id = next((l["id"]["processDefinitionId"] for l in links if l["processDefinitionKey"] == process_key), None)
    if not pd_id:
        raise StepError(f"{user} cannot see process {process_key} on " + (f"case {document_id}" if document_id else case))
    return pd_id


def submit_start_form(user, process_key, data, document_id=None, case=CASE):
    pd_id = start_link(user, process_key, document_id, case)
    query = f"documentId={document_id}" if document_id else f"documentDefinitionName={case}"
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


def route_args(**overrides):
    """The walkthrough CLI defaults as an argparse-like namespace, for scripts that drive a route themselves."""
    defaults = dict(route="informeel-coordinator", dienst="SZW", autorisatiegroep=None,
                    zaakbehandelaar="ANDERE_KLACHTENCOORDINATOR", terugkoppeling="off", post=False,
                    melder_akkoord=None, oordeel="ONGEGROND", oordeel_overnemen=False, commissie_stoppen=False,
                    terugkoppeling_afkeuren=False, verbose=False)
    return argparse.Namespace(**{**defaults, **overrides})


def run_route(args, stop_at=None, melder=None):
    """Walks one route. With stop_at (a task key), returns as soon as that task is open, without completing it."""
    report = Report(args.verbose)
    report.document_id = None
    ctx = Context(args, report)
    since = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    label = f"{ctx.route} · dienst {ctx.dienst}" + (f" ({args.autorisatiegroep})" if ctx.autorisatiegroep else "") \
        + f" · terugkoppeling {args.terugkoppeling}" + (" · via post" if ctx.post else "") \
        + (f" · {ctx.zaakbehandelaar}" if ctx.route == "informeel-coordinator" else "")
    print(f"\n=== {label}")

    try:
        data = data_start(ctx)
        if melder:
            data["melder"]["personalia"]["achternaam"] = melder
        result = submit_start_form("klachten-ibpost", MAIN_PROCESS, data)
        ctx.document_id = report.document_id = result.get("documentId")
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
        if stop_at and any(t[2] == stop_at for t in tasks):
            report.ok(f"stopped at open task {stop_at}")
            return report
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
            zaak = zaak_state(ctx.document_id)
            (report.ok if zaak and zaak["status"] == "Overgedragen naar klachtencommissie" else report.fail)(
                f"zaak status after start: {zaak and zaak['status']}")
            continue
        if ctx.commissie_stoppen and any(t[2] == "VastleggenResultaatKlachtencommissieTask" for t in tasks):
            try:
                submit_start_form(ctx.coordinator, "klachten-terug-naar-hoofd-proces", nest({
                    "behandelingDoorKlachtencommissie.redenTeruggaanNaarHoofdproces": "Melder trekt het verzoek in."
                }), ctx.document_id)
                report.ok(f"started user action 'Terug naar hoofdproces' as {ctx.coordinator}")
            except StepError as e:
                report.fail(f"stop klachtencommissie: {e}")
                break
            ctx.commissie_stoppen = False
            wait_for_change(ctx, {t[0] for t in tasks})
            zaak = zaak_state(ctx.document_id)
            (report.ok if zaak and zaak["status"] == "In behandeling" else report.fail)(
                f"zaak status after stop: {zaak and zaak['status']}")
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
    if ctx.terugkoppeling:
        types = zaak_document_types(zaak["url"]) if zaak else []
        checks.append(("terugkoppeling document 'Bericht' linked to zaak", "Bericht" in types, types))
    errors = unexpected_backend_errors(report, since)
    checks.append(("no ERROR lines in backend log", not errors, len(errors)))
    for name, passed, actual in checks:
        (report.ok if passed else report.fail)(f"{name}" + ("" if passed else f" (got: {actual})"))
    for line in errors[:5]:
        print(f"     {short(line.splitlines()[0], 300)}")


def unexpected_backend_errors(report, since):
    """Backend ERROR entries since the given time, without the known Valtimo noise (reported as warnings)."""
    errors = []
    for error in backend_errors(since):
        noise = next((why for key, why in KNOWN_BACKEND_NOISE.items() if key in error), None)
        if noise:
            report.warn(f"known Valtimo log noise: {noise}")
        else:
            errors.append(error)
    return errors
