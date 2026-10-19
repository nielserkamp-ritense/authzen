package authz

import rego.v1

# Medewerker KCC: reads every complaint, to answer questions from the melder. Changes nothing.
klachten_scopes["ROLE_KLACHTEN_KCC"] := {
	"rights": "meelezen",
	"diensten": "all",
}
