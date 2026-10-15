#!/usr/bin/env python3
"""
Checks the eerstelijns-klachten forms against the document definition (JSON schema).

Reports, per form:
  - submitted input fields whose document path is not in the schema. The schema uses
    additionalProperties: false, so such a field makes the form submission fail;
  - simple conditionals (conditional.when) that point at neither a field in the form nor a
    document path in the schema (Form.io also resolves `when` against the submission data).

Process variables (pv.* / pv:*), layout components, containers and input: false fields are not
document fields and are skipped.

Usage:
  scripts/check-forms-schema.py [case-dir]

Exits 1 when anything is found. Only the standard library is used.
"""

import glob
import json
import os
import sys

DEFAULT_CASE_DIR = "gzac/src/main/resources/config/case/eerstelijns-klachten/1-0-7"
LAYOUT = {"panel", "columns", "fieldset", "well", "content", "htmlelement", "button", "table", "tabs"}
NESTING = {"container", "datagrid", "editgrid"}


class Schema:
    def __init__(self, path):
        self.root = json.load(open(path, encoding="utf-8"))
        self.definitions = self.root.get("definitions", {})

    def resolve(self, node):
        while isinstance(node, dict) and "$ref" in node:
            node = self.definitions[node["$ref"].split("/")[-1]]
        return node

    def has(self, path):
        node = self.root
        for part in path:
            node = self.resolve(node)
            if "items" in node:
                node = self.resolve(node["items"])
            properties = node.get("properties")
            if properties is None:
                return True  # untyped value: anything goes
            if part not in properties:
                return False
            node = properties[part]
        return True


def is_process_variable(key):
    return key.startswith("pv.") or key.startswith("pv:")


def check_form(form, schema):
    fields, keys, problems, conditionals = set(), set(), [], []

    def walk(components, prefix):
        for c in components or []:
            if not isinstance(c, dict):
                continue
            key, kind, path = c.get("key"), c.get("type"), prefix
            if key and kind not in LAYOUT:
                full = prefix + key.split(".")
                keys.add(key)
                fields.add(".".join(full))
                when = (c.get("conditional") or {}).get("when")
                if when:
                    conditionals.append((".".join(full), when))
                if kind in NESTING:
                    path = full
                elif c.get("input", True) and not is_process_variable(key) and not schema.has(full):
                    problems.append(f"field not in schema: {'.'.join(full)} ({kind})")
            walk(c.get("components"), path)
            for column in c.get("columns") or []:
                walk(column.get("components") if isinstance(column, dict) else None, path)
            for row in c.get("rows") or []:
                for cell in row if isinstance(row, list) else []:
                    walk(cell.get("components") if isinstance(cell, dict) else None, path)

    walk(form.get("components"), [])
    for field, when in conditionals:
        if when not in fields and when not in keys and not schema.has(when.split(".")):
            problems.append(f"conditional of {field} points at a missing field: {when}")
    return problems


def main():
    case_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CASE_DIR
    schemas = glob.glob(os.path.join(case_dir, "document/definition/*.json"))
    if len(schemas) != 1:
        sys.exit(f"expected one document definition in {case_dir}, found {len(schemas)}")
    schema = Schema(schemas[0])

    found = 0
    forms = sorted(glob.glob(os.path.join(case_dir, "form/*.json")))
    for path in forms:
        problems = check_form(json.load(open(path, encoding="utf-8")), schema)
        if problems:
            print(os.path.basename(path))
            for problem in problems:
                print(f"  ❌ {problem}")
            found += len(problems)
    print(f"{len(forms)} forms checked, {found} problem(s)")
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
