# AuthZEN + GZAC proof of concept

A local demo of GZAC (Valtimo) with fully externalized authorization. GZAC asks an [OpenFTV](https://gitlab.com/digilab.overheid.nl/ecosystem/ftv/open-ftv) policy decision point (PDP) through the [AuthZEN](https://openid.net/wg/authzen/) API instead of using its built-in permissions. The demo has three processes, each with its own policy: two zaak-based ones, the klachten (complaints) process of Gemeente Den Haag with one role per afdeling and a bezwaar process with a behandelaar and a juridisch adviseur, and a ToDo without a zaak, where access follows the user's relation to the ToDo (creator or assignee) instead of a role.

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

**Giving the demo:** follow the 10-minute script in [`docs/demo-script.md`](docs/demo-script.md) (Dutch). `scripts/demo-prepare.sh` resets the stack, seeds the demo cases and checks that every user sees what the script says; `scripts/demo-seed.py --check` repeats the check just before presenting.

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
| OpenFTV management UI | http://localhost:8180 | `author-user` (edit and publish policies), `admin-user` (settings only), `auditor-user` (read only) / `password` |
| OpenFTV Keycloak | http://localhost:8088 | `admin` / `admin` |
| OpenFTV manager API | http://localhost:9000 | no token needed; policy ids are UUIDs, the file name is in `metadata.title` |
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
| `bezwaar-behandelaar` | `ROLE_BEZWAAR_BEHANDELAAR` | Bezwaarbehandelaar: creates and handles bezwaren |
| `bezwaar-adviseur` | `ROLE_BEZWAAR_ADVISEUR` | Juridisch adviseur: reads bezwaren, adds notes and documents |
| `todo-anna` | `ROLE_USER` only | ToDo demo user |
| `todo-bram` | `ROLE_USER` only | ToDo demo user |

Generic accounts: `admin` / `admin`, `developer` / `developer` and `user` / `user`.

## Roles and rights

Klachten and bezwaar roles don't see each other's cases. `ROLE_USER`, which every demo user has, gives generic things such as the dashboard, the user list and tasks of the user's own group or team (`valtimo.rego`), and the ToDo rights (`todo.rego`), but no rights on a klachten or bezwaar case.

### Klachten

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

### Bezwaar

Every bezwaar decision comes from `bezwaar.rego` and the role files `bezwaar.*.rego`. Both roles see every bezwaar. Once a bezwaar is closed with "Afsluiten bezwaar", its internal status is `afgerond` and it is read only for everyone:

| | Behandelaar | Adviseur | Afgerond (both) |
|---|---|---|---|
| Case list, open, notes, zaak documents, widgets | ✓ | ✓ | ✓ |
| Add notes and zaak documents | ✓ | ✓ | – |
| Create a bezwaar | ✓ | – | – |
| Claim, assign and edit the bezwaar | ✓ | – | – |
| Tasks (see / claim and complete) | ✓ / ✓ | – | see only |
| User actions | its `acties`: Wijzigen aanvraaggegevens, Zaak bijwerken, Afsluiten bezwaar | its `acties`: none | – |

`scripts/bezwaar-authz-check.py` checks this table (see [Bezwaar walkthrough and check](#bezwaar-walkthrough-and-check)).

### ToDo

Every ToDo decision comes from `todo.rego`, for `ROLE_USER`, so for every logged-in user. It doesn't look at a role or a zaak, but at the user's relation to the ToDo:

| The user is | Unassigned ToDo | Assigned to its creator | Assigned to someone else |
|---|---|---|---|
| Its creator | sees and changes it | sees and changes it | sees it (read only) |
| Its assignee | – | (the creator) | sees and changes it |
| Anyone else | nothing | nothing | nothing |

- "Changes" covers editing it, adding notes, claiming and completing its tasks, and assigning or unassigning it. Anyone may create a ToDo.
- The tasks have no candidate group: who may do them follows from the ToDo.
- Admin sees every ToDo through its generic rights.
- `scripts/todo-authz-check.py` checks this table (see [ToDo walkthrough and check](#todo-walkthrough-and-check)).

### Policies

All policies are in `docker/openftv-imports/manager/policies/`, in one Rego package (`authz`). The manager loads each file as a separate policy, with the tags from its `.meta` file.

| File | Contents |
|---|---|
| `klachten.*.rego` | One per klachten role. It only states the role's scope: its kind of rights and which complaints it handles |
| `klachten.rego` | The rights per kind of klachten role, and the rules that turn every scope into permissions |
| `bezwaar.*.rego` | One per bezwaar role: its kind of rights and the user actions (`acties`) it may start |
| `bezwaar.rego` | The rights per kind of bezwaar role, the afgerond rule, and the rules that turn every scope into permissions |
| `todo.rego` | The ToDo rights of `ROLE_USER`, as a table of permissions on the creator and assignee |
| `valtimo.rego` | Rights for `ROLE_ADMIN` (everything), and the generic non-case rights of `ROLE_USER`, as a table of permissions |
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

A bezwaar role file names its kind of rights (`behandelaar` or `adviseur`, see `bezwaar.rego`) and, by process key, the user actions it may start on a bezwaar that is not afgerond:

```rego
# Bezwaarbehandelaar: creates and handles bezwaren, does their tasks and starts their user actions.
bezwaar_scopes["ROLE_BEZWAAR_BEHANDELAAR"] := {
	"rights": "behandelaar",
	"acties": ["change-name", "patch-zaak", "afsluiten-bezwaar"],
}
```

`todo.rego` compares the ToDo with the current user. GZAC stores the creator's **email** in `createdBy` and the assignee's **username** in `assigneeId`, so the conditions use the placeholders `${currentUserEmail}` and `${currentUsername}`:

```rego
creator := field("createdBy", "==", "${currentUserEmail}")
assignee := field("assigneeId", "==", "${currentUsername}")
unassigned := field("assigneeId", "==", null)

viewer := [[is_todo, creator], [is_todo, assignee]]                  # each list is one permission (AND);
editor := [[is_todo, creator, unassigned], [is_todo, assignee]]      # the permissions together are OR
```

The klachten files are tagged `klachten`, the bezwaar files `bezwaar`, `todo.rego` `todo`, and `valtimo.rego` `valtimo`. The PDP bundle (`docker/openftv-imports/manager/bundles/pdp1.yaml`) takes all four tags.

After changing a policy file, check it and load it:

```bash
scripts/policy-check.py        # opa check with the PDP's OPA version, in docker
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

### OpenFTV version

The demo runs on OpenFTV **v0.5.2** (release of 2026-10-09). The `open-ftv` submodule points to that release tag in the upstream repository [gitlab.com/digilab.overheid.nl/ecosystem/ftv/open-ftv](https://gitlab.com/digilab.overheid.nl/ecosystem/ftv/open-ftv), without changes. The release notes are in the annotated tags.

To move to a newer release:

1. In `open-ftv`: `git fetch --tags` and `git checkout <tag>` (e.g. `v0.6.0`).
2. In this repo: `git add open-ftv` to point the submodule at it.
3. Compare the `openftv-*` env in `docker/docker-compose.yaml` with the flags in `open-ftv/apps/{pdp,manager,management-interface}/config/config.go`. Each flag `x-y` is read from `PDP_X_Y` or `MANAGER_X_Y`, and an env var without a flag is ignored without a warning.
4. Set `OPA_IMAGE` in `scripts/policy-check.py` to the `open-policy-agent/opa` version in `open-ftv/go.mod`.
5. Check it: `./run.sh --reset -d`, `scripts/policy-check.py`, `scripts/policy-filter-dump.py --compare` against a dump from before the update, `scripts/klachten-authz-check.py`, `scripts/klachten-walkthrough.py`, `scripts/bezwaar-authz-check.py`, `scripts/bezwaar-walkthrough.py`, `scripts/todo-authz-check.py`, `scripts/todo-walkthrough.py`, and the [live policy change](#live-policy-change).

### Logs and decisions

- **PDP log:** `docker logs authzen_openftv_pdp` shows warnings and errors only (`PDP_LOG_LEVEL: warn`). At `info` the PDP logs every single decision.
- **Manager log:** `docker logs authzen_openftv_manager` (JSON). It shows the seeding and every publication ("bundle-runner").
- **Decision log:** the PDP stores every request it answers, in the OpenFTV database `openftv_adl` (table `decision`, the full request in `body`). The management UI shows it under "Logboek". It is emptied by `--reload-policies` and `--reset`.

Where the seed data lives:

| Path | Contents |
|---|---|
| `gzac/src/main/resources/config/` | The case definitions `eerstelijns-klachten`, `bezwaar` (both with a zaaktype link) and `todo` (without), with their BPMN, forms and tabs, plus plugin configurations and roles. GZAC deploys them on startup. |
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

## Bezwaar walkthrough and check

The bezwaar case (`gzac/src/main/resources/config/case/bezwaar/`) runs on the bezwaar zaaktype "bezwaar-behandelen" in Open Zaak:

1. `bezwaar-behandelaar` starts a bezwaar with the start form. Internal status "Aanvraag ontvangen".
2. Task "Valideer gegevens aanvrager", then status "In behandeling".
3. Task "In behandeling", then status "Informatieverzoek uitgezet".
4. User actions on the bezwaar: "Wijzigen aanvraaggegevens" (a task to edit the bezwaar), "Zaak bijwerken" (the zaak in Open Zaak), and "Afsluiten bezwaar": choose a resultaat (Gegrond, Afgewezen or Ingetrokken), which sets the zaak resultaat, the end status "Zaak afgerond", and the internal status "Afgerond".

`scripts/bezwaar-walkthrough.py` walks this as `bezwaar-behandelaar` and checks the end state (internal status, zaak status and resultaat, incidents, ERROR lines in the backend log):

```bash
scripts/bezwaar-walkthrough.py                         # closes with resultaat Gegrond
scripts/bezwaar-walkthrough.py --resultaat Ingetrokken
```

`scripts/bezwaar-authz-check.py` checks the [bezwaar matrix](#bezwaar) for both bezwaar users, three klachten users and `user` (about 1.5 minutes). Every run seeds two bezwaren with a note and a zaak document: `open`, at its first task, and `afgerond`, closed straight away. For each user × seed it checks the list, open, notes, files, widgets, the task (list, open, claim), the user actions, the "Afsluiten bezwaar" start form, adding a note, uploading a zaak document, and (once) creating a bezwaar.

```bash
scripts/bezwaar-authz-check.py
scripts/bezwaar-authz-check.py --user bezwaar-adviseur --check actions --verbose
```

After a live policy change, `--grant USER=CHECK[,CHECK]` expects those checks to be allowed on the open bezwaar, e.g. `--grant bezwaar-adviseur=actions,afsluiten`.

## ToDo walkthrough and check

The ToDo case (`gzac/src/main/resources/config/case/todo/`) has no zaak, so it has no documents tab. Its process:

1. Anyone creates a ToDo with the start form (titel, omschrijving, deadline). Status "Open".
2. Task "Oppakken", then status "In behandeling".
3. Task "Afronden", then status "Afgerond".

The creator can assign the ToDo to a colleague in the case header. The open task then moves to that colleague.

`scripts/todo-walkthrough.py` walks this through the GZAC API: `todo-anna` creates a ToDo and picks it up, assigns it to `todo-bram`, and bram completes it. It checks along the way that bram doesn't see it before it is assigned to him, and that anna can still read it but no longer change it. At the end it checks the status, that there is no zaak, Operaton incidents, and ERROR lines in the backend log.

```bash
scripts/todo-walkthrough.py
scripts/todo-walkthrough.py --seed      # leave three demo ToDos for a walkthrough in the UI
```

`--seed` leaves "Boodschappen bestellen" (anna's, unassigned), "Rapport nalezen" (anna's, assigned to bram) and "Presentatie voorbereiden" (bram's). Run it after a fresh `./run.sh --reset`, so the lists only show these.

`scripts/todo-authz-check.py` checks the [ToDo table](#todo) for `todo-anna`, `todo-bram`, `user` and `klachten-kcc` (about 10 seconds). Every run seeds three ToDos by anna, each with a note: `unassigned`, `self-assigned` (to anna) and `assigned` (to bram). For each user × seed it checks the list, open, notes, the widget, the open task (list, open, claim), adding a note, assigning the ToDo to themselves, and (once) creating a ToDo. Claims and assignments that succeed are undone right away.

```bash
scripts/todo-authz-check.py
scripts/todo-authz-check.py --user todo-anna --verbose
```

After a live policy change, `--grant USER=SEED:CHECK[,CHECK]` expects those checks to be allowed, e.g. `--grant todo-anna=assigned:note-create,claim,assign`.

## Live policy change

The demo moment: change a role's rights in the OpenFTV manager and show the effect in GZAC, without a release or a restart. A change is active about a second after "Publiceren"; there is no cache in GZAC or the PDP.

**Grant: SZW also handles DSO complaints**

1. In GZAC (http://localhost), log in as `klachten-behandelaar-szw`. Show the case list: only SZW complaints. Open a DSO complaint URL: no access.
2. In the OpenFTV management UI (http://localhost:8180), log in as `author-user` / `password`. Only the author role can edit and publish policies; `admin-user` sees them read only.
3. Open the policy `klachten.eerstlijnsklachten.klachtenbehandelaar-szw`. It only says which complaints SZW handles:
   ```rego
   klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_SZW"] := {
   	"rights": "behandelaar",
   	"diensten": ["SZW"],
   }
   ```
4. Click "Bewerken", change the line to `"diensten": ["SZW", "DSO"],` and click "Opslaan". Nothing changes in GZAC yet.
5. Check the edit: `scripts/policy-check.py --manager` must say `OK`. Then go to "Publicaties" and click "Publiceren". Wait until the publication is finished (a second or two).
6. Refresh GZAC: the case list now also has the DSO complaints, and SZW can open them, read and add notes and zaak documents, and start user actions. The DSO tasks stay with the DSO behandelaar: a task also has to be meant for the role (candidate group). That is a separate rule.

**Revoke: KCC no longer reads complaints**

1. Log in to GZAC as `klachten-kcc`: every complaint is visible, read only.
2. In the manager, edit `klachten.eerstlijnsklachten.medewerker-kcc`: change `"diensten": "all",` to `"diensten": [],`. Opslaan, then Publiceren.
3. Refresh GZAC: the case list is empty, and opening a complaint is denied.

**Grant: the juridisch adviseur may close a bezwaar**

1. Log in to GZAC as `bezwaar-adviseur` and open a bezwaar that is not afgerond: no user actions.
2. In the manager, edit `bezwaar.adviseur`: change `"acties": [],` to `"acties": ["afsluiten-bezwaar"],`. Opslaan, then Publiceren.
3. Refresh GZAC: the adviseur now has the user action "Afsluiten bezwaar", and only that one. On an afgerond bezwaar it still has nothing: the afgerond rule is separate.

**Grant: the creator keeps changing a ToDo after assigning it**

1. Run `scripts/todo-walkthrough.py --seed`. Log in to GZAC as `todo-anna` and open "Rapport nalezen", which she assigned to bram: she can read it, but not add a note or do its task.
2. In the manager, edit `todo`: change `editor := [[is_todo, creator, unassigned], [is_todo, assignee]]` to `editor := [[is_todo, creator], [is_todo, assignee]]`. Opslaan, then Publiceren.
3. Refresh GZAC: anna can change the ToDo again, although it is still assigned to bram.

**Prove it and undo it**

```bash
scripts/klachten-authz-check.py --user klachten-behandelaar-szw --grant klachten-behandelaar-szw=DSO
scripts/klachten-authz-check.py --user klachten-kcc --revoke klachten-kcc
scripts/bezwaar-authz-check.py --user bezwaar-adviseur --grant bezwaar-adviseur=actions,afsluiten
scripts/todo-authz-check.py --user todo-anna --grant todo-anna=assigned:note-create,claim,assign
```

To undo, edit the lines back and publish again, or run `./run.sh --reload-policies` to reset every policy to the files in git (about 30 seconds). The "Versies" panel in the manager can't be used to undo: it only records versions of policies with status "accepted" when they are published, and the UI has no way to set that status (only the API: `PATCH /v1/policy/{id}/status`).

**Be careful with typos.** The manager doesn't check Rego. A policy that doesn't compile is still published as "Finished successfully", and neither the manager nor the PDP logs an error. The PDP then drops the klachten and bezwaar rules, so every klachten and bezwaar user suddenly sees nothing (admin and `ROLE_USER` rights stay). Fix the edit and publish again, or run `./run.sh --reload-policies`. Check the policies with `scripts/policy-check.py --manager` before you publish (or `scripts/policy-check.py` for the files, see [Policies](#policies)).

## Known limitations

- **Changed seeds don't load on a restart.** The OpenFTV manager adds a seed policy file only when that policy doesn't exist yet. It doesn't update a policy it already has. Keycloak imports the realm only when it doesn't exist yet. Run `./run.sh --reset` after pulling changes to the realm or other seed data, or `./run.sh --reload-policies` after changes to policies only.
- **Policy changes made in the OpenFTV UI are lost** on `--down`, `--reset` or `--reload-policies`. Nothing persists between resets.
- **Fixed ports.** The stack publishes many host ports: 80, 3000, 5005, 5010, 5400, 5433, 5672–5673, 6379, 8001–8002, 8010–8012, 8080–8081, 8088, 8100, 8180, 8443, 8480, 9000, 9100, 9104, 9200, 15672–15673, 54319–54329. Stop anything else that uses them first.
- **The first build is slow** (about 8 minutes), because it compiles Valtimo.
- **Klachten process stubs.** Email, notifications, the ontvangstbevestiging and the KTO data delivery are `${true}` stubs. Nothing is sent.
- **The terugkoppeling letter is a fixed dummy HTML document.** It is stored in the Documenten API as "Bericht", without a file name or format.
- **"Mijzelf" assigns a fixed user.** When a coordinator assigns the complaint to "Mijzelf", the case always goes to `klachten-coordinator`, also for GGD and VTH.
- **Herbeoordelen keeps the earlier answers.** "Terugzetten naar eerste beoordeling" restarts the beoordeling, but doesn't clear the verkenning, informal or formal answers.
- **The dienst email isn't updated after "dienst aanpassen"** in the eerste beoordeling. Only the stubbed notifications use it.
- **Log noise.** After every subprocess, Valtimo's SSE `TaskUpdateListener` logs `ERROR … Process instance not found`. An open GZAC browser tab also causes `AsyncRequestNotUsableException … disconnected client` errors. The OpenFTV PDP logs `ERROR failed to parse body … application/octet-stream` on every publication, also when it succeeds. All are harmless. The walkthrough reports the two Valtimo errors as known noise.
- **The GZAC database dump contains 2 old klachten cases** from 2026-09-23. They have dummy choice values and open Operaton incidents, and they show up in the case list.
- **Temporary uploads are not scoped by complaint.** Every role except KCC may upload a temporary file (`ResourcePermission`), because a form upload happens before the file is linked to a complaint. Storing it as a zaak document is checked against the complaint (`ZgwDocument:create`).
- **Only eerstelijns klachten are covered.** The klachten policies have no rules for tweedelijns klachten and interventieverzoeken, because those processes are not deployed.
- **The bezwaar case is a trimmed copy of Valtimo's dev case `bezwaar`,** not the GZAC Exchange app `kim-bezwaar-en-beroep`, which can't be downloaded. Its test parts (FVM, UI components, portaaltaak, besluiten, tags) are left out, and its forms are rewritten with Dutch labels.
- **"Afsluiten bezwaar" is meant for the end of the bezwaar.** Started earlier, it leaves the open task of the main process behind, and nobody can complete it: an afgerond bezwaar is read only.
- **The afgerond rule only covers rights on an existing bezwaar.** GZAC can't check the status of a case that has none, so creating and reading a bezwaar don't look at the status. A bezwaar gets its first status when it is created.
- **The "Zaak bijwerken" form keeps the dev defaults** for geometry and betalingsindicatie, so they are sent to Open Zaak too.
- **Upstream endpoints that skip authorization.** Valtimo serves some endpoints without checking the case, so no policy can close them. A logged-in user who knows a process instance ID can read its variables (`POST /api/v1/process-instance/{id}/variables`) and its state, history and BPMN (`GET /api/v1/process/{id}`, `/history`, `/activities`, `/xml`). The authorization check reports them. The tab list and the case's process links are readable too, but they are configuration only.
- **A denied form submission returns 400, not 403.** Valtimo's form-submission handler turns the `AccessDeniedException` into a generic 400 with a reference ID. Nothing is started.
- **`ROLE_USER` still grants generic access.** Every demo user also has `ROLE_USER` (`valtimo.rego`). That gives the user list, object-management configuration, the user dashboard and tasks of the user's own group or team, but nothing on a klachten or bezwaar case: those rights come only from the klachten and bezwaar policies. The ToDo rights are also on `ROLE_USER` (`todo.rego`).
- **Admin sees every ToDo.** The ToDo rules are for `ROLE_USER`; admin keeps its generic rights on every case.
- **Unassigning a ToDo as its assignee shows an error, but it works.** Valtimo reloads the ToDo after the change with the user's own rights, which the user no longer has, and then answers 400. To hand a ToDo back without the error, assign it to its creator.
- **A refused assign or unassign returns 400, not 403**, like a refused form submission. Nothing changes.
- **Whether a user can be assigned a ToDo only depends on it being a ToDo.** Valtimo checks the user it is assigned to with that user's roles, but with the current user's placeholders, so a creator or assignee rule can't be used there.
- **The OpenFTV manager doesn't enforce its roles.** Only the management UI does: `author-user` edits and publishes, `admin-user` manages settings, `auditor-user` reads. The manager API lets any logged-in user, and calls without a token, change and publish policies. For example, `author-user` can publish although the manager's Cedar policy `publish_admin_only.cedar` allows only admin. The scripts rely on token-less access.
- **If the PDP is unreachable, everything is denied**, also for admin. Each request waits for the PDP timeout first (about 3 seconds).

## Troubleshooting

- **Port already allocated:** another process uses one of the ports above. Stop it, or change the host port in `docker/docker-compose.yaml`.
- **The backend doesn't start:** follow its logs with `docker compose -f docker/docker-compose.yaml --profile gzac logs -f gzac-backend`.
- **A new user is missing:** run `./run.sh --reset`. **A policy change has no effect:** run `./run.sh --reload-policies` and wait about 30 seconds.
- **Submodule error from `run.sh`:** run `git submodule update --init`.
