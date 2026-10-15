#!/usr/bin/env python3
"""
Checks, per demo user, which klachten each user can list, open and handle, against the expected
role × dienst matrix (the F3 target). Everything goes through the GZAC REST API, so every answer
comes from the OpenFTV policies via AuthZEN.

Usage:
  scripts/klachten-authz-check.py [--user klachten-behandelaar-szw ...] [--check open ...] [--verbose]

Every run seeds fresh complaints, one per scope (unassigned, OCW before verkenning, each dienst and OCW
group, and an OCW-JGZ complaint moved to SZW), each stopped at an open task and with one note. Only these
seeds are judged.

Checks:
  list         complaint is in the case list (case search)
  open         GET the complaint by id (direct URL)
  notes        all notes of the complaint are visible
  files        all zaak documents of the complaint are visible
  zaak         GET the zaak of the complaint
  task-list    the open task of the complaint is in the task list
  task-open    GET the open task and its form by id
  action       open the start form of user action 'Wijzigen informatie melder' (OperatonExecution:create)
  claim        claim the open task (undone right after)
  note-create  add a note to the complaint

Needs: python3, docker (the demo stack running via ./run.sh). Only the standard library is used.
"""

import argparse
import base64
import json
import sys
import time
import urllib.parse

from klachten_api import (
    CASE, OPEN_ZAAK, StepError, api, api_ok, open_tasks, open_zaak_get, psql, route_args, run_route, short, token,
    user_id,
)

BEHANDELAAR_TASK = "VastleggenEindresultaatOnderzoekOplossingsmogelijkhedenTask1"
USER_ACTION = "klachten-wijzigen-algemene-informatie"

# scope → (walkthrough args, task the seed stops at)
SEEDS = {
    "UNASSIGNED": (dict(route="informeel-behandelaar"), "ToewijzenKlachtAanKlachtenteamDienstTask"),
    "OCW_PRE": (dict(route="informeel-behandelaar", dienst="OCW"), "VastleggenResultaatEersteBeoordelingTask"),
    **{d: (dict(route="informeel-behandelaar", dienst=d, terugkoppeling="on"), BEHANDELAAR_TASK)
       for d in ["SZW", "DBV", "DPZ", "DSB", "DSO", "BSD", "GGD", "VTH"]},
    **{f"OCW_{g}": (dict(route="informeel-behandelaar", dienst="OCW", autorisatiegroep=g, terugkoppeling="on"),
                    BEHANDELAAR_TASK) for g in ["ALG", "JGZ", "JH"]},
    "OCW_JGZ_MOVED": (dict(route="informeel-behandelaar", dienst="OCW", autorisatiegroep="JGZ", terugkoppeling="on"),
                      BEHANDELAAR_TASK),
}
# Seeds moved to another dienst after the verkenning, keeping their autorisatiegroep (like herbeoordelen does).
MOVED = {"OCW_JGZ_MOVED": "SZW"}
ALL = set(SEEDS)

# user → (list scope, read scope, write scope). Read: open, notes, files, zaak.
# Write: task-list, task-open, claim, action, note-create.
EXPECTED = {
    "admin": (ALL, ALL, ALL),
    "klachten-kcc": (ALL, ALL, set()),
    "klachten-ibpost": ({"UNASSIGNED"}, ALL, {"UNASSIGNED"}),
    "klachten-coordinator": (ALL - {"GGD", "VTH"},) * 3,
    "klachten-coordinator-ggd": ({"GGD", "UNASSIGNED"},) * 3,
    "klachten-coordinator-vth": ({"VTH", "UNASSIGNED"},) * 3,
    **{f"klachten-behandelaar-{d.lower()}": ({d},) * 3 for d in ["DBV", "DPZ", "DSB", "DSO", "BSD"]},
    "klachten-behandelaar-szw": ({"SZW", "OCW_JGZ_MOVED"},) * 3,
    "klachten-behandelaar-ocw": ({"OCW_ALG", "OCW_PRE"},) * 3,
    "klachten-behandelaar-ocw-jgz": ({"OCW_JGZ"},) * 3,
    "klachten-behandelaar-ocw-jh": ({"OCW_JH"},) * 3,
}
# These see tasks through the case document, not through the task's candidate groups.
TASK_BY_DOCUMENT = {"admin", "klachten-coordinator"}

READ_CHECKS = ["list", "open", "notes", "files", "zaak"]
TASK_CHECKS = ["task-list", "task-open", "claim"]
WRITE_CHECKS = TASK_CHECKS + ["action", "note-create"]
CHECKS = READ_CHECKS + ["task-list", "task-open", "action", "claim", "note-create"]

ALLOWED, DENIED = "allowed", "denied"


# ---- seeding and ground truth -------------------------------------------------------------------

class Seed:
    def __init__(self, scope, document_id, task_id, candidate_groups):
        self.scope = scope
        self.document_id = document_id
        self.task_id = task_id
        self.candidate_groups = candidate_groups
        self.notes = 0
        self.files = 0


def seed_all():
    seeds = {}
    for scope, (overrides, stop_at) in SEEDS.items():
        report = run_route(route_args(**overrides), stop_at=stop_at, melder=f"Authz-check {scope}")
        if report.failures or not report.document_id:
            raise StepError(f"seeding {scope} failed: {report.failures}")
        task_id = next(t[0] for t in open_tasks(report.document_id) if t[2] == stop_at)
        groups = {r[0] for r in psql(f"select group_id_ from act_ru_identitylink "
                                     f"where task_id_ = '{task_id}' and type_ = 'candidate'")}
        seed = Seed(scope, report.document_id, task_id, groups)
        if scope in MOVED:
            psql(f"update json_schema_document set json_document_content = jsonb_set(json_document_content, "
                 f"'{{rapportageCategorieen,toegewezenDienst,dienst,name}}', '\"{MOVED[scope]}\"') "
                 f"where json_schema_document_id = '{seed.document_id}'")
        psql(f"insert into note (id, created_by_user_id, created_by_user_full_name, created_date, content, document_id) "
             f"values (gen_random_uuid(), 'authz-check', 'Authz check', now(), 'Notitie {scope}', '{seed.document_id}')")
        seed.notes = int(psql(f"select count(*) from note where document_id = '{seed.document_id}'")[0][0])
        seed.files = file_count(seed.document_id)
        seeds[scope] = seed
    return seeds


def file_count(document_id):
    rows = psql(f"select zaak_instance_url from zaak_instance_link where document_id = '{document_id}'")
    if not rows:
        return 0
    query = urllib.parse.urlencode({"zaak": rows[0][0].replace("host.docker.internal", "localhost")})
    return len(open_zaak_get(f"{OPEN_ZAAK}/zaken/api/v1/zaakinformatieobjecten?{query}"))


def roles(user):
    payload = token(user).split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    return set(claims.get("realm_access", {}).get("roles", []))


# ---- checks -------------------------------------------------------------------------------------

def expected(user, check, seed):
    list_scope, read_scope, write_scope = EXPECTED[user]
    if check == "list":
        allowed = seed.scope in list_scope
    elif check in READ_CHECKS:
        allowed = seed.scope in read_scope
    else:
        allowed = seed.scope in write_scope
    if allowed and check in TASK_CHECKS and user not in TASK_BY_DOCUMENT:
        allowed = bool(roles(user) & seed.candidate_groups)
    return ALLOWED if allowed else DENIED


def outcome(status, ok=(200,), denied=(403, 404)):
    """HTTP status → (allowed|denied|error, detail)."""
    if status in ok:
        return ALLOWED, ""
    if status in denied:
        return DENIED, ""
    return "error", f"HTTP {status}"


def paged_ids(method, path, user, body=None):
    ids, page = set(), 0
    while True:
        sep = "&" if "?" in path else "?"
        resp = api_ok(method, f"{path}{sep}page={page}&size=200", user, body)
        ids |= {row["id"] for row in resp["content"]}
        if resp.get("last", True):
            return ids
        page += 1


def counted(status, body, truth):
    """Filtered list: allowed only when every item the complaint has is visible."""
    if truth == 0:
        return None, "nothing to see"
    if status in (403, 404):
        return DENIED, ""
    if status != 200:
        return "error", f"HTTP {status}"
    seen = body.get("totalElements", len(body.get("content", []))) if isinstance(body, dict) else len(body or [])
    return (ALLOWED, "") if seen >= truth else (DENIED, f"{seen}/{truth}")


class Checker:
    def __init__(self, seeds, users, checks):
        self.seeds = seeds
        self.users = users
        self.checks = checks
        self.results = {}  # (user, check, scope) → (actual, detail)
        links = api_ok("GET", f"/api/v1/case-definition/{CASE}/case-process-link", "admin")
        self.action_pd = next(l["id"]["processDefinitionId"] for l in links if l["processDefinitionKey"] == USER_ACTION)

    def record(self, user, check, seed, result):
        self.results[(user, check, seed.scope)] = result

    def run(self):
        for user in self.users:
            listed = paged_ids("POST", f"/api/v1/case/{CASE}/search", user, {"assigneeFilter": "ALL", "otherFilters": []}) \
                if "list" in self.checks else set()
            tasks = paged_ids("POST", "/api/v3/task?filter=ALL", user, {}) if "task-list" in self.checks else set()
            for seed in self.seeds.values():
                self.read_checks(user, seed, listed, tasks)
        # Checks that change state run after all read checks, so the counts above stay valid.
        for user in self.users:
            for seed in self.seeds.values():
                self.write_checks(user, seed)

    def read_checks(self, user, seed, listed, tasks):
        d = seed.document_id
        for check in self.checks:
            if check == "list":
                result = (ALLOWED if d in listed else DENIED, "")
            elif check == "open":
                result = outcome(api("GET", f"/api/v1/document/{d}", user)[0])
            elif check == "notes":
                result = counted(*api("GET", f"/api/v1/document/{d}/note?page=0&size=100", user), seed.notes)
            elif check == "files":
                result = counted(*api("GET", f"/api/v2/zaken-api/document/{d}/files?page=0&size=100", user), seed.files)
            elif check == "zaak":
                result = outcome(api("GET", f"/api/v1/zaken-api/document/{d}/zaak", user)[0])
            elif check == "task-list":
                result = (ALLOWED if seed.task_id in tasks else DENIED, "")
            elif check == "task-open":
                task = outcome(api("GET", f"/api/v1/task/{seed.task_id}", user)[0])
                form = outcome(api("GET", f"/api/v2/process-link/task/{seed.task_id}", user)[0])
                result = task if task[0] == form[0] else (ALLOWED, f"task {task[0]}, form {form[0]}")
            elif check == "action":
                result = outcome(api("GET", f"/api/v1/process-definition/{self.action_pd}/start-form?documentId={d}", user)[0])
            else:
                continue
            self.record(user, check, seed, result)

    def write_checks(self, user, seed):
        if "claim" in self.checks:
            status, _ = api("POST", f"/api/v1/task/{seed.task_id}/assign", user, {"assignee": user_id(user)})
            result = outcome(status, ok=(200, 204))
            if result[0] == ALLOWED:
                api("POST", f"/api/v1/task/{seed.task_id}/unassign", "admin")
            self.record(user, "claim", seed, result)
        if "note-create" in self.checks:
            status, _ = api("POST", f"/api/v1/document/{seed.document_id}/note", user,
                            {"content": f"Authz check: notitie van {user}"})
            self.record(user, "note-create", seed, outcome(status, ok=(200, 201)))


# ---- report -------------------------------------------------------------------------------------

def report(checker, verbose):
    differences = []
    width = max(len(u) for u in checker.users)
    print("\n=== matrix (✅ all seeds as expected, ❌n = n seeds differ, · = nothing to check)\n")
    print(f"  {'user':{width}}  " + "  ".join(f"{c:>11}" for c in checker.checks))
    for user in checker.users:
        cells = []
        for check in checker.checks:
            wrong = 0
            judged = 0
            for seed in checker.seeds.values():
                actual, detail = checker.results[(user, check, seed.scope)]
                if actual is None:
                    continue
                judged += 1
                want = expected(user, check, seed)
                if actual != want:
                    wrong += 1
                    differences.append((user, check, seed.scope, want, actual, detail))
                elif verbose:
                    print(f"     {user} {check} {seed.scope}: {actual}")
            cells.append("·" if not judged else ("✅" if not wrong else f"❌{wrong}"))
        print(f"  {user:{width}}  " + "  ".join(f"{c:>11}" for c in cells))

    print(f"\n=== {len(differences)} difference(s)")
    for user, check, scope, want, actual, detail in differences:
        print(f"  {user:{width}}  {check:11}  {scope:10}  expected {want}, got {actual}" + (f" ({detail})" if detail else ""))
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--user", action="append", choices=list(EXPECTED), help="only these users (repeatable)")
    parser.add_argument("--check", action="append", choices=CHECKS, help="only these checks (repeatable)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    users = args.user or list(EXPECTED)
    checks = [c for c in CHECKS if not args.check or c in args.check]

    started = time.time()
    try:
        print("=== seeding one complaint per scope")
        seeds = seed_all()
        print("\n=== seeds")
        for seed in seeds.values():
            print(f"  {seed.scope:10}  document {seed.document_id}  notes {seed.notes}  files {seed.files}")
        checker = Checker(seeds, users, checks)
        checker.run()
    except StepError as e:
        print(f"\n❌ {short(str(e), 600)}")
        sys.exit(2)
    differences = report(checker, args.verbose)
    print(f"\n  done in {time.time() - started:.0f}s")
    sys.exit(1 if differences else 0)


if __name__ == "__main__":
    main()
