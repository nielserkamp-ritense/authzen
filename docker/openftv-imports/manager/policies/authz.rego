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
context_permission(role, resource_type, actions, context_type, context_conditions) := {
	"type": "ValtimoAuthorizationPermission",
	"role": role,
	"resourceType": resource_type,
	"actions": actions,
	"conditionContainer": {"conditions": []},
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
