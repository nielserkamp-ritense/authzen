# Epic: Setup klachten process van Den Haag in demo omgeving

## Goal

Run the klachten process of Gemeente Den Haag on the local docker-compose demo (GZAC + OpenFTV + AuthZEN) so that its authorization is fully externalized. Authorization decisions come from OpenFTV policies (Rego) through AuthZEN and not from Valtimo's built-in permissions. The process is only the vehicle; the main message is that one role model per afdeling can be managed outside the application.

### Use case

A burger files a complaint. A **medewerker KCC** registers it. A **medewerker IB/Post** assigns it to the right afdeling. The **klachtenbehandelaar** of that afdeling (e.g. SZW) sees and handles only complaints for their own afdeling. They do not see complaints for OCW-JGZ, for example. A **klachtencoördinator** (general, GGD or VTH) has an overview of their own scope and can take over or escalate complaints.

During the demo, the presenter logs in as these roles one after another and shows:
- that the case lists, tasks and actions differ per role
- that a change to a policy in OpenFTV takes effect immediately in GZAC, with no redeploy

## Stakeholders

| Stakeholder | Interest | Involvement |
|---|---|---|
| Niels Erkamp (PoC owner) | Proves that AuthZEN/OpenFTV works with GZAC | **Final say**. Builds the demo, sets scope and priorities |
| Ritense product/development (GZAC/Valtimo) | Decides whether externalized authz goes into the product | Audience of the demo. Gives feedback on the integration approach |
| Ritense sales/consultancy | Has a convincing story to tell municipalities | Audience. Possible future presenters |
| Demo presenter (end-user) | A reliable, reproducible demo | Uses the setup. Needs a script and test accounts |
| Gemeente Den Haag (indirect) | Their process and role model are the source | Not directly involved. Their process definition is the basis |

## Business Requirements

1. BR1: The demo clearly shows the value of externalized authorization: central management, fine-grained control and changes without a release.
2. BR2: The demo uses a realistic, recognizable government process (klachten DH) with its real role model.
3. BR3: Every Ritense colleague can start the demo locally in a reproducible way, without help from the PoC owner.
4. BR4: The demo is reliable. No broken forms or wrong choice fields during a presentation.
5. BR5: The demo shows that the approach is generic. It also works for other processes, with and without a zaak.
6. BR6: The setup runs on a current OpenFTV version, so it stays representative.

## Functional Requirements

### Setup & environment
1. FR1: `run.sh` starts the full stack (GZAC, Open Zaak, Objecten, Keycloak, OpenFTV, authzen) from a clean checkout including submodules.
2. FR2: All seed data is loaded automatically on startup: zaaktypen, case definitions, BPMN, forms, Keycloak realm/users and OpenFTV policies.
3. FR3: The README documents prerequisites, startup, URLs, test accounts per role and known limitations.

### Klachten process
4. FR4: The DH klachten process (eerstlijnsklachten + klachtencoördinator) runs end to end without errors.
5. FR5: All choice fields (afdeling, type, etc.) are configured correctly and drive routing and authorization.

### Authorization
6. FR6: Each role has a Keycloak demo user and its own policy in OpenFTV:
   - medewerker KCC
   - medewerker IB/Post
   - klachtenbehandelaar per afdeling: BSD-bestuursdienst, DBV, DPZ, DSB, DSO, OCW, OCW-JGZ, OCW-JH, SZW
   - klachtencoördinator: general, GGD and VTH
7. FR7: List and search results are filtered via the PDP. This covers combined filters: ZaakTypeFilter AND afdeling/type filters.
8. FR8: A negative decision (`false`) results in a blocking permission. No specification leaks access.
9. FR9: Policies are rewritten in idiomatic Rego/filters, which makes them readable as demo material.
10. FR10: A policy change in OpenFTV is visible in GZAC without restarting GZAC.

### Extensibility
11. FR11: OpenFTV (submodule + images) is updated to the latest version, and the policies and integration still work.
12. FR12: A ToDo process that is **not** linked to a zaak is protected by the same authz mechanism.
13. FR13: A bezwaar process (from GZAC Exchange) that **is** linked to a zaak is protected by the same authz mechanism.

## Features

### F1: Reproducible local demo environment
- **Goal:** Any colleague can start the demo with a single command.
- **Requirements:** BR3; FR1, FR2, FR3
- **Acceptance criteria:**
  - On a clean checkout with `git submodule update --init`, `./run.sh` starts all services without manual steps.
  - After startup, the DH klachten zaaktypen, case definitions, Keycloak users and OpenFTV policies are present.
  - The README lists all URLs, test accounts per role and startup instructions. Someone other than Niels can start the demo using only the README.

### F2: Working klachten process Den Haag
- **Goal:** The klachten process runs end to end, without errors, across all roles.
- **Requirements:** BR2, BR4; FR4, FR5
- **Acceptance criteria:**
  - A complaint can be registered, assigned to an afdeling, handled and closed.
  - All choice fields show the correct options, and the selected values are stored correctly in the document/zaak.
  - No errors show up in forms or in the process log while walking through the happy flow.

### F3: Role-based access per afdeling via OpenFTV
- **Goal:** Show that access to klachten is fully determined by externally managed policies.
- **Requirements:** BR1, BR2; FR6, FR7, FR8
- **Acceptance criteria:**
  - Each role in FR6 has a demo user, and each user only sees the cases and tasks that their policy allows.
  - A klachtenbehandelaar of afdeling X cannot see or open any complaint of afdeling Y, not even through a direct URL.
  - Combined filters (zaaktype AND afdeling) return the correct results.
  - A `false` decision blocks access. There is no fallback to Valtimo's default permissions.

### F4: Live policy change (demo moment)
- **Goal:** Show the core value: authorization changes without a release.
- **Requirements:** BR1; FR10, FR9
- **Acceptance criteria:**
  - Changing a policy in the OpenFTV manager (e.g. giving SZW access to DSO complaints) is visible in GZAC after a refresh.
  - Policies are written in idiomatic Rego and are understandable when shown on screen.

### F5: Up-to-date OpenFTV
- **Goal:** The demo runs on a current, representative OpenFTV version.
- **Requirements:** BR6; FR11
- **Acceptance criteria:**
  - The open-ftv submodule and images point to the latest release.
  - All F3/F4 acceptance criteria still pass after the update.

> F6 and F7 bring the demo to three processes in total: klachten (zaak-based), bezwaar (zaak-based) and ToDo (no zaak).

### F6: Bezwaar process (linked to a zaak)
- **Goal:** Show that the approach works for zaak-based processes other than klachten, with a different zaaktype.
- **Source:** GZAC Exchange app `kim-bezwaar-en-beroep` (release March 2025): https://exchange.gzac.nl/item/r57E3n8QZg1Go9bK
- **Contents of the app:**
  - Case definition `kim-bezwaar-en-beroep`, with assignee support and no auto-assign.
  - Main process "Verwerken verzoek: Bezwaar en beroep". It initializes the document and is configured as **not** startable by the user in the original app. We change this for the demo.
  - User-startable actions: "Wijzig interne status", "Wijzigen aanvraaggegevens" and "Afsluiten zaak".
  - Generic ZGW subprocesses: "Update zaakstatus" and "Afsluiten zaak". They use the plugin actions `get-statustype`, `set-zaakstatus`, `get-resultaattype` and `create-zaakresultaat`.
  - Internal case statuses: Nieuw, In behandeling, Afgerond, Heropend, Aanvullend behandelen.
  - Forms (start form, summary, actions), case tabs, widgets, search fields, case list and document upload fields.
  - **No** user tasks, **no** zaaktype/Open Zaak data and **no** roles or permissions.
- **Requirements:** BR5; FR13
- **Acceptance criteria:**
  - The bezwaar app is imported into `gzac` config and loads without errors on Valtimo (>13.32, which supports the app's config format).
  - A bezwaar zaaktype (with statustypen and resultaattypen) exists in the Open Zaak seed, and it is linked to the case definition.
  - The plugin configuration IDs in the process links are mapped to the demo's Zaken API/Catalogi API plugin configurations.
  - The main process "Verwerken verzoek" is made startable by the user (`startableByUser: true`). A demo user with the bezwaar role can create a bezwaar case from the GZAC UI using the start form.
  - A separate role (e.g. `bezwaar.behandelaar`) with a Keycloak demo user gets access to bezwaar. Valtimo permissions and an OpenFTV policy are written for this role, since the app provides none.
  - Existing klachten roles get **no** access to bezwaar (for now).
  - Access is determined by its own OpenFTV policy, and it differs per role.
  - The ZaakTypeFilter separates it correctly from klachten. Klachten users do not see bezwaren, and the bezwaar user does not see klachten.
  - The OpenFTV policy controls the user-startable actions. For example, the bezwaar role may run "Afsluiten zaak", and other roles may not.
  - Policies can use the internal case status. For example, an "Afgerond" bezwaar is read-only.

### F7: ToDo process (not linked to a zaak)
- **Goal:** Show that the approach also works for Valtimo cases without a zaak in Open Zaak, using a simple and recognizable example.
- **Requirements:** BR5; FR12
- **Acceptance criteria:**
  - A simple ToDo case (create → in progress → done) is seeded automatically (case definition, BPMN, forms), with no zaak in Open Zaak.
  - Access is determined by its own OpenFTV policy, based on the user's relation to the case (creator, assignee) instead of on roles or zaak attributes. This shows relationship-based access next to role-based access.
  - **Create:** any authenticated user can create a ToDo.
  - **View:** only the creator and the current assignee can see a ToDo. Other users don't see it in lists or search, and they can't open it through a direct URL.
  - **Edit/complete, unassigned (or assigned to the creator):** only the creator can edit or complete the ToDo.
  - **Edit/complete, assigned to someone else:** only the assignee can edit or complete it. The creator keeps read access but loses edit/complete rights while it is assigned.
  - The demo includes at least one assigned ToDo that shows this switch between creator and assignee.
  - A `false` decision blocks access, just as it does for zaak-based processes.

### F8: Demo script
- **Goal:** Presenters can give the demo reliably and consistently.
- **Requirements:** BR1, BR4; FR3
- **Acceptance criteria:**
  - There is a step-by-step script covering which user does what and what to show.
  - The script covers F2, F3, F4, F6 and F7, and it has been walked through at least once without errors.

## Out of scope

- Hosted/shared demo environment. The demo runs locally via docker-compose only.
