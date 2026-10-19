#!/usr/bin/env python3
"""
Walks the Den Haag eerstelijns-klachten process end to end through the GZAC REST API,
the same way the frontend does, as the demo user that owns each task.

Usage:
  scripts/klachten-walkthrough.py --route informeel-coordinator [--dienst SZW] [--terugkoppeling off] [--post]
  scripts/klachten-walkthrough.py --route all

Routes:
  informeel-coordinator  coordinator handles the complaint (--zaakbehandelaar MIJZELF|ANDERE_KLACHTENCOORDINATOR)
  informeel-behandelaar  behandelaar of the dienst handles it, coordinator checks it
  formeel                melder disagrees with the informal solution, so it is handled formally
  commissie              coordinator hands the complaint over to the klachtencommissie

Needs: python3, docker (the demo stack running via ./run.sh). Only the standard library is used.
"""

import argparse
import sys

from klachten_api import AUTORISATIEGROEPEN_OCW, DIENSTEN, ROUTES, run_route


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--route", choices=ROUTES + ["all"], default="all")
    parser.add_argument("--dienst", choices=DIENSTEN, default="SZW")
    parser.add_argument("--autorisatiegroep", choices=list(AUTORISATIEGROEPEN_OCW), help="only for --dienst OCW")
    parser.add_argument("--zaakbehandelaar", choices=["MIJZELF", "ANDERE_KLACHTENCOORDINATOR"],
                        default="ANDERE_KLACHTENCOORDINATOR", help="for the informeel-coordinator route")
    parser.add_argument("--terugkoppeling", choices=["on", "off"], default="off")
    parser.add_argument("--post", action="store_true", help="melder wants communication via post")
    parser.add_argument("--melder-akkoord", choices=["JA", "NEE", "ONBEKEND"],
                        help="melder agrees with the informal solution (default JA; NEE continues formally)")
    parser.add_argument("--oordeel", choices=["GEGROND", "DEELS_GEGROND", "ONGEGROND", "GEEN_OORDEEL"],
                        default="ONGEGROND", help="oordeel in the informeel/formeel onderzoek; (deels) gegrond fills 3 principes")
    parser.add_argument("--oordeel-overnemen", action="store_true",
                        help="melder disagrees and the informal oordeel is taken over, so formeel skips hoor en wederhoor")
    parser.add_argument("--commissie-stoppen", action="store_true",
                        help="commissie: stop it via 'Terug naar hoofdproces'; informeel restarts and closes the case")
    parser.add_argument("--terugkoppeling-afkeuren", action="store_true",
                        help="informeel-behandelaar: the coordinator rejects the terugkoppeling once")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    routes = ROUTES if args.route == "all" else [args.route]
    results = []
    for route in routes:
        args.route = route
        results.append((route, run_route(args)))

    print("\n=== summary")
    for route, report in results:
        state = "✅ passed" if not report.failures else f"❌ {len(report.failures)} failure(s)"
        print(f"  {route:24} {state}" + (f", {len(report.warnings)} warning(s)" if report.warnings else ""))
    sys.exit(1 if any(r.failures for _, r in results) else 0)


if __name__ == "__main__":
    main()
