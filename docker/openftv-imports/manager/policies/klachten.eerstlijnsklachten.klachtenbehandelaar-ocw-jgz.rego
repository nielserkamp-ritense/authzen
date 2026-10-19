package authz

import rego.v1

# Klachtenbehandelaar OCW-JGZ: handles the OCW complaints of autorisatiegroep JGZ.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_OCW_JGZ"] := {
	"rights": "behandelaar",
	"diensten": ["OCW"],
	"autorisatiegroepen": ["JGZ"],
}
