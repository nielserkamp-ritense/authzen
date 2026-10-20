#!/usr/bin/env python3
"""
Checks that the OpenFTV Rego policies compile, before they reach the PDP.

Usage:
  scripts/policy-check.py             # the seed files in docker/openftv-imports/manager/policies
  scripts/policy-check.py --manager   # the policies in the running manager, before "Publiceren"

The manager doesn't check Rego: a policy that doesn't compile is still published as "Finished
successfully", and the PDP then silently drops the klachten rights of every role. This runs
`opa check` on the policies with the same OPA version as the PDP, and exits with 1 on any error.
It only finds parse and compile errors, not rules that conflict at evaluation time.

Needs: python3 and docker; --manager also needs the demo stack running (manager API on
localhost:9000). Only the standard library is used.
"""

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile
import urllib.request

# Keep in sync with github.com/open-policy-agent/opa in open-ftv/go.mod.
OPA_IMAGE = "openpolicyagent/opa:1.18.2"
ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "docker/openftv-imports/manager/policies"
MANAGER = "http://localhost:9000/v1"


def get(path):
    with urllib.request.urlopen(MANAGER + path, timeout=10) as resp:
        return json.load(resp)


def fetch_manager_policies(target):
    """Writes every Rego policy in the manager to target as <title>.rego, and returns the count."""
    policies = [p for p in get("/policies") if p.get("language") == "rego"]
    for policy in policies:
        title = policy.get("metadata", {}).get("title") or policy["id"]
        (target / f"{title}.rego").write_text(get(f"/policy/{policy['id']}")["data"])
    return len(policies)


def opa_check(directory):
    cmd = ["docker", "run", "--rm", "-v", f"{directory}:/policies:ro", OPA_IMAGE,
           "check", "/policies", "--ignore", "*.meta", "--ignore", "cedar"]
    return subprocess.run(cmd).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manager", action="store_true", help="check the policies in the running manager")
    args = parser.parse_args()

    if not args.manager:
        count = len(list(SEED_DIR.glob("*.rego")))
        code = opa_check(SEED_DIR)
        source, advice = SEED_DIR.relative_to(ROOT), "Fix them before ./run.sh --reload-policies."
    else:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                count = fetch_manager_policies(pathlib.Path(tmp))
            except OSError as e:
                print(f"Error: can't read the policies from the manager at {MANAGER}: {e}", file=sys.stderr)
                return 2
            code = opa_check(tmp)
        source, advice = "the manager", "Fix them before you publish."

    if code == 0:
        print(f"OK: {count} policies in {source} compile.")
    else:
        print(f"FAILED: the policies in {source} don't compile. {advice}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
