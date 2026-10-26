#!/usr/bin/env python3
"""
Walks the bezwaar process end to end through the GZAC REST API, the same way the frontend does, as
bezwaar-behandelaar: start a bezwaar, do both tasks, run the user actions 'Wijzigen aanvraaggegevens'
and 'Zaak bijwerken', and close it with 'Afsluiten bezwaar'.

Usage:
  scripts/bezwaar-walkthrough.py [--resultaat Gegrond|Afgewezen|Ingetrokken] [--verbose]

Needs: python3, docker (the demo stack running via ./run.sh). Only the standard library is used.
"""

import argparse
import datetime
import sys
import time

from klachten_api import (
    STEP_TIMEOUT, Report, StepError, api_ok, incidents, open_tasks, psql, running_processes, short,
    submit_start_form, unexpected_backend_errors, user_id, zaak_state,
)

CASE = "bezwaar"
BEHANDELAAR = "bezwaar-behandelaar"
RESULTATEN = ["Gegrond", "Afgewezen", "Ingetrokken"]


def start_data(achternaam="Bakker"):
    return {
        "aanhef": "Mevrouw", "voornaam": "Fatima", "achternaam": achternaam, "bsn": "999990755",
        "straatnaam": "Spui", "huisnummer": "70", "postcode": "2511 BT", "plaats": "Den Haag",
        "telefoonnummer": "0701234567", "e-mailadres": "f.bakker@example.org",
        "zaaknummer": "ZAAK-2026-0042", "datumBesluit": "01-10-2026", "naamBeslisser": "J. de Vries",
        "besluit": "De aanvraag voor een parkeervergunning is afgewezen.",
        "bezwaar": "Ik woon in het vergunninggebied en heb recht op een vergunning.",
    }


def internal_status(document_id):
    rows = psql(f"select internal_case_status_key from json_schema_document where json_schema_document_id = '{document_id}'")
    return rows[0][0] if rows else None


def content(document_id, field):
    return psql(f"select json_document_content->>'{field}' from json_schema_document "
                f"where json_schema_document_id = '{document_id}'")[0][0]


def wait_for(check, what):
    deadline = time.time() + STEP_TIMEOUT
    while time.time() < deadline:
        value = check()
        if value:
            return value
        time.sleep(1)
    raise StepError(f"timed out waiting for {what}")


def wait_for_task(document_id, task_key):
    return wait_for(lambda: next((t[0] for t in open_tasks(document_id) if t[2] == task_key), None), f"task {task_key}")


def wait_for_status(document_id, status):
    return wait_for(lambda: internal_status(document_id) == status, f"internal status {status}")


def complete_task(document_id, task_id, data, user=BEHANDELAAR):
    api_ok("POST", f"/api/v1/task/{task_id}/assign", user, {"assignee": user_id(user)})
    link = api_ok("GET", f"/api/v2/process-link/task/{task_id}", user)
    api_ok("POST", f"/api/v1/process-link/{link['processLinkId']}/form/submission"
                   f"?documentId={document_id}&taskInstanceId={task_id}", user, data)


def start_bezwaar(achternaam="Bakker", user=BEHANDELAAR):
    return submit_start_form(user, CASE, start_data(achternaam), case=CASE)["documentId"]


def afsluiten(document_id, resultaat, user=BEHANDELAAR):
    submit_start_form(user, "afsluiten-bezwaar", {"pv": {"resultaat": resultaat, "toelichting": f"Bezwaar: {resultaat}."}},
                      document_id, CASE)
    wait_for_status(document_id, "afgerond")


def walk(resultaat, report):
    since = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"\n=== bezwaar · afsluiten met resultaat {resultaat}")
    document_id = None
    steps = [
        ("task 'Valideer gegevens aanvrager'", lambda: complete_task(
            document_id, wait_for_task(document_id, "validate-request"), {"zaaknummer": "ZAAK-2026-0042", "bsn": "999990755"})),
        ("status 'in-behandeling'", lambda: wait_for_status(document_id, "in-behandeling")),
        ("task 'In behandeling'", lambda: complete_task(document_id, wait_for_task(document_id, "in-behandeling"), {})),
        ("status 'informatieverzoek-uitgezet'", lambda: wait_for_status(document_id, "informatieverzoek-uitgezet")),
        ("user action 'Wijzigen aanvraaggegevens'", lambda: wijzigen(document_id)),
        ("user action 'Zaak bijwerken'", lambda: submit_start_form(
            BEHANDELAAR, "patch-zaak", {"pv": {"description": "Bezwaar parkeervergunning"}}, document_id, CASE)),
        ("user action 'Afsluiten bezwaar'", lambda: afsluiten(document_id, resultaat)),
    ]
    try:
        document_id = start_bezwaar()
        wait_for_status(document_id, "aanvraag-ontvangen")
        report.ok(f"started a bezwaar as {BEHANDELAAR} (document {document_id}), status 'aanvraag-ontvangen'")
    except StepError as e:
        report.fail(f"start a bezwaar: {e}")
        return
    for name, step in steps:
        try:
            step()
            report.ok(name)
        except StepError as e:
            report.fail(f"{name}: {e}")
            break
    check_end_state(document_id, resultaat, report, since)


def wijzigen(document_id):
    submit_start_form(BEHANDELAAR, "change-name", {}, document_id, CASE)
    complete_task(document_id, wait_for_task(document_id, "change-name-task"), start_data("Bakker-Jansen"))
    wait_for(lambda: content(document_id, "achternaam") == "Bakker-Jansen", "the changed achternaam")


def check_end_state(document_id, resultaat, report, since):
    zaak = zaak_state(document_id)
    print("  --- end state")
    errors = unexpected_backend_errors(report, since)
    checks = [
        ("processes ended", not running_processes(document_id), running_processes(document_id)),
        ("internal status 'afgerond'", internal_status(document_id) == "afgerond", internal_status(document_id)),
        ("zaak status 'Zaak afgerond'", zaak["status"] == "Zaak afgerond", zaak["status"]),
        (f"zaak resultaat '{resultaat}'", zaak["resultaat"] == resultaat, zaak["resultaat"]),
        ("no incidents", not incidents(document_id), len(incidents(document_id))),
        ("no ERROR lines in backend log", not errors, len(errors)),
    ]
    for name, passed, actual in checks:
        (report.ok if passed else report.fail)(name + ("" if passed else f" (got: {actual})"))
    for line in errors[:5]:
        print(f"     {short(line.splitlines()[0], 300)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--resultaat", choices=RESULTATEN, default="Gegrond")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    report = Report(args.verbose)
    walk(args.resultaat, report)
    state = "✅ passed" if not report.failures else f"❌ {len(report.failures)} failure(s)"
    print(f"\n=== summary\n  bezwaar {args.resultaat:12} {state}" + (f", {len(report.warnings)} warning(s)" if report.warnings else ""))
    sys.exit(1 if report.failures else 0)


if __name__ == "__main__":
    main()
