package authz

import rego.v1

# Shared by every policy in package `authz`. GZAC sends one request per resource type and action, and
# reads two things from the answer:
#   allow           may the user do this at all?
#   context.filter  the Valtimo permissions (rows) that say on which resources. GZAC keeps the rows of
#                   the user's roles, and turns them into a database filter and an entity check.

has_role(role) if {
	some r in input.subject.attributes.roles
	r == role
}

has_resource_type(resource_type) if {
	input.resource.type == resource_type
}

has_action(actions) if {
	some a in actions
	input.action.id == a
}

# ---- resource types -------------------------------------------------------------------------------

case_tab := "com.ritense.case.domain.CaseTab"

case := "com.ritense.case_.domain.definition.CaseDefinition"

document_definition := "com.ritense.document.domain.impl.JsonSchemaDocumentDefinition"

search_field := "com.ritense.document.domain.impl.searchfield.SearchField"

document := "com.ritense.document.domain.impl.JsonSchemaDocument"

note := "com.ritense.note.domain.Note"

zaak_document := "com.ritense.documentenapi.authorization.ZgwDocument"

widget := "com.ritense.case_.domain.tab.CaseWidgetTabWidget"

user_action := "com.ritense.valtimo.operaton.domain.OperatonExecution"

task := "com.ritense.valtimo.operaton.domain.OperatonTask"

upload := "com.ritense.resource.authorization.ResourcePermission"

dashboard := "com.ritense.dashboard.domain.Dashboard"

user := "com.ritense.valtimo.contract.authentication.User"

document_snapshot := "com.ritense.document.domain.impl.snapshot.JsonSchemaDocumentSnapshot"

zaak := "com.ritense.zakenapi.security.Zaak"

zaaktype_link := "com.ritense.zakenapi.domain.ZaakTypeLink"

identity_link := "com.ritense.valtimo.operaton.domain.OperatonIdentityLink"

process_definition := "com.ritense.valtimo.operaton.domain.OperatonProcessDefinition"

timer := "com.ritense.valtimo.operaton.domain.OperatonTimer"

api_object := "com.ritense.objectenapi.security.Object"

object_management := "com.ritense.objectmanagement.domain.ObjectManagement"

iko_view := "com.ritense.iko.domain.IkoView"

team := "com.ritense.team.domain.Team"

# The context of a permission that is not about a specific resource (e.g. starting a new case).
no_context := "com.ritense.authorization.NoContext"

# ---- building blocks for filter rows --------------------------------------------------------------

# A permission on the resource itself.
permission(role, resource_type, actions, conditions) := {
	"type": "ValtimoAuthorizationPermission",
	"role": role,
	"resourceType": resource_type,
	"actions": actions,
	"conditionContainer": {"conditions": conditions},
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
}

# A permission that only applies in the context of another resource (e.g. starting a process on a
# case: the conditions are about the case, not about the process).
context_permission(role, resource_type, actions, context_type, context_conditions) := context_permission_with(
	role, resource_type, actions, [], context_type, context_conditions,
)

# As context_permission, with conditions on the resource as well (e.g. which process may be started).
context_permission_with(role, resource_type, actions, conditions, context_type, context_conditions) := {
	"type": "ValtimoAuthorizationPermission",
	"role": role,
	"resourceType": resource_type,
	"actions": actions,
	"conditionContainer": {"conditions": conditions},
	"contextResourceType": context_type,
	"contextConditionContainer": {"conditions": context_conditions},
}

# A property of the resource compares with a value.
field(name, operator, value) := {"type": "field", "field": name, "operator": operator, "value": value}

# A value inside a JSON property compares with a value.
json_value(name, path, operator, value) := {
	"type": "expression",
	"field": name,
	"path": path,
	"operator": operator,
	"value": value,
	"clazz": "java.lang.String",
}

# The conditions hold for a related resource (e.g. the case a note belongs to).
related(resource_type, conditions) := {"type": "container", "resourceType": resource_type, "conditions": conditions}

context := {"filter": sort(filter)}
