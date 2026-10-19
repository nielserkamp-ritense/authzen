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
| `./run.sh --reload-policies` | Reload the OpenFTV policies from `docker/openftv-imports/manager/policies`. Only the OpenFTV database and manager are recreated, so GZAC data is kept. The PDP picks up the policies within about 30 seconds. |
| `./run.sh --help` | Show usage. |

Use `--reset` after pulling changes to seed data or the Keycloak realm. For OpenFTV policies, `--reload-policies` is enough (see [Known limitations](#known-limitations)).

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

## Roles and rights

Every klachten decision comes from the role's policy in `docker/openftv-imports/manager/policies/klachten.*.rego`. A role's scope is the set of complaints it may act on, based on the dienst (and for OCW the autorisatiegroep) the complaint is assigned to:

| Role | Case list | Open, notes, zaak documents | Tasks, user actions, add notes and documents |
|---|---|---|---|
| KCC | All complaints | All complaints | Nothing |
| IB/Post | Unassigned complaints | All complaints | Unassigned complaints |
| Coordinator (general) | All except GGD and VTH, incl. unassigned | Same | Same |
| Coordinator GGD / VTH | GGD / VTH, plus unassigned | Same | Same |
| Behandelaar BSD, DBV, DPZ, DSB, DSO, SZW | Own dienst | Same | Same |
| Behandelaar OCW | OCW without autorisatiegroep or with ALGEMEEN | Same | Same |
| Behandelaar OCW-JGZ / OCW-JH | OCW with their own autorisatiegroep | Same | Same |

- A user sees, claims and completes a task only when the complaint is in their scope **and** the task is meant for their role (candidate group). The general coordinator sees every task of the complaints in their scope.
- The klachten zaaktype and the dienst are checked together, so a document of the right dienst on another case definition or zaaktype is not visible.
- Outside the scope, a direct URL (complaint, task, notes, zaak documents, user action) returns 403 or 404.
- `scripts/klachten-authz-check.py` checks this whole table (see [Authorization check](#authorization-check)).

### Policies

All policies are in `docker/openftv-imports/manager/policies/`, in one Rego package (`authz`). The manager loads each file as a separate policy, with the tags from its `.meta` file.

| File | Contents |
|---|---|
| `klachten.*.rego` | One per klachten role. It only states the role's scope: its kind of rights and which complaints it handles |
| `klachten.rego` | The rights per kind of klachten role, and the rules that turn every scope into permissions |
| `valtimo.rego` | Generic rights for `ROLE_ADMIN` and `ROLE_USER`, as a table of permissions |
| `authz.rego` | Shared helpers, resource types, and the response GZAC reads (`allow` and `context.filter`) |

A klachten role file looks like this:

```rego
# Klachtenbehandelaar SZW: handles the complaints assigned to dienst SZW.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_SZW"] := {
	"rights": "behandelaar",
	"diensten": ["SZW"],
}
```

A scope can also have `"diensten": "all"`, `"unassigned": true` (complaints not assigned to a dienst yet), and for OCW `"autorisatiegroepen"` or `"except_autorisatiegroepen"`. The kinds of rights are `behandelaar`, `coordinator`, `hoofdcoordinator`, `meelezen` (KCC) and `registratie` (IB/Post); see `klachten.rego`.

After changing a policy file, check it and load it:

```bash
docker run --rm -v "$PWD/docker/openftv-imports/manager/policies":/p:ro openpolicyagent/opa:latest check /p --ignore '*.meta' --ignore cedar
./run.sh --reload-policies
```

`scripts/policy-filter-dump.py` shows what the PDP decides per role. Use `--out before.json` before a change and `--compare before.json` after it, to see exactly which permissions changed.

## How it fits together

```
GZAC frontend ──> GZAC backend ──AuthZEN──> OpenFTV PDP <──bundle── OpenFTV manager <── management UI
                       │
                       └──> Open Zaak, Objecten, Objecttypen, Open Notificaties, Keycloak
```

- The GZAC backend (`gzac/`) is built from the `valtimo` submodule as a Gradle composite build. Its `authorization-authzen` module sends access checks to the PDP.
- The OpenFTV images are built from the `open-ftv` submodule. The manager seeds the Rego policies and publishes them to the PDP as a bundle: automatically about 15 seconds after a fresh start, and after that every time someone clicks "Publiceren" in the management UI.

Where the seed data lives:

| Path | Contents |
|---|---|
| `gzac/src/main/resources/config/` | Case definition, BPMN, forms, plugin configurations and permissions. GZAC deploys them on startup. |
| `docker/gzac-imports/` | Keycloak realm with users, and the Open Zaak, Objecten, Objecttypen and Open Notificaties database seeds |
| `docker/gzac-imports/gzac/choice-fields.sql` | GZAC choice fields (diensten, autorisatiegroepen, sectoren/afdelingen, producten, thema's, oordeel, behoorlijkheidsnormen) |
| `docker/openftv-imports/manager/policies/` | Rego policies, see [Policies](#policies) |
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
scripts/klachten-authz-check.py                                   # all users, all checks (about 5 minutes)
scripts/klachten-authz-check.py --user klachten-behandelaar-szw --check open --check task-list
```

Every run seeds 14 fresh complaints: one unassigned, one for OCW before the verkenning, one per dienst and OCW group, and one OCW-JGZ complaint that was moved to SZW afterwards. Each stops at an open task and has a note. Only these seeds are judged. For each user × seed it checks:
- `list`, `open`: the case list and the complaint by id (direct URL);
- `notes`, `files`, `zaak`, `widgets`: notes, zaak documents, the zaak and the data of a summary widget;
- `task-list`, `task-open`, `claim`: the open task (a claim is undone right away);
- `action`: the start form of a user action;
- `note-create`: adding a note;
- `file-upload`, `file-modify`: uploading a zaak document from the documents tab, and changing a document's title.

It prints a grid per user and every difference with the expected result. It also checks that every allowed upload was stored on the zaak, and it reports the known upstream bypasses (see below) without counting them. It exits with 1 when anything is wrong. The seeds, their notes and the uploaded files stay in the database.

After a live policy change, tell the check what to expect instead:

| Option | Effect |
|---|---|
| `--grant USER=SCOPE` | `USER` also has the complaints of seed scope `SCOPE` (e.g. `klachten-behandelaar-szw=DSO`). Tasks still follow the candidate group, so SZW is not expected to see DSO's tasks |
| `--revoke USER` | `USER` has no complaints at all |

## Live policy change

The demo moment: change a role's rights in the OpenFTV manager and show the effect in GZAC, without a release or a restart. A change is active about a second after "Publiceren"; there is no cache in GZAC or the PDP.

**Grant: SZW also handles DSO complaints**

1. In GZAC (http://localhost), log in as `klachten-behandelaar-szw`. Show the case list: only SZW complaints. Open a DSO complaint URL: no access.
2. In the OpenFTV management UI (http://localhost:8180), log in as `admin-user` / `password`.
3. Open the policy `klachten.eerstlijnsklachten.klachtenbehandelaar-szw`. It only says which complaints SZW handles:
   ```rego
   klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_SZW"] := {
   	"rights": "behandelaar",
   	"diensten": ["SZW"],
   }
   ```
4. Click "Bewerken", change the line to `"diensten": ["SZW", "DSO"],` and click "Opslaan". Nothing changes in GZAC yet.
5. Go to "Publicaties" and click "Publiceren". Wait until the publication is finished (a second or two).
6. Refresh GZAC: the case list now also has the DSO complaints, and SZW can open them, read and add notes and zaak documents, and start user actions. The DSO tasks stay with the DSO behandelaar: a task also has to be meant for the role (candidate group). That is a separate rule.

**Revoke: KCC no longer reads complaints**

1. Log in to GZAC as `klachten-kcc`: every complaint is visible, read only.
2. In the manager, edit `klachten.eerstlijnsklachten.medewerker-kcc`: change `"diensten": "all",` to `"diensten": [],`. Opslaan, then Publiceren.
3. Refresh GZAC: the case list is empty, and opening a complaint is denied.

**Prove it and undo it**

```bash
scripts/klachten-authz-check.py --user klachten-behandelaar-szw --grant klachten-behandelaar-szw=DSO
scripts/klachten-authz-check.py --user klachten-kcc --revoke klachten-kcc
```

To undo, edit the lines back and publish again, or run `./run.sh --reload-policies` to reset every policy to the files in git (about 30 seconds). The "Versies" panel in the manager is empty, so it can't be used to undo.

**Be careful with typos.** The manager doesn't check Rego. A policy that doesn't compile is still published as "Finished successfully", and neither the manager nor the PDP logs an error. The PDP then has only part of the policies, so most klachten users suddenly see nothing. Fix the edit and publish again, or run `./run.sh --reload-policies`. Check a policy file before you load it with `opa check` (see [Policies](#policies)).

## Known limitations

- **Seeds load only into an empty database.** The OpenFTV manager seeds policies only when its store is empty. Keycloak imports the realm only when it doesn't exist yet. Run `./run.sh --reset` after pulling changes to the realm or other seed data, or `./run.sh --reload-policies` after changes to policies only.
- **Policy changes made in the OpenFTV UI are lost** on `--down`, `--reset` or `--reload-policies`. Nothing persists between resets.
- **Fixed ports.** The stack publishes many host ports: 80, 3000, 5005, 5010, 5400, 5433, 5672–5673, 6379, 8001–8002, 8010–8012, 8080–8081, 8088, 8100, 8180, 8443, 8480, 9000, 9100, 9104, 9200, 15672–15673, 54319–54329. Stop anything else that uses them first.
- **The first build is slow** (about 8 minutes), because it compiles Valtimo.
- **Klachten process stubs.** Email, notifications, the ontvangstbevestiging and the KTO data delivery are `${true}` stubs. Nothing is sent.
- **The terugkoppeling letter is a fixed dummy HTML document.** It is stored in the Documenten API as "Bericht", without a file name or format.
- **"Mijzelf" assigns a fixed user.** When a coordinator assigns the complaint to "Mijzelf", the case always goes to `klachten-coordinator`, also for GGD and VTH.
- **Herbeoordelen keeps the earlier answers.** "Terugzetten naar eerste beoordeling" restarts the beoordeling, but doesn't clear the verkenning, informal or formal answers.
- **The dienst email isn't updated after "dienst aanpassen"** in the eerste beoordeling. Only the stubbed notifications use it.
- **Log noise.** After every subprocess, Valtimo's SSE `TaskUpdateListener` logs `ERROR … Process instance not found`. An open GZAC browser tab also causes `AsyncRequestNotUsableException … disconnected client` errors. Both are harmless, and the walkthrough reports them as known noise.
- **The GZAC database dump contains 2 old klachten cases** from 2026-09-23. They have dummy choice values and open Operaton incidents, and they show up in the case list.
- **Temporary uploads are not scoped by complaint.** Every role except KCC may upload a temporary file (`ResourcePermission`), because a form upload happens before the file is linked to a complaint. Storing it as a zaak document is checked against the complaint (`ZgwDocument:create`).
- **Only eerstelijns klachten are covered.** The klachten policies have no rules for tweedelijns klachten and interventieverzoeken, because those processes are not deployed.
- **Upstream endpoints that skip authorization.** Valtimo serves some endpoints without checking the case, so no policy can close them. A logged-in user who knows a process instance ID can read its variables (`POST /api/v1/process-instance/{id}/variables`) and its state, history and BPMN (`GET /api/v1/process/{id}`, `/history`, `/activities`, `/xml`). The authorization check reports them. The tab list and the case's process links are readable too, but they are configuration only.
- **A denied form submission returns 400, not 403.** Valtimo's form-submission handler turns the `AccessDeniedException` into a generic 400 with a reference ID. Nothing is started.
- **`ROLE_USER` still grants generic access.** Every demo user also has `ROLE_USER` (`valtimo.rego`). For klachten users that gives the user list, object-management configuration and the user dashboard, but no klachten data. Widget data on a klachten case is excluded there and granted per klachten role instead.
- **The Valtimo permission files in `gzac/src/main/resources/config/global/permission/` are not used for decisions.** GZAC still imports them, but with AuthZEN on, every decision comes from the OpenFTV policies.
- **If the PDP is unreachable, everything is denied**, also for admin. Each request waits for the PDP timeout first (about 3 seconds).

## Troubleshooting

- **Port already allocated:** another process uses one of the ports above. Stop it, or change the host port in `docker/docker-compose.yaml`.
- **The backend doesn't start:** follow its logs with `docker compose -f docker/docker-compose.yaml --profile gzac logs -f gzac-backend`.
- **A new user is missing:** run `./run.sh --reset`. **A policy change has no effect:** run `./run.sh --reload-policies` and wait about 30 seconds.
- **Submodule error from `run.sh`:** run `git submodule update --init`.
