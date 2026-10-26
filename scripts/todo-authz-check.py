#!/usr/bin/env python3
"""
Checks, per demo user, what each user can see and do on a ToDo, against the expected matrix (EXPECTED
below): only the creator and the assignee see a ToDo; the creator changes it while it is unassigned (or
assigned to the creator), and once it is assigned to someone else only that assignee does. Everything
goes through the GZAC REST API, so every answer comes from the OpenFTV policies via AuthZEN.

Usage:
  scripts/todo-authz-check.py [--user todo-bram ...] [--check open ...] [--verbose]
                              [--grant USER=SEED:CHECK[,CHECK] ...]

--grant changes the expected matrix, to prove a live policy change: e.g. after letting every user see
every ToDo, run with --grant todo-bram=unassigned:list,open.

Every run seeds three fresh ToDos, all created by todo-anna, each with one note:
  unassigned     not assigned, at task 'Oppakken'
  self-assigned  assigned to todo-anna, at task 'Oppakken'
  assigned       picked up by todo-anna and assigned to todo-bram, at task 'Afronden'

Checks:
  list         ToDo is in the case list (case search)
  open         GET the ToDo by id (direct URL)
  notes        all notes of the ToDo are visible
  widgets      data of the ToDo widget
  task-list    the open task of the ToDo is in the task list
  task-open    GET the open task and its form by id
  note-create  add a note to the ToDo (a change)
  claim        claim the open task (undone right after)
  assign       assign the ToDo to the user themselves (undone right after)
  create       create a new ToDo (judged once, on the unassigned seed)

Needs: python3, docker (the demo stack running via ./run.sh). Only the standard library is used.
"""

import argparse
import importlib.util
import pathlib
import sys

from klachten_api import StepError, api, psql, user_id


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(__file__).with_name(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tw = load("todo_walkthrough", "todo-walkthrough.py")
kc = load("klachten_authz_check", "klachten-authz-check.py")

ALLOWED, DENIED = kc.ALLOWED, kc.DENIED
ANNA, BRAM = tw.ANNA, tw.BRAM

READ_CHECKS = ["list", "open", "notes", "widgets", "task-list", "task-open"]
WRITE_CHECKS = ["note-create", "claim", "assign"]
CHECKS = READ_CHECKS + WRITE_CHECKS + ["create"]
SEEDS = ["unassigned", "self-assigned", "assigned"]

EVERYTHING = set(READ_CHECKS + WRITE_CHECKS)
NOTHING = set()
EXPECTED = {
    ANNA: {"unassigned": EVERYTHING, "self-assigned": EVERYTHING, "assigned": set(READ_CHECKS)},
    BRAM: {"unassigned": NOTHING, "self-assigned": NOTHING, "assigned": EVERYTHING},
    "user": {"unassigned": NOTHING, "self-assigned": NOTHING, "assigned": NOTHING},
    "klachten-kcc": {"unassigned": NOTHING, "self-assigned": NOTHING, "assigned": NOTHING},
}
# Every logged-in user may create a ToDo.
CREATE = {ANNA, BRAM, "user", "klachten-kcc"}


class Seed:
    def __init__(self, scope, document_id, task_key):
        self.scope = scope
        self.document_id = document_id
        self.task_id = tw.bw.wait_for_task(document_id, task_key)
        self.assignee = tw.assignee(document_id)
        psql(f"insert into note (id, created_by_user_id, created_by_user_full_name, created_date, content, document_id) "
             f"values (gen_random_uuid(), 'authz-check', 'Authz check', now(), 'Notitie {scope}', '{document_id}')")
        self.notes = int(psql(f"select count(*) from note where document_id = '{document_id}'")[0][0])


def seed_all():
    seeds = {}
    unassigned = tw.create(ANNA, "Authz-check unassigned")
    seeds["unassigned"] = Seed("unassigned", unassigned, "oppakken")
    self_assigned = tw.create(ANNA, "Authz-check self-assigned")
    tw.assign(ANNA, self_assigned, ANNA)
    seeds["self-assigned"] = Seed("self-assigned", self_assigned, "oppakken")
    assigned = tw.create(ANNA, "Authz-check assigned")
    tw.oppakken(ANNA, assigned)
    tw.assign(ANNA, assigned, BRAM)
    seeds["assigned"] = Seed("assigned", assigned, "afronden")
    return seeds


def restore_assignee(seed):
    """Puts the seed's assignee back as it was, as admin."""
    if seed.assignee:
        api("POST", f"/api/v1/document/{seed.document_id}/assign", "admin", {"assigneeId": user_id(seed.assignee)})
    else:
        api("POST", f"/api/v1/document/{seed.document_id}/unassign", "admin")


def run_check(user, check, seed):
    d = seed.document_id
    if check == "list":
        listed = kc.paged_ids("POST", f"/api/v1/case/{tw.CASE}/search", user, {"assigneeFilter": "ALL", "otherFilters": []})
        return (ALLOWED if d in listed else DENIED), ""
    if check == "open":
        return kc.outcome(api("GET", f"/api/v1/document/{d}", user)[0])
    if check == "notes":
        return kc.counted(*api("GET", f"/api/v1/document/{d}/note?page=0&size=100", user), seed.notes)
    if check == "widgets":
        return kc.outcome(api("GET", f"/api/v1/document/{d}/widget-tab/widgets/widget/todo", user)[0])
    if check == "task-list":
        return (ALLOWED if seed.task_id in kc.paged_ids("POST", "/api/v3/task?filter=ALL", user, {}) else DENIED), ""
    if check == "task-open":
        task = kc.outcome(api("GET", f"/api/v1/task/{seed.task_id}", user)[0])
        form = kc.outcome(api("GET", f"/api/v2/process-link/task/{seed.task_id}", user)[0])
        return task if task[0] == form[0] else (ALLOWED, f"task {task[0]}, form {form[0]}")
    if check == "note-create":
        status, _ = api("POST", f"/api/v1/document/{d}/note", user, {"content": f"Authz check: notitie van {user}"})
        if status in (200, 201):
            seed.notes += 1
        return kc.outcome(status, ok=(200, 201))
    if check == "claim":
        rows = psql(f"select assignee_ from act_ru_task where id_ = '{seed.task_id}'")
        before = rows[0][0] if rows and rows[0] and rows[0][0] else None
        status, _ = api("POST", f"/api/v1/task/{seed.task_id}/assign", user, {"assignee": user_id(user)})
        result = kc.outcome(status, ok=(200, 204))
        if result[0] == ALLOWED:
            if before:
                api("POST", f"/api/v1/task/{seed.task_id}/assign", "admin", {"assignee": user_id(before)})
            else:
                api("POST", f"/api/v1/task/{seed.task_id}/unassign", "admin")
        return result
    if check == "assign":
        status, _ = api("POST", f"/api/v1/document/{d}/assign", user, {"assigneeId": user_id(user)})
        # A refused assign comes back as 400 from Valtimo; what counts is whether the assignee changed.
        changed = tw.assignee(d) == user and seed.assignee != user
        allowed = status in (200, 204) and (changed or seed.assignee == user)
        if changed:
            restore_assignee(seed)
        return (ALLOWED if allowed else DENIED), "" if status in (200, 204, 400, 403, 404) else f"HTTP {status}"
    if check == "create":
        try:
            created = tw.create(user, f"Authz-check create {user}")
            return (ALLOWED if created else DENIED), ""
        except StepError:
            return DENIED, ""
    raise ValueError(check)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--user", action="append", choices=list(EXPECTED))
    parser.add_argument("--check", action="append", choices=CHECKS)
    parser.add_argument("--grant", action="append", default=[], metavar="USER=SEED:CHECK[,CHECK]",
                        help="expect these checks to be allowed (after a live policy change)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    users = args.user or list(EXPECTED)
    checks = args.check or CHECKS
    expected = {u: {s: set(c) for s, c in seeds.items()} for u, seeds in EXPECTED.items()}
    for grant in args.grant:
        user, _, rest = grant.partition("=")
        scope, _, granted = rest.partition(":")
        if user not in expected or scope not in SEEDS or not set(granted.split(",")) <= set(CHECKS):
            parser.error(f"--grant {grant}: unknown user, seed or check")
        expected[user][scope] |= set(granted.split(","))

    print("=== seeding")
    seeds = seed_all()
    for scope, seed in seeds.items():
        print(f"  {scope:14} document {seed.document_id}, assignee {seed.assignee}, task {seed.task_id}")

    differences = []
    print("\n=== matrix (✅ as expected, ❌ differs)")
    print(f"  {'user':16}" + "".join(f"{s:>16}" for s in SEEDS))
    for user in users:
        cells = []
        for scope in SEEDS:
            wrong = []
            for check in checks:
                if check == "create" and scope != "unassigned":
                    continue
                actual, detail = run_check(user, check, seeds[scope])
                if actual is None:
                    continue
                allowed = user in CREATE if check == "create" else check in expected[user][scope]
                want = ALLOWED if allowed else DENIED
                if args.verbose:
                    print(f"     {user} {scope} {check}: {actual}" + (f" ({detail})" if detail else ""))
                if actual != want:
                    wrong.append(check)
                    differences.append(f"{user} · {scope} · {check}: expected {want}, got {actual}"
                                       + (f" ({detail})" if detail else ""))
            cells.append("✅" if not wrong else f"❌{len(wrong)}")
        print(f"  {user:16}" + "".join(f"{c:>16}" for c in cells))

    print(f"\n=== {len(differences)} difference(s)")
    for line in differences:
        print(f"  {line}")
    sys.exit(1 if differences else 0)


if __name__ == "__main__":
    main()
