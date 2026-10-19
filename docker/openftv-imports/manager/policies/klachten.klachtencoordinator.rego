package authz

import rego.v1

# Klachtencoördinator: handles the complaints of every dienst except GGD and VTH (they have their own
# coordinator), and the complaints that are not assigned to a dienst yet.
klachten_scopes["ROLE_KLACHTEN_KLACHTENCOORDINATOR"] := {
	"rights": "hoofdcoordinator",
	"diensten": ["BSD", "DBV", "DPZ", "DSB", "DSO", "OCW", "SZW"],
	"unassigned": true,
}
