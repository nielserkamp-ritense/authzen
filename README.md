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
| `klachten-kcc` | `ROLE_KLACHTEN_KCC` | Medewerker KCC: views complaints (read-only) |
| `klachten-ibpost` | `ROLE_KLACHTEN_IB_POST` | Medewerker IB/Post: registers complaints and assigns them to a dienst |
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

| Option | Effect |
|---|---|
| `--dienst SZW\|OCW\|DPZ\|DSB\|DSO\|DBV\|BSD\|GGD\|VTH` | Dienst the complaint is assigned to (default SZW) |
| `--autorisatiegroep ALG\|JGZ\|JH` | For OCW: the autorisatiegroep chosen at verkenning (default: the first one, OCW algemeen) |
| `--zaakbehandelaar MIJZELF\|ANDERE_KLACHTENCOORDINATOR` | informeel-coordinator: who handles the complaint |
| `--terugkoppeling on` | Send a terugkoppeling to the melder, which stores a dummy letter on the zaak |
| `--post` | The melder wants communication by post (adds the "afdrukken brief" task) |
| `--melder-akkoord JA\|NEE\|ONBEKEND` | Whether the melder agrees with the informal solution. NEE continues formally |
| `--oordeel GEGROND\|DEELS_GEGROND\|ONGEGROND\|GEEN_OORDEEL` | Oordeel in the onderzoek. (Deels) gegrond also fills 3 dienstverleningsprincipes |
| `--oordeel-overnemen` | formeel: take the informal oordeel over, which skips hoor en wederhoor |
| `--terugkoppeling-afkeuren` | informeel-behandelaar: the coordinator rejects the behandelaar's terugkoppeling once |
| `--commissie-stoppen` | commissie: stop it with "Terug naar hoofdproces". Informeel restarts and closes the case |

For each step the script prints ✅ or ❌. At the end it checks the zaak status and resultaat in Open Zaak, the internal case status, Operaton incidents, and ERROR lines in the backend log. It exits with 1 on any failure. Add `--verbose` to see the submitted form data.

The walkthrough submits the document paths the schema expects, so it can't catch a form field whose key doesn't match the schema. `scripts/check-forms-schema.py` checks that statically, without the stack:

```bash
scripts/check-forms-schema.py
```

It lists every submitted form field that isn't in the document definition (with `additionalProperties: false`, such a field makes the form submission fail), and every conditional that points at a missing field. It exits with 1 when it finds anything. Run it after changing a form or the document definition.

## Authorization check

`scripts/klachten-authz-check.py` checks, for every demo user, what they can see and do on the klachten, against the expected role × dienst matrix in the script (`EXPECTED`). Everything goes through the GZAC API, so every answer comes from the OpenFTV policies.

```bash
scripts/klachten-authz-check.py                                   # all users, all checks (about 3 minutes)
scripts/klachten-authz-check.py --user klachten-behandelaar-szw --check open --check task-list
```

Every run seeds 13 fresh complaints: one unassigned, one for OCW before the verkenning, and one per dienst and OCW group. Each stops at an open task and has a note. Only these seeds are judged. For each user × seed it checks:
- `list`, `open`: the case list and the complaint by id (direct URL);
- `notes`, `files`, `zaak`: notes, zaak documents and the zaak;
- `task-list`, `task-open`, `claim`: the open task (a claim is undone right away);
- `action`: the start form of a user action;
- `note-create`: adding a note.

It prints a grid per user and every difference with the expected result, and exits with 1 when there is any. The seeds and their notes stay in the database.

## Known limitations

- **Seeds load only into an empty database.** The OpenFTV manager seeds policies only when its store is empty. Keycloak imports the realm only when it doesn't exist yet. Run `./run.sh --reset` after pulling changes to policies, the realm or other seed data.
- **Policy changes made in the OpenFTV UI are lost** on `--down` or `--reset`. Nothing persists between resets.
- **Fixed ports.** The stack publishes many host ports: 80, 3000, 5005, 5010, 5400, 5433, 5672–5673, 6379, 8001–8002, 8010–8012, 8080–8081, 8088, 8100, 8180, 8443, 8480, 9000, 9100, 9104, 9200, 15672–15673, 54319–54329. Stop anything else that uses them first.
- **The first build is slow** (about 8 minutes), because it compiles Valtimo.
- **Klachten process stubs.** Email, notifications, the ontvangstbevestiging and the KTO data delivery are `${true}` stubs. Nothing is sent.
- **The terugkoppeling letter is a fixed dummy HTML document.** It is stored in the Documenten API as "Bericht", without a file name or format.
- **"Mijzelf" assigns a fixed user.** When a coordinator assigns the complaint to "Mijzelf", the case always goes to `klachten-coordinator`, also for GGD and VTH.
- **Herbeoordelen keeps the earlier answers.** "Terugzetten naar eerste beoordeling" restarts the beoordeling, but doesn't clear the verkenning, informal or formal answers.
- **The dienst email isn't updated after "dienst aanpassen"** in the eerste beoordeling. Only the stubbed notifications use it.
- **Log noise.** After every subprocess, Valtimo's SSE `TaskUpdateListener` logs `ERROR … Process instance not found`. An open GZAC browser tab also causes `AsyncRequestNotUsableException … disconnected client` errors. Both are harmless, and the walkthrough reports them as known noise.
- **The GZAC database dump contains 2 old klachten cases** from 2026-09-23. They have dummy choice values and open Operaton incidents, and they show up in the case list.
- `scripts/permissions-to-rego.py` was a one-time aid to convert Valtimo permission files into the initial Rego policies. The Rego files in git are the source of truth.

## Troubleshooting

- **Port already allocated:** another process uses one of the ports above. Stop it, or change the host port in `docker/docker-compose.yaml`.
- **The backend doesn't start:** follow its logs with `docker compose -f docker/docker-compose.yaml --profile gzac logs -f gzac-backend`.
- **A new user or policy is missing:** run `./run.sh --reset`.
- **Submodule error from `run.sh`:** run `git submodule update --init`.
