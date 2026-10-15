# AuthZEN + GZAC proof of concept

A local demo of GZAC (Valtimo) with fully externalized authorization. GZAC asks an [OpenFTV](https://gitlab.com/digilab.overheid.nl/ecosystem/ftv/open-ftv) policy decision point (PDP) through the [AuthZEN](https://openid.net/wg/authzen/) API instead of using its built-in permissions. The demo uses the klachten (complaints) process of Gemeente Den Haag with one role per afdeling.

## Prerequisites

- Docker with Compose v2 (`docker compose`)
- git
- A bash-compatible shell
- Docker resources: at least **10 GB memory** and about **20 GB free disk**. The stack uses about 7 GB when running, and the GZAC build uses up to 6 GB.

No JDK, Gradle or Node is needed on the host. Everything is built inside Docker.

## Quick start

```bash
git clone --recurse-submodules https://github.com/nielserkamp-ritense/authzen.git
cd authzen
./run.sh
```

For an existing clone without submodules, run `git submodule update --init` first.

The first run builds the GZAC backend (including Valtimo) and the OpenFTV images. This takes about 8 minutes. Later runs reuse the Docker cache. The stack is ready when GZAC opens at http://localhost.

## Commands

| Command | What it does |
|---|---|
| `./run.sh` | Build and start the stack in the foreground. Existing containers are reused, so data is kept. |
| `./run.sh -d` | Same, in the background. Returns once the GZAC backend is healthy. |
| `./run.sh --stop` | Stop the stack. Containers and data are kept; `./run.sh` resumes. |
| `./run.sh --down` | Remove all containers, networks and volumes. Nothing persists. |
| `./run.sh --reset` | `--down`, then start fresh. Combine with `-d` to run in the background. |
| `./run.sh --help` | Show usage. |

Use `--reset` after pulling changes to seed data, the Keycloak realm or OpenFTV policies (see [Known limitations](#known-limitations)).

## Services

| Service | URL | Login |
|---|---|---|
| GZAC frontend | http://localhost | see [Demo accounts](#demo-accounts) |
| GZAC backend | http://localhost:8080 (debug port 5005) | |
| GZAC Keycloak | http://localhost:8081/auth | `admin` / `admin` |
| OpenFTV management UI | http://localhost:8180 | `admin-user`, `author-user`, `auditor-user` / `password` |
| OpenFTV Keycloak | http://localhost:8088 | `admin` / `admin` |
| OpenFTV manager API | http://localhost:9000 | |
| OpenFTV PDP (AuthZEN) | http://localhost:8443/.well-known/authzen-configuration | |
| Open Zaak | http://localhost:8001/admin/ | `admin` / `admin` |
| Objecten API | http://localhost:8010/admin/ | `admin` / `admin` |
| Objecttypen API | http://localhost:8011/admin/ | `admin` / `admin` |
| Open Notificaties | http://localhost:8002/admin/ | |
| RabbitMQ (GZAC) | http://localhost:15672 | `guest` / `guest` |

## Demo accounts

All demo users log in to GZAC at http://localhost. The password is the same as the username.

| Username | Role | Scope |
|---|---|---|
| `klachten-kcc` | `ROLE_KLACHTEN_KCC` | Medewerker KCC: registers complaints |
| `klachten-ibpost` | `ROLE_KLACHTEN_IB_POST` | Medewerker IB/Post: assigns complaints to an afdeling |
| `klachten-behandelaar-bsd` | `ROLE_KLACHTEN_KLACHTBEHANDELAAR_BSD_BESTUURSDIENST` | Klachtenbehandelaar BSD-Bestuursdienst |
| `klachten-behandelaar-dbv` | `ROLE_KLACHTEN_KLACHTBEHANDELAAR_DBV` | Klachtenbehandelaar DBV |
| `klachten-behandelaar-dpz` | `ROLE_KLACHTEN_KLACHTBEHANDELAAR_DPZ` | Klachtenbehandelaar DPZ |
| `klachten-behandelaar-dsb` | `ROLE_KLACHTEN_KLACHTBEHANDELAAR_DSB_DIENST_STADSBEHEER` | Klachtenbehandelaar DSB |
| `klachten-behandelaar-dso` | `ROLE_KLACHTEN_KLACHTBEHANDELAAR_DSO` | Klachtenbehandelaar DSO |
| `klachten-behandelaar-ocw` | `ROLE_KLACHTEN_KLACHTBEHANDELAAR_OCW_ALGEMEEN` | Klachtenbehandelaar OCW |
| `klachten-behandelaar-ocw-jgz` | `ROLE_KLACHTEN_KLACHTBEHANDELAAR_OCW_JGZ` | Klachtenbehandelaar OCW-JGZ |
| `klachten-behandelaar-ocw-jh` | `ROLE_KLACHTEN_KLACHTBEHANDELAAR_OCW_JH` | Klachtenbehandelaar OCW-JH |
| `klachten-behandelaar-szw` | `ROLE_KLACHTEN_KLACHTBEHANDELAAR_SZW` | Klachtenbehandelaar SZW |
| `klachten-coordinator` | `ROLE_KLACHTEN_KLACHTENCOORDINATOR` | Klachtencoördinator (general) |
| `klachten-coordinator-ggd` | `ROLE_KLACHTEN_KLACHTENCOORDINATOR_GGD` | Klachtencoördinator GGD |
| `klachten-coordinator-vth` | `ROLE_KLACHTEN_KLACHTENCOORDINATOR_VTH` | Klachtencoördinator VTH |

Generic accounts: `admin` / `admin`, `developer` / `developer` and `user` / `user`.

## How it fits together

```
GZAC frontend ──> GZAC backend ──AuthZEN──> OpenFTV PDP <──bundle── OpenFTV manager <── management UI
                       │
                       └──> Open Zaak, Objecten, Objecttypen, Open Notificaties, Keycloak
```

- The GZAC backend (`gzac/`) is built from the `valtimo` submodule as a Gradle composite build. Its `authorization-authzen` module sends access checks to the PDP.
- The OpenFTV images are built from the `open-ftv` submodule. The manager seeds the Rego policies and publishes them to the PDP as a bundle.

Where the seed data lives:

| Path | Contents |
|---|---|
| `gzac/src/main/resources/config/` | Case definition, BPMN, forms, plugin configurations and permissions. GZAC deploys them on startup. |
| `docker/gzac-imports/` | Keycloak realm with users, and the Open Zaak, Objecten, Objecttypen and Open Notificaties database seeds |
| `docker/gzac-imports/gzac/choice-fields.sql` | GZAC choice fields (diensten, autorisatiegroepen, sectoren/afdelingen, producten, thema's, oordeel, behoorlijkheidsnormen) |
| `docker/openftv-imports/manager/policies/` | Rego policies, one per role (`klachten.*.rego`), plus `valtimo.rego` |
| `docker/openftv-imports/keycloak/` | OpenFTV Keycloak realm |

## Klachten walkthrough

`scripts/klachten-walkthrough.py` walks the klachten process end to end through the GZAC API, as the demo user that owns each task. Use it to check that the process still works after a change. It needs only `python3` and the running stack.

```bash
scripts/klachten-walkthrough.py                                   # all routes, dienst SZW
scripts/klachten-walkthrough.py --route informeel-behandelaar --dienst OCW --autorisatiegroep JGZ
scripts/klachten-walkthrough.py --route informeel-coordinator --zaakbehandelaar MIJZELF --terugkoppeling on
```

| Route | Flow |
|---|---|
| `informeel-coordinator` | The coordinator handles the complaint informally |
| `informeel-behandelaar` | The behandelaar of the dienst handles it, the coordinator checks it |
| `formeel` | The melder disagrees with the informal solution, so it is handled formally |
| `commissie` | The coordinator hands the complaint over to the klachtencommissie |

For each step the script prints ✅ or ❌. At the end it checks the zaak status and resultaat in Open Zaak, the internal case status, Operaton incidents, and ERROR lines in the backend log. It exits with 1 on any failure. Add `--verbose` to see the submitted form data.

## Known limitations

- **Seeds load only into an empty database.** The OpenFTV manager seeds policies only when its store is empty. Keycloak imports the realm only when it doesn't exist yet. Run `./run.sh --reset` after pulling changes to policies, the realm or other seed data.
- **Policy changes made in the OpenFTV UI are lost** on `--down` or `--reset`. Nothing persists between resets.
- **Fixed ports.** The stack publishes many host ports: 80, 3000, 5005, 5010, 5400, 5433, 5672–5673, 6379, 8001–8002, 8010–8012, 8080–8081, 8088, 8100, 8180, 8443, 8480, 9000, 9100, 9104, 9200, 15672–15673, 54319–54329. Stop anything else that uses them first.
- **The first build is slow** (about 8 minutes), because it compiles Valtimo.
- `scripts/permissions-to-rego.py` was a one-time aid to convert Valtimo permission files into the initial Rego policies. The Rego files in git are the source of truth.

## Troubleshooting

- **Port already allocated:** another process uses one of the ports above. Stop it, or change the host port in `docker/docker-compose.yaml`.
- **The backend doesn't start:** follow its logs with `docker compose -f docker/docker-compose.yaml --profile gzac logs -f gzac-backend`.
- **A new user or policy is missing:** run `./run.sh --reset`.
- **Submodule error from `run.sh`:** run `git submodule update --init`.
