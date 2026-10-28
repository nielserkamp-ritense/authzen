# Demodraaiboek: autorisatie buiten GZAC

In deze demo bepaalt niet GZAC zelf wie wat mag, maar een aparte policy-engine (OpenFTV). Je laat zien dat je de rechten centraal beheert, tot op de afdeling, de zaakstatus of de relatie met een zaak, en dat je ze aanpast zonder release.

- **Doelgroep:** beheerders.
- **Duur:** 10 minuten.
- **Nodig:** de demo-omgeving uit deze repository (zie de [README](../README.md)) en een browser met privévensters of profielen.

## Voorbereiding (vooraf, ±10 minuten)

1. Zet de omgeving klaar:

   ```bash
   scripts/demo-prepare.sh
   ```

   Dit start alles schoon op (3 à 5 minuten), zet de demogegevens klaar en controleert of elke gebruiker ziet wat dit draaiboek belooft. Aan het eind staat `✅ demo ready` en een lijst met de demozaken en hun URL's.
2. Open **één privévenster (of browserprofiel) per gebruiker** en log vooraf in. Keycloak onthoudt per browser maar één ingelogde gebruiker. Per onderdeel van het draaiboek staat welk venster, welke URL en welke gebruiker je nodig hebt.
3. Kopieer de URL van **"Demo DSO"** uit de uitvoer van stap 1. Die heb je nodig in venster 1.
4. Vlak voor je begint:

   ```bash
   scripts/demo-seed.py --check
   ```

   Staat er geen `✅ demo ready`? Draai dan `scripts/demo-prepare.sh` opnieuw.
5. De demo draait zonder cache, en dat is de standaard. Start niet met `./run.sh --cache`: dan duurt de live wijziging tot een minuut in plaats van een seconde.

## Draaiboek

### 0:00–1:00 · Inleiding

> GZAC vraagt bij elke handeling aan een aparte policy-engine: "mag deze gebruiker dit?" Dat gaat via de open standaard AuthZEN. De regels staan in policies (Rego) in OpenFTV, niet in de applicatie. We laten drie processen zien: klachten en bezwaar, die bij een zaak horen en per rol werken, en een ToDo zonder zaak, waar je relatie met de ToDo telt.

Laat eventueel het plaatje uit de README zien (*How it fits together*).

### 1:00–3:30 · Klachten: één rol per afdeling

- Venster 1 · SZW: http://localhost, `klachten-behandelaar-szw` / `klachten-behandelaar-szw`
- Venster 2 · KCC: http://localhost, `klachten-kcc` / `klachten-kcc`

| Venster | Doen | Laten zien |
|---|---|---|
| 1 · SZW | Toon de zaaklijst klachten. | Wel **"Demo SZW"**, niet **"Demo DSO"**. |
| 1 · SZW | Open "Demo SZW". | De behandelaar van SZW heeft hier een taak. Het proces loopt gewoon. |
| 1 · SZW | Plak de URL van "Demo DSO" in de adresbalk. | **Geen toegang**, ook niet via een directe link. |
| 2 · KCC | Toon de zaaklijst klachten en open "Demo SZW". | KCC ziet **alle** klachten, maar kan niets wijzigen: geen acties, geen notitie toevoegen. |

> Het is dezelfde applicatie en hetzelfde proces. Wat je ziet en mag, hangt af van je rol en de afdeling van de klacht, tot op de directe URL.

### 3:30–5:30 · Live wijziging: SZW krijgt ook DSO

- Venster 7 · Beheer: http://localhost:8180, `author-user` / `password` (niet `admin-user`: daarmee kun je policies niet bewerken)
- Venster 1 · SZW: http://localhost, `klachten-behandelaar-szw` / `klachten-behandelaar-szw`

| Venster | Doen | Laten zien |
|---|---|---|
| 7 · Beheer | Open de policy `klachten.eerstlijnsklachten.klachtenbehandelaar-szw` en toon `"diensten": ["SZW"]`. Klik **Bewerken**, maak er `"diensten": ["SZW", "DSO"],` van en klik **Opslaan**. | De regel zegt alleen welke klachten SZW behandelt. GZAC verandert nog niets. |
| 7 · Beheer | Ga naar **Publicaties** en klik **Publiceren**. Wacht tot de publicatie klaar is (een paar seconden). | |
| 1 · SZW | Vernieuw de zaaklijst. | **"Demo DSO"** staat er nu ook bij, en is te openen. |

> Er was geen release en geen herstart. De wijziging is een seconde na het publiceren actief, voor alle gebruikers.

Let op met typfouten. Een policy die niet compileert, wordt toch "gepubliceerd", en dan ziet niemand meer klachten. Twijfel je, controleer dan eerst met `scripts/policy-check.py --manager`.

### 5:30–7:30 · Bezwaar: ander zaaktype, andere rollen

- Venster 3 · Behandelaar: http://localhost, `bezwaar-behandelaar` / `bezwaar-behandelaar`
- Venster 4 · Adviseur: http://localhost, `bezwaar-adviseur` / `bezwaar-adviseur`

| Venster | Doen | Laten zien |
|---|---|---|
| 3 · Behandelaar | Open "Demo open" en toon de acties. | Drie acties: **Wijzigen aanvraaggegevens**, **Zaak bijwerken** en **Afsluiten bezwaar**. |
| 4 · Adviseur | Open hetzelfde bezwaar. | De juridisch adviseur ziet het bezwaar en kan een **notitie** toevoegen, maar heeft **geen acties**. |
| 3 · Behandelaar | Open "Demo afgerond". | Een afgerond bezwaar is voor iedereen **alleen lezen**: geen acties meer. |

> Het bezwaar heeft een eigen policy. Die noemt per rol welke acties mogen, en de status van het bezwaar telt ook mee. Klachtenmedewerkers zien helemaal geen bezwaren.

### 7:30–9:00 · ToDo: geen zaak, maar je relatie met de ToDo

- Venster 5 · Anna: http://localhost, `todo-anna` / `todo-anna`
- Venster 6 · Bram: http://localhost, `todo-bram` / `todo-bram`

| Venster | Doen | Laten zien |
|---|---|---|
| 5 · Anna | Toon de zaaklijst ToDo. | **"Boodschappen bestellen"** en **"Rapport nalezen"**, niet bram's "Presentatie voorbereiden". |
| 5 · Anna | Open "Rapport nalezen". | Anna heeft hem aangemaakt, maar aan bram toegewezen. Ze kan hem nog **lezen**, maar niet meer wijzigen. |
| 6 · Bram | Toon de zaaklijst ToDo. | **"Presentatie voorbereiden"** en **"Rapport nalezen"** (aan hem toegewezen), niet anna's "Boodschappen bestellen". |

> Hier speelt geen rol en geen zaak. Wie de ToDo maakte en aan wie hij is toegewezen, bepaalt de rechten. Hetzelfde mechanisme, een ander soort regel.

### 9:00–10:00 · Logboek en afsluiting

- Venster 7 · Beheer: http://localhost:8180, `author-user` / `password` (niet `admin-user`: daarmee kun je policies niet bewerken)

| Venster | Doen | Laten zien |
|---|---|---|
| 7 · Beheer | Open **Logboek**. | Elke vraag van GZAC aan de policy-engine is vastgelegd: wie, welke handeling, het antwoord en het filter dat GZAC toepast. |

> Samengevat:
> 1. Autorisatie staat buiten de applicatie, centraal en leesbaar.
> 2. Fijnmazig: per afdeling, per actie, per status, en per relatie.
> 3. Een wijziging werkt direct, zonder release.

## Na de demo

Draai de live wijziging terug:

```bash
./run.sh --reload-policies     # alle policies terug naar de bestanden in git (±30 seconden)
```

Voor een volgende demo draai je weer `scripts/demo-prepare.sh`.

## Als het misgaat

| Wat je ziet | Oorzaak en oplossing |
|---|---|
| Niemand ziet nog klachten, bezwaren of ToDo's | Een typfout in een gepubliceerde policy, of de policy-engine is net (her)start en heeft de policies nog niet (±30 seconden). Herstel de policy en publiceer opnieuw, of wacht even. Twijfel je, draai dan `./run.sh --reload-policies`. |
| Een foutmelding (400) bij een actie die niet mag | Normaal: GZAC meldt een geweigerde actie als 400. Er is niets veranderd. |
| "Demo DSO" verschijnt niet na de live wijziging | Nog niet gepubliceerd, of de publicatie loopt nog. Kijk bij **Publicaties** en vernieuw daarna. |
| Bewerken kan niet in de beheeromgeving | Je bent ingelogd als `admin-user`. Log in als `author-user`. |
| `demo-seed.py --check` faalt | De omgeving is niet in de beginstand, bijvoorbeeld door een eerdere live wijziging. Draai `scripts/demo-prepare.sh`. |

## Tijd over?

- **De adviseur mag afsluiten.**
  - In de beheeromgeving: zet in `bezwaar.adviseur` `"acties": ["afsluiten-bezwaar"]` en publiceer.
  - De adviseur heeft dan precies die ene actie.
- **De maker van een ToDo blijft wijzigen na het toewijzen.**
  - In `todo`: maak `editor := [[is_todo, creator], [is_todo, assignee]]`.
  - Anna kan "Rapport nalezen" dan weer wijzigen.

Beide staan uitgewerkt in de README onder *Live policy change*. Draai na afloop `./run.sh --reload-policies`.
