package authz

import rego.v1

# Klachtenbehandelaar BSD-Bestuursdienst: handles the complaints assigned to dienst BSD.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_BSD_BESTUURSDIENST"] := {
	"rights": "behandelaar",
	"diensten": ["BSD"],
}
