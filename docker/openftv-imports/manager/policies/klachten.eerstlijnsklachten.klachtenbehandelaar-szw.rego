package authz

import rego.v1

# Klachtenbehandelaar SZW: handles the complaints assigned to dienst SZW.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_SZW"] := {
	"rights": "behandelaar",
	"diensten": ["SZW"],
}
