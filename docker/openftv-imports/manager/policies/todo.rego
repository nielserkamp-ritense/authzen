package authz

import rego.v1

# ToDo rights for every logged-in user (ROLE_USER). They don't follow a role or a zaak, but the user's
# relation to the ToDo:
#   - everyone may create a ToDo;
#   - only its creator and its current assignee see it;
#   - while it is unassigned (or assigned to its creator), only the creator changes, completes and
#     assigns it;
#   - once it is assigned to someone else, only that assignee does; the creator can still read it.
#
# Each entry is one permission, as in valtimo.rego. A right that has alternatives (creator OR assignee)
# becomes one permission per alternative: conditions within a permission are AND, permissions are OR.

todo_case_definition := "todo"

is_todo := related(case, [field("id.key", "==", todo_case_definition)])

# GZAC stores the creator's email in createdBy and the assignee's username in assigneeId.
creator := field("createdBy", "==", "${currentUserEmail}")

assignee := field("assigneeId", "==", "${currentUsername}")

unassigned := field("assigneeId", "==", null)

# Sees the ToDo: its creator or its assignee.
viewer := [[is_todo, creator], [is_todo, assignee]]

# Changes the ToDo: its creator while nobody else has it, or its assignee.
editor := [[is_todo, creator, unassigned], [is_todo, assignee]]

on_todo(alternatives) := [[related(document, conditions)] | some conditions in alternatives]

# One group per kind of right; a right with alternatives gets one permission per alternative.
todo_permission_groups := [
	[
		{"type": case, "actions": ["view", "view_list"], "conditions": [field("id.key", "==", todo_case_definition)]},
		{"type": document_definition, "actions": ["view", "view_list"], "conditions": [field("id.name", "==", todo_case_definition)]},
		{"type": search_field, "actions": ["view_list"], "conditions": [field("id.caseDefinitionKey", "==", todo_case_definition)]},
		{"type": document, "actions": ["create"], "conditions": [is_todo]},
		# Assignable is checked for the user a ToDo is assigned to, so it can't depend on the current user.
		{"type": document, "actions": ["assignable"], "conditions": [is_todo]},
		{"type": task, "actions": ["assignable"], "conditions": [related(document, [is_todo])]},
		{
			"type": user_action, "actions": ["create"],
			"conditions": [related(process_definition, [field("key", "==", todo_case_definition)])],
			"context": no_context, "context_conditions": [],
		},
	],
	[{"type": document, "actions": ["view", "view_list"], "conditions": c} | some c in viewer],
	[{"type": document, "actions": ["modify", "claim", "assign"], "conditions": c} | some c in editor],
	[{"type": note, "actions": ["view", "view_list"], "conditions": c} | some c in on_todo(viewer)],
	[{"type": note, "actions": ["create", "modify", "delete"], "conditions": c} | some c in on_todo(editor)],
	[{"type": task, "actions": ["view", "view_list"], "conditions": c} | some c in on_todo(viewer)],
	[{"type": task, "actions": ["claim", "complete", "assign"], "conditions": c} | some c in on_todo(editor)],
	[{"type": widget, "actions": ["view"], "conditions": [], "context": document, "context_conditions": c} | some c in viewer],
]

todo_permissions := [p | some group in todo_permission_groups; some p in group]

# ---- decision -------------------------------------------------------------------------------------

allow if {
	some p in todo_permissions
	has_role("ROLE_USER")
	has_resource_type(p.type)
	has_action(p.actions)
}

filter contains permission("ROLE_USER", p.type, p.actions, p.conditions) if {
	some p in todo_permissions
	has_resource_type(p.type)
	has_action(p.actions)
	not p.context
}

filter contains context_permission_with("ROLE_USER", p.type, p.actions, p.conditions, p.context, p.context_conditions) if {
	some p in todo_permissions
	has_resource_type(p.type)
	has_action(p.actions)
	p.context
}
