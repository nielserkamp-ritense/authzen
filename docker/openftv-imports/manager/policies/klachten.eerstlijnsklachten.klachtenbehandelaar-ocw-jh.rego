package authz

import rego.v1

# Klachtenbehandelaar OCW-JH: handles the OCW complaints of autorisatiegroep JH.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_OCW_JH"] := {
	"rights": "behandelaar",
	"diensten": ["OCW"],
	"autorisatiegroepen": ["JH"],
}
