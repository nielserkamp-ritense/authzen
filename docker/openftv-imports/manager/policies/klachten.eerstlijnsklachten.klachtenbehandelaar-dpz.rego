package authz

import rego.v1

# Klachtenbehandelaar DPZ: handles the complaints assigned to dienst DPZ.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_DPZ"] := {
	"rights": "behandelaar",
	"diensten": ["DPZ"],
}
