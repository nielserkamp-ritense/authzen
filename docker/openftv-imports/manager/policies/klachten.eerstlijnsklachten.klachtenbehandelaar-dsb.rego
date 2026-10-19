package authz

import rego.v1

# Klachtenbehandelaar DSB (Dienst Stadsbeheer): handles the complaints assigned to dienst DSB.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_DSB_DIENST_STADSBEHEER"] := {
	"rights": "behandelaar",
	"diensten": ["DSB"],
}
