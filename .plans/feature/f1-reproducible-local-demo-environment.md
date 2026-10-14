# Feature F1: Reproducible local demo environment

Epic: [klachten-process-den-haag-demo](../../.plan/epic/klachten-process-den-haag-demo.md)
Requirements: BR3; FR1, FR2, FR3

## Goal

As a **Ritense colleague (demo presenter, developer or consultant)**,
I want **to start the complete GZAC + OpenFTV + AuthZEN demo with a single command from a clean checkout**,
Because **then I can give or explore the externalized-authorization demo without help from the PoC owner and without manual setup steps**.

## Research

### Current state

| Area | Today | Problem for reproducibility |
|---|---|---|
| `run.sh` | `cd gzac && ./gradlew build`, then `docker compose --profile gzac up --build` | No shebang or `set -e`. Needs a host JDK 21 and ~6 GB Gradle heap (`gzac/gradle.properties`). No reset option. |
| GZAC build | `gzac/settings.gradle` uses `includeBuild("../valtimo")` (composite build). `gzac/Dockerfile` only copies a prebuilt `build/libs/gzac-*.war`. | The image depends on a host build. A missing or uninitialised `valtimo` submodule breaks it. |
| Submodules | `valtimo` and `open-ftv` point to public forks via SSH (`git@github.com:nielserkamp-ritense/...`). | SSH needs a GitHub key, even though the repos are public. |
| Keycloak (GZAC) | `docker/gzac-imports/keycloak/realm.json` is imported with `--import-realm`. All `ROLE_KLACHTEN_*` realm roles exist. | **No demo users** for the klachten roles. Only the generic admin/developer/user users exist. |
| Open Zaak | `docker/gzac-imports/open-zaak/init-db.sql` (DB dump) contains klachten zaaktypen and roltypen. | Loaded only on first DB init. Needs verification that it matches the case definition `eerstelijns-klachten/1-0-7`. |
| GZAC config | Case definition, BPMN, forms and permissions live in `gzac/src/main/resources/config/` and are autodeployed at startup. | Works as long as the build works. |
| OpenFTV policies | `docker/openftv-imports/manager/policies/*.rego(.meta)` are seeded by `apps/manager/server/seed.go` **only when the policy store is empty**. They are pushed to the PDP via bundle `manager/bundles/pdp1.yaml` (tags `valtimo`, `klachten`). | `openftv-database` has no volume, so state survives `up` and is lost on `down`. After a `git pull` with policy changes, a plain restart keeps the old policies. |
| Policy sources | `scripts/permissions-to-rego.py` converts `temp/*.permission.json` into Rego. | `temp/` is gitignored. The generated Rego is in git, so this does not block startup. The same permission JSON also exists in `gzac/src/main/resources/config/global/permission/`. |
| Networking | `gzac-backend` uses `host.docker.internal` for Open Zaak, Objecten etc., and has `extra_hosts` only for `keycloak.localhost`. | `host.docker.internal` is not resolvable on every Docker runtime. The setup must not depend on the host runtime. |
| IKO | `SPRING_DATA_REDIS_HOST: iko-redis`, but the service is `gzac-iko-redis` (container `authzen-iko-redis`). | The hostname is probably unresolvable. Needs verification. |
| Startup order | `gzac-backend` depends only on `gzac-keycloak`. | The backend can start before Open Zaak, Objecten or the PDP are ready. |
| Leftovers | `gzac-imports/open-klanten`, `gzac-imports/open-formulieren`, `keycloak/realm-2.backup`, `manager/bundles/openftv.yaml.todo` | Not used by compose. Confusing for newcomers. |
| README | Root README has a typo (`./run/sh`) and lists only 2 URLs. `gzac/README.md` is copied from the Valtimo monorepo and is wrong. | Doesn't meet FR3: no prerequisites, accounts, ports or limitations. |

### Decisions (confirmed with PoC owner)

- The GZAC backend is built **inside Docker** (multi-stage). The only prerequisites are Docker and git.
- The submodule forks are public. Switch the URLs to **HTTPS** so no SSH key is needed.
- F1 **creates one Keycloak demo user per FR6 role**. F3 then checks what each user can see.
- `run.sh` **keeps state by default**. `--reset` wipes volumes so seeds and policies match git again.

### Side effects

- A Docker build of the composite gzac+valtimo build is slow on first run (Gradle download + full Valtimo compile). A Gradle cache mount (BuildKit `--mount=type=cache`) limits this on later runs.
- Docker needs enough memory (≥ 8 GB for the Gradle build plus ~25 containers). Document the minimum resources Docker needs.
- Changing the submodule URL changes `.gitmodules`. Existing clones need `git submodule sync`.
- Keycloak `--import-realm` skips a realm that already exists. New users only show up after `--reset` (or on a fresh DB).

## Acceptance criteria

1. On a clean clone with `git submodule update --init` (no SSH key, no host JDK), `./run.sh` builds and starts all services without manual steps.
2. `./run.sh` stops with a clear error on a missing prerequisite (Docker, Compose v2, uninitialised submodules) or a failing build step.
3. `./run.sh --reset` removes all demo state (containers + volumes) and starts fresh. A plain `./run.sh` keeps existing state.
4. After startup:
   - The klachten zaaktypen are present in Open Zaak, and the `eerstelijns-klachten` case definition, BPMN and forms are deployed in GZAC without errors in the backend log.
   - A Keycloak demo user exists for every FR6 role: KCC, IB/Post, the 9 klachtenbehandelaar afdelingen, and klachtencoördinator general/GGD/VTH.
   - All klachten policies are visible in the OpenFTV manager UI and loaded in the PDP bundle.
5. GZAC backend starts only after its dependencies (Keycloak, DB, Open Zaak, Objecten/Objecttypen, PDP) are healthy.
6. The setup is system agnostic: it relies only on Docker, Compose v2, git and a bash-compatible shell, with no OS- or Docker-runtime-specific configuration.
7. The README lists prerequisites, start/reset/stop commands, all relevant URLs/ports, admin credentials, the test account per role, and known limitations. Someone other than Niels can start the demo with only the README (verified by a walk-through).

## Stories

### S1: Build GZAC backend inside Docker

**Description:** Remove the host JDK/Gradle dependency by building the gzac war, including the Valtimo composite build, in a multi-stage Docker build.

**Steps:**
1. Change the compose build context of `gzac-backend` to the repo root (so both `gzac/` and `valtimo/` are in context). Add a `.dockerignore` that excludes `build/`, `.gradle/`, `node_modules`, `open-ftv`, `docker`, `temp`.
2. Rewrite `gzac/Dockerfile` as multi-stage: a JDK 21 build stage runs `./gradlew build -x test` in `gzac/` (with `valtimoDir=../valtimo`), and the `eclipse-temurin:21-jre` runtime stage copies the war.
3. Add a BuildKit cache mount for `~/.gradle` to speed up rebuilds.
4. Keep the debug entrypoint (port 5005) from compose.
5. Check that the image builds from a clean clone and that the backend starts.

### S2: Make submodules cloneable without SSH

**Description:** Switch submodule URLs to HTTPS so anyone can clone the public forks.

**Steps:**
1. Change `.gitmodules` URLs to `https://github.com/nielserkamp-ritense/{valtimo,open-ftv}.git`.
2. Run `git submodule sync` and check that the pinned commits are pushed to the forks.
3. Test with `git clone --recurse-submodules` in a fresh directory, with no SSH agent.

### S3: Robust `run.sh` with prerequisite checks and `--reset`

**Description:** Turn `run.sh` into a reliable single entry point.

**Steps:**
1. Add `#!/usr/bin/env bash`, `set -euo pipefail`, and make the script runnable from any directory (resolve the repo root).
2. Check the prerequisites: `docker`, `docker compose` v2, Docker daemon running, submodules initialised (e.g. `valtimo/settings.gradle` and `open-ftv/apps` exist). If any is missing, print a clear message and exit.
3. Remove the host Gradle step (S1).
4. Add flags: `--reset` (`docker compose --profile gzac down -v --remove-orphans` first), `--stop`, and optionally `--detach`.
5. Run `docker compose --profile gzac up --build` and print the main URLs when the services are healthy (when detached).
6. Use no named volumes: state lives only in the containers (and their anonymous volumes), so `--stop` keeps it and `--down`/`--reset` (`down -v`) wipes everything.

### S4: Fix compose startup order, networking and leftovers

**Description:** Make the stack start reliably on any Docker host.

**Steps:**
1. Remove the dependency on `host.docker.internal`: switch to Docker service names (e.g. `gzac-openzaak:8000`), adjusting `VALTIMO_DOCKER_FILTER_PORTS`/`ALLOWED_HOSTS` where needed. Use `extra_hosts: host-gateway` only where a host-reachable URL is unavoidable (e.g. `keycloak.localhost` issuer).
2. Add healthchecks where they are missing (gzac-database, keycloak-database, openzaak, openzaak-database).
3. Make `gzac-backend` `depends_on` the healthy services: Keycloak, gzac-database, Open Zaak, Objecten/Objecttypen (and the import jobs completed), and `openftv-pdp`.
4. Make `gzac-frontend` wait for the backend's health/readiness endpoint.
5. Fix the IKO redis hostname (`iko-redis` → `gzac-iko-redis`) after you confirm the error in the logs.
6. Remove or document the unused imports (`open-klanten`, `open-formulieren`, `realm-2.backup`, `openftv.yaml.todo`).
7. Run a full `--reset` start and check the logs for connection errors.

### S5: Seed Keycloak demo users per role

**Description:** Add one GZAC Keycloak user for each FR6 role to the realm import.

**Steps:**
1. Map each FR6 role to its existing `ROLE_KLACHTEN_*` realm role. Check the names against the role values in the Rego policies and `global/role` config. Note: OCW maps to `..._OCW_ALGEMEEN`, and DSB maps to `..._DSB_DIENST_STADSBEHEER`.
2. Define usernames (e.g. `kcc`, `ibpost`, `behandelaar-szw`, …, `coordinator`, `coordinator-ggd`, `coordinator-vth`) with password = username, a first and last name, an email, and the realm roles `ROLE_USER` + the role.
3. Add the users to `docker/gzac-imports/keycloak/realm.json`. A helper script that generates them keeps this maintainable.
4. Run `./run.sh --reset`, then log in to GZAC as each user.

### S6: Verify and fix automatic seeding (Open Zaak, GZAC config, OpenFTV)

**Description:** Make sure all domain seed data is present after a fresh start, with no manual steps.

**Steps:**
1. Open Zaak: after `--reset`, use the Catalogi API to check that the klachten zaaktypen are published and match the zaaktype URL/identification used by the case definition and plugin configuration (`plugin-configurations/app.pluginconfig.json`).
2. GZAC: check that the backend log shows a successful autodeploy of `eerstelijns-klachten/1-0-7`, its forms, the permissions and the plugin configurations.
3. OpenFTV: check that the manager log shows `seed:` for every `.rego` file, that the policies appear in the UI with tag `klachten`/`valtimo`, and that the PDP receives the bundle (PDP log / health).
4. Document the "seed only on empty store" behaviour and that `--reset` is needed after policy changes in git.
5. Optional: move the source `*.permission.json` for `permissions-to-rego.py` from `temp/` to a tracked folder (or point it at `gzac/.../global/permission`), so regenerating policies is reproducible.

### S7: Rewrite the README

**Description:** Write a README that lets anyone start and use the demo on their own.

**Steps:**
1. Prerequisites: Docker + Compose v2, git, a bash-compatible shell, and minimum memory/disk for Docker. No OS-specific instructions.
2. Quick start: `git clone --recurse-submodules …` → `./run.sh`. Include the expected first-build duration.
3. Commands: start, `--reset`, `--stop`, and when to reset (after pulling seed/policy changes).
4. URL/port table: GZAC frontend, GZAC backend, GZAC Keycloak admin, OpenFTV UI, OpenFTV manager/PDP, Open Zaak admin, Objecten/Objecttypen admin, debug port 5005.
5. Accounts: admin credentials per service, and the demo user table (username / password / role / what they should see).
6. Known limitations and troubleshooting (first build slow, port conflicts, Keycloak realm not re-imported, policy seed only on empty DB).
7. Fix or replace the stale `gzac/README.md`.

### S8: Clean-checkout validation

**Description:** Prove AC1–AC7 end to end.

**Steps:**
1. In a fresh directory (no Gradle/Docker caches if possible), clone via HTTPS with submodules and run `./run.sh` following only the README.
2. Tick each acceptance criterion and record any manual intervention as a bug.
3. Repeat on a second, different machine/OS to confirm nothing is system-specific.
4. Have a colleague other than Niels do the walk-through and give feedback. Fix any gaps.
