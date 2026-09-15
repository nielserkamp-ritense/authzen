package authz

import rego.v1

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
