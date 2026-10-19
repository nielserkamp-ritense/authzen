package authz

import rego.v1

# Klachtencoördinator VTH: handles the VTH complaints, and the complaints that are not assigned to a
# dienst yet.
klachten_scopes["ROLE_KLACHTEN_KLACHTENCOORDINATOR_VTH"] := {
	"rights": "coordinator",
	"diensten": ["VTH"],
	"unassigned": true,
}
