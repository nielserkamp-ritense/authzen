#!/usr/bin/env python3
"""
Seeds the demo data and checks the demo's starting state, so a presenter can trust what the demo script
(docs/demo-script.md) says each user will see.

Usage:
  scripts/demo-seed.py            # wait for the PDP, seed, check, and print the demo URLs
  scripts/demo-seed.py --check    # only check the newest demo seeds (e.g. just before presenting)

Seeds:
  klachten  'Demo SZW' and 'Demo DSO' (melder achternaam), at the task of the dienst's behandelaar
  bezwaar   'Demo open' at 'Valideer gegevens aanvrager', and 'Demo afgerond' (closed as Gegrond)
  ToDo      'Boodschappen bestellen' (anna), 'Rapport nalezen' (anna, assigned to bram) and
            'Presentatie voorbereiden' (bram)

Needs: python3, docker (the demo stack running via ./run.sh). Only the standard library is used.
"""

import argparse
import importlib.util
import pathlib
import sys
import time

from klachten_api import Report, StepError, api, open_tasks, psql, route_args, run_route


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(__file__).with_name(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kc = load("klachten_authz_check", "klachten-authz-check.py")
bw = load("bezwaar_walkthrough", "bezwaar-walkthrough.py")
tw = load("todo_walkthrough", "todo-walkthrough.py")

GZAC_UI = "http://localhost"
KLACHTEN = "eerstelijns-klachten"
PDP_TIMEOUT = 120

# name → (case, how to find the newest document with that name)
SEEDS = {
    "Demo SZW": (KLACHTEN, "json_document_content->'melder'->'personalia'->>'achternaam'"),
    "Demo DSO": (KLACHTEN, "json_document_content->'melder'->'personalia'->>'achternaam'"),
    "Demo open": (bw.CASE, "json_document_content->>'achternaam'"),
    "Demo afgerond": (bw.CASE, "json_document_content->>'achternaam'"),
    "Boodschappen bestellen": (tw.CASE, "json_document_content->>'titel'"),
    "Rapport nalezen": (tw.CASE, "json_document_content->>'titel'"),
    "Presentatie voorbereiden": (tw.CASE, "json_document_content->>'titel'"),
}


def find(name):
    case, path = SEEDS[name]
    rows = psql(f"select json_schema_document_id from json_schema_document where document_definition_name = '{case}' "
                f"and {path} = '{name}' order by created_on desc limit 1")
    if not rows or not rows[0] or not rows[0][0]:
        raise StepError(f"no demo seed '{name}' found; run scripts/demo-seed.py first")
    return rows[0][0]


def url(name):
    return f"{GZAC_UI}/cases/{SEEDS[name][0]}/document/{find(name)}"


def wait_for_pdp():
    """Before the manager has published its first bundle, the PDP denies everything."""
    deadline = time.time() + PDP_TIMEOUT
    while time.time() < deadline:
        status, body = api("GET", "/api/v1/document-definition?page=0&size=50", "klachten-kcc")
        if status == 200 and any(d["id"]["name"] == KLACHTEN for d in body.get("content", [])):
            return
        time.sleep(3)
    raise StepError(f"the PDP has no klachten policies after {PDP_TIMEOUT} s")


def seed(report):
    print("=== seeding")
    for dienst in ["SZW", "DSO"]:
        result = run_route(route_args(route="informeel-behandelaar", dienst=dienst), stop_at=kc.BEHANDELAAR_TASK,
                           melder=f"Demo {dienst}")
        if result.failures:
            raise StepError(f"klacht 'Demo {dienst}': {result.failures}")
    report.ok("klachten 'Demo SZW' and 'Demo DSO', at the behandelaar's task")
    bw.start_bezwaar("Demo open")
    bw.wait_for_task(find("Demo open"), "validate-request")
    report.ok("bezwaar 'Demo open', at 'Valideer gegevens aanvrager'")
    afgerond = bw.start_bezwaar("Demo afgerond")
    bw.complete_task(afgerond, bw.wait_for_task(afgerond, "validate-request"), {"zaaknummer": "ZAAK-2026-0042"})
    bw.complete_task(afgerond, bw.wait_for_task(afgerond, "in-behandeling"), {})
    bw.afsluiten(afgerond, "Gegrond")
    report.ok("bezwaar 'Demo afgerond', closed as Gegrond")
    todos = Report(False)
    tw.seed(todos)
    if todos.failures:
        raise StepError(f"ToDos: {todos.failures}")


# ---- the demo's claims ----------------------------------------------------------------------------

def listed(user, case, name):
    return find(name) in kc.paged_ids("POST", f"/api/v1/case/{case}/search", user, {"assigneeFilter": "ALL", "otherFilters": []})


def opens(user, name):
    return api("GET", f"/api/v1/document/{find(name)}", user)[0] == 200


def may_add_note(user, name):
    return api("POST", f"/api/v1/document/{find(name)}/note", user, {"content": f"Demo check: notitie van {user}"})[0] in (200, 201)


def actions(user, name):
    status, items = api("GET", f"/api/v1/case/startable-item?caseDocumentId={find(name)}", user)
    return sorted(i["key"] for i in items) if status == 200 else []


def sees_nothing_of(user, case):
    status, body = api("POST", f"/api/v1/case/{case}/search", user, {"assigneeFilter": "ALL", "otherFilters": []})
    return status != 200 or body.get("totalElements", 0) == 0


def sees_task(user, name):
    tasks = {t[0] for t in open_tasks(find(name))}
    return bool(tasks & kc.paged_ids("POST", "/api/v3/task?filter=ALL", user, {}))


CLAIMS = [
    ("klachten-behandelaar-szw lists 'Demo SZW'", lambda: listed("klachten-behandelaar-szw", KLACHTEN, "Demo SZW"), True),
    ("klachten-behandelaar-szw has a task on 'Demo SZW'", lambda: sees_task("klachten-behandelaar-szw", "Demo SZW"), True),
    ("klachten-behandelaar-szw doesn't list 'Demo DSO'", lambda: listed("klachten-behandelaar-szw", KLACHTEN, "Demo DSO"), False),
    ("klachten-behandelaar-szw can't open 'Demo DSO' by URL", lambda: opens("klachten-behandelaar-szw", "Demo DSO"), False),
    ("klachten-kcc lists 'Demo SZW' and 'Demo DSO'",
     lambda: listed("klachten-kcc", KLACHTEN, "Demo SZW") and listed("klachten-kcc", KLACHTEN, "Demo DSO"), True),
    ("klachten-kcc can't add a note (read only)", lambda: may_add_note("klachten-kcc", "Demo SZW"), False),
    ("klachten-kcc has no actions on 'Demo SZW'", lambda: actions("klachten-kcc", "Demo SZW"), []),
    ("bezwaar-behandelaar's actions on 'Demo open'", lambda: actions("bezwaar-behandelaar", "Demo open"),
     ["afsluiten-bezwaar", "change-name", "patch-zaak"]),
    ("bezwaar-behandelaar has no actions on 'Demo afgerond'", lambda: actions("bezwaar-behandelaar", "Demo afgerond"), []),
    ("bezwaar-adviseur opens 'Demo open'", lambda: opens("bezwaar-adviseur", "Demo open"), True),
    ("bezwaar-adviseur has no actions on 'Demo open'", lambda: actions("bezwaar-adviseur", "Demo open"), []),
    ("bezwaar-adviseur can add a note to 'Demo open'", lambda: may_add_note("bezwaar-adviseur", "Demo open"), True),
    ("bezwaar-adviseur can't add a note to 'Demo afgerond'", lambda: may_add_note("bezwaar-adviseur", "Demo afgerond"), False),
    ("todo-anna lists 'Boodschappen bestellen' and 'Rapport nalezen'",
     lambda: listed(tw.ANNA, tw.CASE, "Boodschappen bestellen") and listed(tw.ANNA, tw.CASE, "Rapport nalezen"), True),
    ("todo-anna doesn't list 'Presentatie voorbereiden'", lambda: listed(tw.ANNA, tw.CASE, "Presentatie voorbereiden"), False),
    ("todo-anna opens 'Rapport nalezen' (assigned to bram)", lambda: opens(tw.ANNA, "Rapport nalezen"), True),
    ("todo-anna can't change 'Rapport nalezen'", lambda: may_add_note(tw.ANNA, "Rapport nalezen"), False),
    ("todo-bram lists 'Presentatie voorbereiden' and 'Rapport nalezen'",
     lambda: listed(tw.BRAM, tw.CASE, "Presentatie voorbereiden") and listed(tw.BRAM, tw.CASE, "Rapport nalezen"), True),
    ("todo-bram doesn't list 'Boodschappen bestellen'", lambda: listed(tw.BRAM, tw.CASE, "Boodschappen bestellen"), False),
    ("klachten-behandelaar-szw sees no bezwaar and no ToDo",
     lambda: sees_nothing_of("klachten-behandelaar-szw", bw.CASE) and sees_nothing_of("klachten-behandelaar-szw", tw.CASE), True),
]


def check(report):
    print("=== checking the demo's starting state")
    for name, actual, wanted in CLAIMS:
        try:
            value = actual()
        except StepError as e:
            report.fail(f"{name}: {e}")
            continue
        (report.ok if value == wanted else report.fail)(name + ("" if value == wanted else f" (got: {value})"))
    # The note claims add real notes; remove them, so the demo data stays as seeded.
    psql("delete from note where content like 'Demo check: %'")


def summary():
    print("\n=== demo data")
    rows = [
        ("klachten-behandelaar-szw / klachten-kcc", "Demo SZW"), ("(denied for SZW)", "Demo DSO"),
        ("bezwaar-behandelaar / bezwaar-adviseur", "Demo open"), ("(read only)", "Demo afgerond"),
        ("todo-anna", "Boodschappen bestellen"), ("todo-anna → todo-bram", "Rapport nalezen"),
        ("todo-bram", "Presentatie voorbereiden"),
    ]
    for who, name in rows:
        print(f"  {name:26} {who:42} {url(name)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="only check the newest demo seeds")
    args = parser.parse_args()

    report = Report(False)
    try:
        if not args.check:
            wait_for_pdp()
            seed(report)
        check(report)
        if not report.failures:
            summary()
    except StepError as e:
        report.fail(str(e))
    print(f"\n=== {'✅ demo ready' if not report.failures else f'❌ {len(report.failures)} problem(s)'}")
    sys.exit(1 if report.failures else 0)


if __name__ == "__main__":
    main()
