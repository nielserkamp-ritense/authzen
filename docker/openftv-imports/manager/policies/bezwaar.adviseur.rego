package authz

import rego.v1

# Juridisch adviseur: reads bezwaren and adds notes and documents. Starts no user actions; add one to
# `acties` (change-name, patch-zaak, afsluiten-bezwaar) to allow it.
bezwaar_scopes["ROLE_BEZWAAR_ADVISEUR"] := {
	"rights": "adviseur",
	"acties": [],
}
