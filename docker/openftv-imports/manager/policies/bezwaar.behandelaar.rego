package authz

import rego.v1

# Bezwaarbehandelaar: creates and handles bezwaren, does their tasks and starts their user actions.
bezwaar_scopes["ROLE_BEZWAAR_BEHANDELAAR"] := {"rights": "behandelaar"}
