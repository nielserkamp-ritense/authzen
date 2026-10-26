package authz

import rego.v1

# Bezwaarbehandelaar: creates and handles bezwaren, does their tasks and starts their user actions.
# User actions on a bezwaar: change-name (Wijzigen aanvraaggegevens), patch-zaak (Zaak bijwerken) and
# afsluiten-bezwaar (Afsluiten bezwaar).
bezwaar_scopes["ROLE_BEZWAAR_BEHANDELAAR"] := {
	"rights": "behandelaar",
	"acties": ["change-name", "patch-zaak", "afsluiten-bezwaar"],
}
