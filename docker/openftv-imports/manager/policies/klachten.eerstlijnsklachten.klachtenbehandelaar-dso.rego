package authz

import rego.v1

# Klachtenbehandelaar DSO: handles the complaints assigned to dienst DSO.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_DSO"] := {
	"rights": "behandelaar",
	"diensten": ["DSO"],
}
