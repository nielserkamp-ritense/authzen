#!/usr/bin/env python3
"""
Checks, per demo user, what each user can see and do on a bezwaar, against the expected role matrix
(EXPECTED below). Everything goes through the GZAC REST API, so every answer comes from the OpenFTV
policies via AuthZEN.

Usage:
  scripts/bezwaar-authz-check.py [--user bezwaar-adviseur ...] [--check actions ...] [--verbose]
                                 [--grant USER=CHECK[,CHECK] ...]

--grant changes the expected matrix on the open bezwaar, to prove a live policy change: e.g. after adding
"afsluiten-bezwaar" to the acties of the adviseur, run with --grant bezwaar-adviseur=actions,afsluiten.

Every run seeds two fresh bezwaren, each with one note and one zaak document:
  open      stopped at the open task 'Valideer gegevens aanvrager'
  afgerond  closed with 'Afsluiten bezwaar' straight away, so its first task is still open

Checks:
  list         bezwaar is in the case list (case search)
  open         GET the bezwaar by id (direct URL)
  notes        all notes of the bezwaar are visible
  files        all zaak documents of the bezwaar are visible
  widgets      data of the first widget on the widgets tab
  task-list    the open task of the bezwaar is in the task list
  task-open    GET the open task and its form by id
  claim        claim the open task (undone right after)
  actions      the bezwaar has user actions to start (startable items)
  afsluiten    open the start form of 'Afsluiten bezwaar' (OperatonExecution:create)
  note-create  add a note to the bezwaar
  file-upload  upload a zaak document from the documents tab (it must end up on the zaak)
  create       start a new bezwaar (judged once, on the open seed)

Needs: python3, docker (the demo stack running via ./run.sh). Only the standard library is used.
"""

import argparse
import importlib.util
import pathlib
import sys
import time

from klachten_api import StepError, api, api_ok, open_tasks, psql, submit_start_form, user_id

walkthrough = importlib.util.spec_from_file_location("bezwaar_walkthrough", pathlib.Path(__file__).with_name("bezwaar-walkthrough.py"))
bw = importlib.util.module_from_spec(walkthrough)
walkthrough.loader.exec_module(bw)
klachten_check = importlib.util.spec_from_file_location("klachten_authz_check", pathlib.Path(__file__).with_name("klachten-authz-check.py"))
kc = importlib.util.module_from_spec(klachten_check)
klachten_check.loader.exec_module(kc)

ALLOWED, DENIED = kc.ALLOWED, kc.DENIED
CASE = bw.CASE
TASK = "validate-request"

READ_CHECKS = ["list", "open", "notes", "files", "widgets", "task-list", "task-open"]
WRITE_CHECKS = ["claim", "actions", "afsluiten", "note-create", "file-upload"]
CHECKS = READ_CHECKS + WRITE_CHECKS + ["create"]
SEEDS = ["open", "afgerond"]

# What each user may do per seed. A bezwaar that is afgerond is read only for everyone.
BEHANDELAAR_READ = set(READ_CHECKS)
ADVISEUR_READ = {"list", "open", "notes", "files", "widgets"}
EXPECTED = {
    "bezwaar-behandelaar": {"open": set(CHECKS), "afgerond": BEHANDELAAR_READ},
    "bezwaar-adviseur": {"open": ADVISEUR_READ | {"note-create", "file-upload"}, "afgerond": ADVISEUR_READ},
    "klachten-kcc": {"open": set(), "afgerond": set()},
    "klachten-coordinator": {"open": set(), "afgerond": set()},
    "klachten-behandelaar-szw": {"open": set(), "afgerond": set()},
    "user": {"open": set(), "afgerond": set()},
}


class Seed:
    def __init__(self, scope, document_id):
        self.scope = scope
        self.document_id = document_id
        self.task_id = bw.wait_for_task(document_id, TASK)
        self.iot = api_ok("GET", f"/api/v1/document/{document_id}/zaaktype/documenttype", "admin")[0]["url"]
        self.uploads = 0
        if kc.upload(bw.BEHANDELAAR, self) not in (200, 201):
            raise StepError(f"seeding {scope}: the behandelaar could not upload a zaak document")
        api_ok("POST", f"/api/v1/document/{document_id}/note", bw.BEHANDELAAR, {"content": f"Notitie {scope}"})
        time.sleep(5)  # the upload process stores and links the document
        self.notes = int(psql(f"select count(*) from note where document_id = '{document_id}'")[0][0])
        self.files = kc.file_count(document_id)


def seed_all():
    seeds = {}
    for scope in SEEDS:
        document_id = bw.start_bezwaar(f"Authz-check {scope}")
        seeds[scope] = Seed(scope, document_id)
        if scope == "afgerond":
            bw.afsluiten(document_id, "Ingetrokken")
    return seeds


def run_check(user, check, seed, widget):
    d = seed.document_id
    if check == "list":
        listed = kc.paged_ids("POST", f"/api/v1/case/{CASE}/search", user, {"assigneeFilter": "ALL", "otherFilters": []})
        return (ALLOWED if d in listed else DENIED), ""
    if check == "open":
        return kc.outcome(api("GET", f"/api/v1/document/{d}", user)[0])
    if check == "notes":
        return kc.counted(*api("GET", f"/api/v1/document/{d}/note?page=0&size=100", user), seed.notes)
    if check == "files":
        return kc.counted(*api("GET", f"/api/v2/zaken-api/document/{d}/files?page=0&size=100", user), seed.files)
    if check == "widgets":
        return kc.outcome(api("GET", f"/api/v1/document/{d}/widget-tab/{widget[0]}/widget/{widget[1]}", user)[0])
    if check == "task-list":
        return (ALLOWED if seed.task_id in kc.paged_ids("POST", "/api/v3/task?filter=ALL", user, {}) else DENIED), ""
    if check == "task-open":
        task = kc.outcome(api("GET", f"/api/v1/task/{seed.task_id}", user)[0])
        form = kc.outcome(api("GET", f"/api/v2/process-link/task/{seed.task_id}", user)[0])
        return task if task[0] == form[0] else (ALLOWED, f"task {task[0]}, form {form[0]}")
    if check == "claim":
        status, _ = api("POST", f"/api/v1/task/{seed.task_id}/assign", user, {"assignee": user_id(user)})
        result = kc.outcome(status, ok=(200, 204))
        if result[0] == ALLOWED:
            api("POST", f"/api/v1/task/{seed.task_id}/unassign", "admin")
        return result
    if check == "actions":
        status, items = api("GET", f"/api/v1/case/startable-item?caseDocumentId={d}", user)
        if status != 200:
            return kc.outcome(status)
        return (ALLOWED if items else DENIED), ", ".join(i["key"] for i in items)
    if check == "afsluiten":
        return kc.outcome(api("GET", f"/api/v1/process-definition/{afsluiten_pd()}/start-form?documentId={d}", user)[0])
    if check == "note-create":
        status, _ = api("POST", f"/api/v1/document/{d}/note", user, {"content": f"Authz check: notitie van {user}"})
        return kc.outcome(status, ok=(200, 201))
    if check == "file-upload":
        before = kc.file_count(d)
        kc.upload(user, seed)
        time.sleep(5)
        # The temp upload itself is not scoped by case; what counts is whether it ends up on the zaak.
        return (ALLOWED if kc.file_count(d) > before else DENIED), ""
    if check == "create":
        try:
            created = submit_start_form(user, CASE, bw.start_data(f"Authz-check create {user}"), case=CASE)
            return (ALLOWED if created.get("documentId") else DENIED), ""
        except StepError:
            return DENIED, ""
    raise ValueError(check)


_afsluiten_pd = []


def afsluiten_pd():
    if not _afsluiten_pd:
        links = api_ok("GET", f"/api/v1/case-definition/{CASE}/case-process-link", "admin")
        _afsluiten_pd.append(next(l["id"]["processDefinitionId"] for l in links if l["processDefinitionKey"] == "afsluiten-bezwaar"))
    return _afsluiten_pd[0]


def first_widget(seed):
    tab = next(t["key"] for t in api_ok("GET", f"/api/v1/document/{seed.document_id}/tab", "admin") if t["type"] == "widgets")
    return tab, api_ok("GET", f"/api/v1/document/{seed.document_id}/widget-tab/{tab}", "admin")["widgets"][0]["key"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--user", action="append", choices=list(EXPECTED))
    parser.add_argument("--check", action="append", choices=CHECKS)
    parser.add_argument("--grant", action="append", default=[], metavar="USER=CHECK[,CHECK]",
                        help="expect these checks to be allowed on the open bezwaar (after a live policy change)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    users = args.user or list(EXPECTED)
    checks = args.check or CHECKS
    expected = {u: {s: set(c) for s, c in seeds.items()} for u, seeds in EXPECTED.items()}
    for grant in args.grant:
        user, _, granted = grant.partition("=")
        if user not in expected or not set(granted.split(",")) <= set(CHECKS):
            parser.error(f"--grant {grant}: unknown user or check")
        expected[user]["open"] |= set(granted.split(","))

    print("=== seeding")
    seeds = seed_all()
    for scope, seed in seeds.items():
        print(f"  {scope:9} document {seed.document_id}, task {seed.task_id}, {seed.notes} note(s), {seed.files} file(s)")
    widget = first_widget(seeds["open"])

    differences = []
    print("\n=== matrix (✅ as expected, ❌ differs, · = not judged)")
    print(f"  {'user':26}" + "".join(f"{s:>10}" for s in SEEDS))
    for user in users:
        cells = []
        for scope in SEEDS:
            wrong = []
            for check in checks:
                if check == "create" and scope != "open":
                    continue
                actual, detail = run_check(user, check, seeds[scope], widget)
                if actual is None:
                    continue
                want = ALLOWED if check in expected[user][scope] else DENIED
                if args.verbose:
                    print(f"     {user} {scope} {check}: {actual}" + (f" ({detail})" if detail else ""))
                if actual != want:
                    wrong.append(check)
                    differences.append(f"{user} · {scope} · {check}: expected {want}, got {actual}"
                                       + (f" ({detail})" if detail else ""))
            cells.append("✅" if not wrong else f"❌{len(wrong)}")
        print(f"  {user:26}" + "".join(f"{c:>10}" for c in cells))

    print(f"\n=== {len(differences)} difference(s)")
    for line in differences:
        print(f"  {line}")
    sys.exit(1 if differences else 0)


if __name__ == "__main__":
    main()
