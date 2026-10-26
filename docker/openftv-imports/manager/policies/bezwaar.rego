package authz

import rego.v1

# Shared by every bezwaar role. A role's own policy only says what kind of rights it has, for example:
#
#   bezwaar_scopes["ROLE_BEZWAAR_BEHANDELAAR"] := {"rights": "behandelaar"}
#
# This policy turns every scope into the permissions GZAC applies. Everything that changes a bezwaar
# stops once its internal status is "afgerond": it stays visible, but is read only.

# ---- the bezwaar case -----------------------------------------------------------------------------

bezwaar_case_definition := "bezwaar"

bezwaar_zaaktype := "http://host.docker.internal:8001/catalogi/api/v1/zaaktypen/744ca059-f412-49d4-8963-5800e4afd486"

afgerond := "afgerond"

# ---- rights per kind of role ----------------------------------------------------------------------
#
# `on` says which resources the actions apply to:
#   anything         every resource of that type
#   the_case         the bezwaar case definition
#   bezwaar          every bezwaar
#   open_bezwaar     every bezwaar that is not afgerond
#   part             what belongs to a bezwaar (notes, zaak documents)
#   open_part        what belongs to a bezwaar that is not afgerond
#   task             the tasks of a bezwaar that are meant for the role
#   open_task        those tasks, while the bezwaar is not afgerond
#   started_on       what is shown with a bezwaar (widgets)
#   started_on_open  what is started on a bezwaar that is not afgerond (user actions)
#   starting         starting a new bezwaar
#
# The internal status is only checked on rights that change an existing bezwaar: a new bezwaar has no
# status yet, and GZAC can't check a field of a status that is not there.

bezwaar_case_rights := [
	{"type": case_tab, "actions": ["view"], "on": "anything"},
	{"type": case, "actions": ["view", "view_list"], "on": "the_case"},
	{"type": document_definition, "actions": ["view", "view_list"], "on": "the_case"},
	{"type": search_field, "actions": ["view_list"], "on": "the_case"},
]

# Handles bezwaren: creates them, does the tasks and starts the user actions.
bezwaar_rights["behandelaar"] := array.concat(bezwaar_case_rights, [
	{"type": document, "actions": ["view", "view_list", "create"], "on": "bezwaar"},
	{"type": document, "actions": ["modify", "claim", "assign", "assignable"], "on": "open_bezwaar"},
	{"type": note, "actions": ["view", "view_list"], "on": "part"},
	{"type": note, "actions": ["create", "modify", "delete"], "on": "open_part"},
	{"type": zaak_document, "actions": ["view", "view_list"], "on": "part"},
	{"type": zaak_document, "actions": ["create", "modify"], "on": "open_part"},
	{"type": widget, "actions": ["view"], "on": "started_on"},
	{"type": user_action, "actions": ["create"], "on": "started_on_open"},
	{"type": user_action, "actions": ["create"], "on": "starting"},
	{"type": task, "actions": ["view", "view_list"], "on": "task"},
	{"type": task, "actions": ["claim", "complete", "assign", "assignable"], "on": "open_task"},
	{"type": upload, "actions": ["view", "view_list", "create", "modify", "delete"], "on": "anything"},
])

# Juridisch adviseur: reads bezwaren and adds notes and documents. No tasks, no user actions.
bezwaar_rights["adviseur"] := array.concat(bezwaar_case_rights, [
	{"type": document, "actions": ["view", "view_list"], "on": "bezwaar"},
	{"type": note, "actions": ["view", "view_list"], "on": "part"},
	{"type": note, "actions": ["create", "modify", "delete"], "on": "open_part"},
	{"type": zaak_document, "actions": ["view", "view_list"], "on": "part"},
	{"type": zaak_document, "actions": ["create", "modify"], "on": "open_part"},
	{"type": widget, "actions": ["view"], "on": "started_on"},
	{"type": upload, "actions": ["view", "view_list", "create"], "on": "anything"},
])

# ---- which bezwaren -------------------------------------------------------------------------------

is_bezwaar := related(case, [
	related(zaaktype_link, [field("zaakTypeUrl", "==", bezwaar_zaaktype)]),
])

not_afgerond := field("internalStatus.id.key", "!=", afgerond)

bezwaar_conditions("anything", _, _) := []

bezwaar_conditions("the_case", right, _) := [field(case_key[right.type], "==", bezwaar_case_definition)]

bezwaar_conditions("bezwaar", _, _) := [is_bezwaar]

bezwaar_conditions("open_bezwaar", _, _) := [is_bezwaar, not_afgerond]

bezwaar_conditions("part", _, _) := [related(document, [is_bezwaar])]

bezwaar_conditions("open_part", _, _) := [related(document, [is_bezwaar, not_afgerond])]

bezwaar_conditions("task", _, role) := [
	related(identity_link, [field("groupId", "==", role)]),
	related(document, [is_bezwaar]),
]

bezwaar_conditions("open_task", _, role) := [
	related(identity_link, [field("groupId", "==", role)]),
	related(document, [is_bezwaar, not_afgerond]),
]

# The case conditions of rights that apply in the context of a bezwaar.
bezwaar_context := {
	"started_on": [is_bezwaar],
	"started_on_open": [is_bezwaar, not_afgerond],
}

# ---- decision -------------------------------------------------------------------------------------

allow if {
	some role, scope in bezwaar_scopes
	has_role(role)
	some right in bezwaar_rights[scope.rights]
	has_resource_type(right.type)
	has_action(right.actions)
}

filter contains permission(role, right.type, right.actions, bezwaar_conditions(right.on, right, role)) if {
	some role, scope in bezwaar_scopes
	some right in bezwaar_rights[scope.rights]
	has_resource_type(right.type)
	has_action(right.actions)
	not right.on in {"started_on", "started_on_open", "starting"}
}

filter contains context_permission(role, right.type, right.actions, document, bezwaar_context[right.on]) if {
	some role, scope in bezwaar_scopes
	some right in bezwaar_rights[scope.rights]
	has_resource_type(right.type)
	has_action(right.actions)
	right.on in object.keys(bezwaar_context)
}

filter contains context_permission(role, right.type, right.actions, no_context, []) if {
	some role, scope in bezwaar_scopes
	some right in bezwaar_rights[scope.rights]
	has_resource_type(right.type)
	has_action(right.actions)
	right.on == "starting"
}
