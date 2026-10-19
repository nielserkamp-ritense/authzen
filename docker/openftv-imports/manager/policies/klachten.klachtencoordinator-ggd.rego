package authz

import rego.v1

# Klachtencoördinator GGD: handles the GGD complaints, and the complaints that are not assigned to a
# dienst yet.
klachten_scopes["ROLE_KLACHTEN_KLACHTENCOORDINATOR_GGD"] := {
	"rights": "coordinator",
	"diensten": ["GGD"],
	"unassigned": true,
}
