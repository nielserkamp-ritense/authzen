package authz

import rego.v1

# Klachtenbehandelaar OCW: handles the OCW complaints, except those of autorisatiegroep JGZ and JH.
# Complaints without an autorisatiegroep (before the verkenning) are included.
klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_OCW_ALGEMEEN"] := {
	"rights": "behandelaar",
	"diensten": ["OCW"],
	"except_autorisatiegroepen": ["JGZ", "JH"],
}
