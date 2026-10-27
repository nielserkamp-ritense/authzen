#!/usr/bin/env python3
"""
Walks the ToDo process through the GZAC REST API, the same way the frontend does: todo-anna creates a
ToDo and picks it up, assigns it to todo-bram, and bram completes it. Along the way it checks that the
ToDo follows its creator and assignee: bram doesn't see it before it is assigned to him, and anna can
still read it but no longer change it once it is.

Usage:
  scripts/todo-walkthrough.py [--verbose]
  scripts/todo-walkthrough.py --seed     # leave three demo ToDos for a walkthrough in the UI

Needs: python3, docker (the demo stack running via ./run.sh). Only the standard library is used.
"""

import argparse
import datetime
import importlib.util
import pathlib
import sys

from klachten_api import (
    Report, StepError, api, api_ok, incidents, psql, running_processes, short, submit_start_form,
    unexpected_backend_errors, user_id,
)

walkthrough = importlib.util.spec_from_file_location("bezwaar_walkthrough", pathlib.Path(__file__).with_name("bezwaar-walkthrough.py"))
bw = importlib.util.module_from_spec(walkthrough)
walkthrough.loader.exec_module(bw)

CASE = "todo"
ANNA, BRAM = "todo-anna", "todo-bram"


def create(user, titel, omschrijving=""):
    document_id = submit_start_form(user, CASE, {"titel": titel, "omschrijving": omschrijving}, case=CASE)["documentId"]
    bw.wait_for_status(document_id, "open")
    return document_id


def oppakken(user, document_id):
    bw.complete_task(document_id, bw.wait_for_task(document_id, "oppakken"), {}, user)
    bw.wait_for_status(document_id, "in-behandeling")


def afronden(user, document_id, toelichting="Klaar."):
    bw.complete_task(document_id, bw.wait_for_task(document_id, "afronden"), {"toelichtingAfronden": toelichting}, user)
    bw.wait_for_status(document_id, "afgerond")


def assign(user, document_id, to):
    api_ok("POST", f"/api/v1/document/{document_id}/assign", user, {"assigneeId": user_id(to)})
    bw.wait_for(lambda: assignee(document_id) == to, f"assignee {to}")


def assignee(document_id):
    rows = psql(f"select assignee_id from json_schema_document where json_schema_document_id = '{document_id}'")
    return rows[0][0] if rows and rows[0] and rows[0][0] else None


def sees(user, document_id):
    return api("GET", f"/api/v1/document/{document_id}", user)[0] == 200


def may_add_note(user, document_id):
    return api("POST", f"/api/v1/document/{document_id}/note", user, {"content": f"Notitie van {user}"})[0] in (200, 201)


def expect(report, name, actual, wanted):
    (report.ok if actual == wanted else report.fail)(name + ("" if actual == wanted else f" (got: {actual})"))


def walk(report):
    since = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("\n=== ToDo · anna creates, assigns it to bram, bram completes it")
    try:
        document_id = create(ANNA, "Rapport nalezen", "Het kwartaalrapport nalezen op fouten.")
        report.ok(f"{ANNA} created a ToDo (document {document_id}), status 'open'")
    except StepError as e:
        report.fail(f"create a ToDo: {e}")
        return
    try:
        expect(report, f"{BRAM} doesn't see it", sees(BRAM, document_id), False)
        oppakken(ANNA, document_id)
        report.ok(f"{ANNA} did 'Oppakken', status 'in-behandeling'")
        assign(ANNA, document_id, BRAM)
        report.ok(f"{ANNA} assigned it to {BRAM}")
        expect(report, f"{BRAM} sees it", sees(BRAM, document_id), True)
        expect(report, f"{ANNA} still sees it", sees(ANNA, document_id), True)
        expect(report, f"{ANNA} can no longer change it (add a note)", may_add_note(ANNA, document_id), False)
        afronden(BRAM, document_id)
        report.ok(f"{BRAM} did 'Afronden', status 'afgerond'")
    except StepError as e:
        report.fail(str(e))
    check_end_state(document_id, report, since)


def check_end_state(document_id, report, since):
    print("  --- end state")
    errors = unexpected_backend_errors(report, since)
    zaak_links = int(psql(f"select count(*) from zaak_instance_link where document_id = '{document_id}'")[0][0])
    checks = [
        ("processes ended", not running_processes(document_id), running_processes(document_id)),
        ("internal status 'afgerond'", bw.internal_status(document_id) == "afgerond", bw.internal_status(document_id)),
        ("no zaak", zaak_links == 0, zaak_links),
        ("no incidents", not incidents(document_id), len(incidents(document_id))),
        ("no ERROR lines in backend log", not errors, len(errors)),
    ]
    for name, passed, actual in checks:
        (report.ok if passed else report.fail)(name + ("" if passed else f" (got: {actual})"))
    for line in errors[:5]:
        print(f"     {short(line.splitlines()[0], 300)}")


def seed(report):
    print("\n=== seeding demo ToDos")
    try:
        groceries = create(ANNA, "Boodschappen bestellen", "Koffie en melk voor de afdeling.")
        report.ok(f"'Boodschappen bestellen' by {ANNA}, unassigned ({groceries})")
        rapport = create(ANNA, "Rapport nalezen", "Het kwartaalrapport nalezen op fouten.")
        oppakken(ANNA, rapport)
        assign(ANNA, rapport, BRAM)
        report.ok(f"'Rapport nalezen' by {ANNA}, assigned to {BRAM}, at 'Afronden' ({rapport})")
        presentatie = create(BRAM, "Presentatie voorbereiden", "Slides voor het teamoverleg.")
        report.ok(f"'Presentatie voorbereiden' by {BRAM}, unassigned ({presentatie})")
    except StepError as e:
        report.fail(f"seed: {e}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", action="store_true", help="leave three demo ToDos instead of walking one")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    report = Report(args.verbose)
    (seed if args.seed else walk)(report)
    state = "✅ passed" if not report.failures else f"❌ {len(report.failures)} failure(s)"
    print(f"\n=== summary\n  todo {'seed' if args.seed else 'walkthrough':12} {state}"
          + (f", {len(report.warnings)} warning(s)" if report.warnings else ""))
    sys.exit(1 if report.failures else 0)


if __name__ == "__main__":
    main()
