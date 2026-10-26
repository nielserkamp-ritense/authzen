package authz

import rego.v1

# Generic Valtimo rights: administrators (ROLE_ADMIN) and every logged-in user (ROLE_USER). Every demo
# user also has ROLE_USER, so it grants nothing on cases: each case type (klachten, bezwaar) has its own
# policy that grants its roles their case, documents, notes, widgets and actions.
#
# Each entry is one permission: who (`role`) may do what (`actions`) on which resources (`type`, with
# `conditions` on the resource), optionally only in the `context` of another resource. Values like
# ${currentUsername} and ${currentUserTeams} are Valtimo placeholders, filled in by GZAC.

valtimo_permissions := [
	# ---- cases ------------------------------------------------------------------------------------
	{"role": "ROLE_ADMIN", "type": case_tab, "actions": ["view"], "conditions": []},
	{"role": "ROLE_USER", "type": case_tab, "actions": ["view"], "conditions": []},
	{"role": "ROLE_ADMIN", "type": case, "actions": ["view", "view_list"], "conditions": []},
	{"role": "ROLE_ADMIN", "type": document_definition, "actions": ["view", "view_list", "create", "modify", "delete"], "conditions": []},
	{"role": "ROLE_ADMIN", "type": search_field, "actions": ["view_list"], "conditions": []},
	# Administrators: every case.
	{"role": "ROLE_ADMIN", "type": document, "actions": [
		"view", "view_list", "create", "modify", "delete", "claim", "assign", "assignable",
		"export", "inspect", "inspect_modify",
	], "conditions": []},
	{"role": "ROLE_ADMIN", "type": document_snapshot, "actions": ["view", "view_list"], "conditions": []},
	# ---- widgets ----------------------------------------------------------------------------------
	# Widget data is checked against the widget, not the case: each case policy grants the widgets of
	# its own cases. ROLE_USER only gets widgets outside a case (dashboards).
	{"role": "ROLE_ADMIN", "type": widget, "actions": ["view"], "conditions": []},
	{"role": "ROLE_USER", "type": widget, "actions": ["view"], "context": no_context, "context_conditions": []},
	# ---- notes and zaak documents -----------------------------------------------------------------
	{"role": "ROLE_ADMIN", "type": note, "actions": ["view", "view_list", "create", "modify", "delete"], "conditions": []},
	{"role": "ROLE_ADMIN", "type": zaak_document, "actions": ["view", "view_list", "create", "modify", "delete"], "conditions": []},
	{"role": "ROLE_ADMIN", "type": zaak, "actions": ["view"], "conditions": []},
	# ---- tasks and processes ----------------------------------------------------------------------
	{"role": "ROLE_ADMIN", "type": task, "actions": ["view", "view_list", "claim", "complete", "assign"], "conditions": []},
	# A task can be assigned to a user of its candidate group, or of one of their teams. Conditions are
	# AND, so each alternative is its own permission.
	{"role": "ROLE_ADMIN", "type": task, "actions": ["assignable"], "conditions": [candidate_group_is("ROLE_ADMIN")]},
	{"role": "ROLE_ADMIN", "type": task, "actions": ["assignable"], "conditions": [candidate_group_in_teams]},
	{"role": "ROLE_USER", "type": task, "actions": ["view", "view_list", "claim", "complete", "assign", "assignable"], "conditions": [
		candidate_group_is("ROLE_USER"),
	]},
	{"role": "ROLE_USER", "type": task, "actions": ["view", "view_list", "claim", "complete", "assign", "assignable"], "conditions": [
		candidate_group_in_teams,
	]},
	{"role": "ROLE_ADMIN", "type": timer, "actions": ["complete"], "conditions": []},
	{"role": "ROLE_ADMIN", "type": user_action, "actions": ["create"], "conditions": []},
	# ---- objects ----------------------------------------------------------------------------------
	{"role": "ROLE_ADMIN", "type": api_object, "actions": ["view", "view_list", "create", "modify", "delete"], "conditions": []},
	{"role": "ROLE_USER", "type": api_object, "actions": ["view", "view_list"], "conditions": []},
	{"role": "ROLE_ADMIN", "type": object_management, "actions": ["view_list"], "conditions": []},
	{"role": "ROLE_USER", "type": object_management, "actions": ["view_list"], "conditions": [field("title", "==", "Bomen")]},
	{"role": "ROLE_ADMIN", "type": iko_view, "actions": ["view", "view_list"], "conditions": []},
	# ---- users, teams and dashboards --------------------------------------------------------------
	{"role": "ROLE_ADMIN", "type": user, "actions": ["view", "view_list"], "conditions": []},
	# A plain user sees other plain users.
	{"role": "ROLE_USER", "type": user, "actions": ["view", "view_list"], "conditions": [field("roles", "list_contains", "ROLE_USER")]},
	{"role": "ROLE_ADMIN", "type": team, "actions": ["view", "view_list", "create", "modify", "delete", "assign"], "conditions": []},
	# `list_contains`: the field holds a list, and the value is the item looked for.
	{"role": "ROLE_USER", "type": team, "actions": ["view", "view_list", "modify", "delete", "assign"], "conditions": [
		field("users", "list_contains", "${currentUsername}"),
	]},
	{"role": "ROLE_ADMIN", "type": dashboard, "actions": ["view"], "conditions": [field("key", "==", "my_admin_dashboard")]},
	{"role": "ROLE_USER", "type": dashboard, "actions": ["view", "view_list"], "conditions": [field("key", "==", "user-dashboard")]},
]

candidate_group_is(group) := related(identity_link, [field("groupId", "==", group)])

candidate_group_in_teams := related(identity_link, [field("groupId", "in", "${currentUserTeams}")])

# ---- decision -------------------------------------------------------------------------------------

allow if {
	some p in valtimo_permissions
	has_role(p.role)
	has_resource_type(p.type)
	has_action(p.actions)
}

filter contains permission(p.role, p.type, p.actions, p.conditions) if {
	some p in valtimo_permissions
	has_resource_type(p.type)
	has_action(p.actions)
	not p.context
}

filter contains context_permission(p.role, p.type, p.actions, p.context, p.context_conditions) if {
	some p in valtimo_permissions
	has_resource_type(p.type)
	has_action(p.actions)
	p.context
}
