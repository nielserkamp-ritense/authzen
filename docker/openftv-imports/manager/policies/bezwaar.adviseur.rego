package authz

import rego.v1

# Juridisch adviseur: reads bezwaren and adds notes and documents. Changes nothing else.
bezwaar_scopes["ROLE_BEZWAAR_ADVISEUR"] := {"rights": "adviseur"}
