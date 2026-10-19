package authz

import rego.v1

# Medewerker IB/Post: registers complaints and assigns them to a dienst. Reads every complaint, and
# changes only the ones that are not assigned to a dienst yet.
klachten_scopes["ROLE_KLACHTEN_IB_POST"] := {
	"rights": "registratie",
	"unassigned": true,
}
