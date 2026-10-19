package authz

import rego.v1

# Klachtenbehandelaar DBV: handles the complaints assigned to dienst DBV.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_DBV"] := {
	"rights": "behandelaar",
	"diensten": ["DBV"],
}
