#!/usr/bin/env python3
"""
Dumps what the OpenFTV PDP decides for every demo role, so a policy rewrite can be compared with the
policies before it.

Usage:
  scripts/policy-filter-dump.py --out before.json
  scripts/policy-filter-dump.py --compare before.json [--role ROLE_KLACHTEN_KLACHTBEHANDELAAR_SZW ...]

For every resource type × action below it asks the PDP (the same AuthZEN evaluation GZAC sends) for
every role, and keeps:
  allow   the decision per role
  filter  the filter rows (Valtimo permissions) of that role

Rows are normalized so that equal permissions compare equal: one row per action, conditions sorted,
and `in [x]` written as `== x`. With --compare it prints per role the decisions and rows that were
added or removed, and exits with 1 when anything differs.

Needs: python3 and the demo stack running (PDP on localhost:8443). Only the standard library is used.
"""

import argparse
import json
import sys
import urllib.request

PDP = "http://localhost:8443/authzen/v1/evaluations"

ACTIONS = {
    "com.ritense.case.domain.CaseTab": ["view"],
    "com.ritense.case_.domain.definition.CaseDefinition": ["view", "view_list"],
    "com.ritense.case_.domain.tab.CaseWidgetTabWidget": ["view"],
    "com.ritense.dashboard.domain.Dashboard": ["view", "view_list"],
    "com.ritense.document.domain.impl.JsonSchemaDocument": [
        "assign", "assignable", "claim", "create", "delete", "export", "inspect", "inspect_modify", "modify", "view",
        "view_list"],
    "com.ritense.document.domain.impl.JsonSchemaDocumentDefinition": ["create", "delete", "modify", "view", "view_list"],
    "com.ritense.document.domain.impl.searchfield.SearchField": ["view_list"],
    "com.ritense.document.domain.impl.snapshot.JsonSchemaDocumentSnapshot": ["view", "view_list"],
    "com.ritense.documentenapi.authorization.ZgwDocument": ["create", "delete", "modify", "view", "view_list"],
    "com.ritense.iko.domain.IkoView": ["view", "view_list"],
    "com.ritense.note.domain.Note": ["create", "delete", "modify", "view", "view_list"],
    "com.ritense.objectenapi.security.Object": ["create", "delete", "modify", "view", "view_list"],
    "com.ritense.objectmanagement.domain.ObjectManagement": ["view_list"],
    "com.ritense.resource.authorization.ResourcePermission": ["create", "delete", "modify", "view", "view_list"],
    "com.ritense.team.domain.Team": ["assign", "create", "delete", "modify", "view", "view_list"],
    "com.ritense.valtimo.contract.authentication.User": ["view", "view_list"],
    "com.ritense.valtimo.operaton.domain.OperatonExecution": ["create"],
    "com.ritense.valtimo.operaton.domain.OperatonTask": ["assign", "assignable", "claim", "complete", "view", "view_list"],
    "com.ritense.valtimo.operaton.domain.OperatonTimer": ["complete"],
    "com.ritense.zakenapi.security.Zaak": ["view"],
}

ROLES = ["ROLE_ADMIN", "ROLE_USER"] + [f"ROLE_KLACHTEN_{r}" for r in [
    "KCC", "IB_POST", "KLACHTBEHANDELAAR_BSD_BESTUURSDIENST", "KLACHTBEHANDELAAR_DBV", "KLACHTBEHANDELAAR_DPZ",
    "KLACHTBEHANDELAAR_DSB_DIENST_STADSBEHEER", "KLACHTBEHANDELAAR_DSO", "KLACHTBEHANDELAAR_OCW_ALGEMEEN",
    "KLACHTBEHANDELAAR_OCW_JGZ", "KLACHTBEHANDELAAR_OCW_JH", "KLACHTBEHANDELAAR_SZW", "KLACHTENCOORDINATOR",
    "KLACHTENCOORDINATOR_GGD", "KLACHTENCOORDINATOR_VTH"]]


def evaluate(resource_type, action):
    evaluations = [{"subject": {"type": "user", "id": "policy-filter-dump", "properties": {"roles": [role]}},
                    "action": {"name": action}, "resource": {"type": resource_type, "id": "any"}} for role in ROLES]
    request = urllib.request.Request(PDP, json.dumps({"evaluations": evaluations}).encode(),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)["evaluations"]


def normalize(value):
    """Sorts condition lists and writes `in [x]` as `== x`, so equal permissions compare equal."""
    if isinstance(value, dict):
        value = {k: normalize(v) for k, v in value.items()}
        if value.get("operator") == "in" and isinstance(value.get("value"), list) and len(value["value"]) == 1:
            value["operator"], value["value"] = "==", value["value"][0]
        if isinstance(value.get("conditions"), list):
            value["conditions"] = sorted(value["conditions"], key=lambda c: json.dumps(c, sort_keys=True))
        return value
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def dump():
    result = {role: {"allow": [], "filter": []} for role in ROLES}
    for resource_type, actions in ACTIONS.items():
        for action in actions:
            for role, evaluation in zip(ROLES, evaluate(resource_type, action)):
                if evaluation.get("decision"):
                    result[role]["allow"].append(f"{resource_type} {action}")
                # The rows a user with only this role gets (a rule may depend on the user's roles).
                for row in (evaluation.get("context") or {}).get("filter") or []:
                    if row["role"] == role and action in row["actions"]:
                        row = normalize({**row, "actions": [action]})
                        result[role]["filter"].append(json.dumps(row, sort_keys=True))
    for entry in result.values():
        entry["allow"] = sorted(set(entry["allow"]))
        entry["filter"] = sorted(set(entry["filter"]))
    return result


def short(row):
    row = json.loads(row)
    return f"{row['resourceType'].split('.')[-1]} {row['actions'][0]}: {json.dumps(row['conditionContainer'])}" + (
        f" context {row['contextResourceType'].split('.')[-1]}: {json.dumps(row['contextConditionContainer'])}"
        if row["contextResourceType"] else "")


def compare(before, after, roles):
    differences = 0
    for role in roles:
        lines = []
        for key in ["allow", "filter"]:
            old, new = set(before.get(role, {}).get(key, [])), set(after[role][key])
            show = short if key == "filter" else str
            lines += [f"  - {key} {show(x)}" for x in sorted(old - new)]
            lines += [f"  + {key} {show(x)}" for x in sorted(new - old)]
        differences += len(lines)
        print(f"{'✅' if not lines else '❌'} {role}")
        print("\n".join(lines)) if lines else None
    print(f"=== {differences} difference(s)")
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", help="write the dump to this file")
    parser.add_argument("--compare", help="compare with an earlier dump")
    parser.add_argument("--role", action="append", choices=ROLES, help="only these roles (repeatable)")
    args = parser.parse_args()
    if not args.out and not args.compare:
        parser.error("give --out and/or --compare")

    result = dump()
    if args.out:
        with open(args.out, "w") as f:
            json.dump(result, f, indent=1)
        print(f"wrote {args.out}: {sum(len(r['filter']) for r in result.values())} rows")
    if args.compare:
        with open(args.compare) as f:
            before = json.load(f)
        sys.exit(1 if compare(before, result, args.role or ROLES) else 0)


if __name__ == "__main__":
    main()
