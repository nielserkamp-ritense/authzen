package authz

import rego.v1

# Shared by every klachten role. A role's own policy only says which complaints it handles and what
# kind of rights it has, for example:
#
#   klachten_scopes["ROLE_KLACHTEN_KLACHTBEHANDELAAR_SZW"] := {
#   	"rights": "behandelaar",
#   	"diensten": ["SZW"],
#   }
#
# A scope can have:
#   rights                     kind of rights, see klachten_rights below
#   diensten                   the diensten whose complaints the role handles, or "all"
#   autorisatiegroepen         only OCW complaints of these groups (ALGEMEEN, JGZ, JH)
#   except_autorisatiegroepen  no OCW complaints of these groups (a complaint without a group passes)
#   unassigned                 true: also the complaints that are not assigned to a dienst yet
#
# This policy turns every scope into the permissions GZAC applies.

# ---- the klachten case ----------------------------------------------------------------------------

case_definition := "eerstelijns-klachten"

zaaktype := "http://host.docker.internal:8001/catalogi/api/v1/zaaktypen/dfab41b0-7baa-4efa-8e41-07cfd40f48bc"

dienst := "$.rapportageCategorieen.toegewezenDienst.dienst.name"

autorisatiegroep := "$.verkenning.autorisatieGroep.name"

autorisatiegroepen := {
	"ALGEMEEN": "AUTORISATIEGROEPEN_OCW_ALGEMEEN",
	"JGZ": "AUTORISATIEGROEPEN_OCW_JGZ_JEUGDGEZONDHEIDSZORG",
	"JH": "AUTORISATIEGROEPEN_OCW_JEUGDHULP",
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

# ---- rights per kind of role ----------------------------------------------------------------------
#
# `on` says which resources the actions apply to:
#   anything     every resource of that type
#   the_case     the klachten case definition
#   complaint    the complaints in the role's scope
#   part         what belongs to such a complaint (notes, zaak documents)
#   started_on   what is started on or shown with such a complaint (user actions, widgets)
#   task         the tasks of such a complaint that are meant for the role
#   starting     starting a new case
#
# `"of": "all"` widens a right from the role's scope to every klachten complaint.

case_rights := [
	{"type": case_tab, "actions": ["view"], "on": "anything"},
	{"type": case, "actions": ["view", "view_list"], "on": "the_case"},
	{"type": document_definition, "actions": ["view", "view_list"], "on": "the_case"},
	{"type": search_field, "actions": ["view_list"], "on": "the_case"},
]

# Handles the complaints of their scope.
klachten_rights["behandelaar"] := array.concat(case_rights, [
	{"type": document, "actions": ["view", "view_list", "modify", "claim", "assign", "assignable"], "on": "complaint"},
	{"type": note, "actions": ["view", "view_list", "create", "modify", "delete"], "on": "part"},
	{"type": zaak_document, "actions": ["view", "view_list", "create", "modify"], "on": "part"},
	{"type": widget, "actions": ["view"], "on": "started_on"},
	{"type": user_action, "actions": ["create"], "on": "started_on"},
	{"type": task, "actions": ["view", "view_list", "claim", "complete", "assign", "assignable"], "on": "task"},
	{"type": upload, "actions": ["view", "view_list", "create", "modify", "delete"], "on": "anything"},
])

# Reads the complaints of their scope, changes nothing.
klachten_rights["meelezen"] := array.concat(case_rights, [
	{"type": document, "actions": ["view", "view_list"], "on": "complaint"},
	{"type": note, "actions": ["view", "view_list"], "on": "part"},
	{"type": zaak_document, "actions": ["view", "view_list"], "on": "part"},
	{"type": widget, "actions": ["view"], "on": "started_on"},
	{"type": upload, "actions": ["view", "view_list"], "on": "anything"},
])

# Registers complaints and assigns them: reads every complaint, changes the ones in their scope.
klachten_rights["registratie"] := array.concat(case_rights, [
	{"type": document, "actions": ["view", "create"], "on": "complaint", "of": "all"},
	{"type": document, "actions": ["view_list", "modify", "claim", "assign", "assignable"], "on": "complaint"},
	{"type": note, "actions": ["view", "view_list"], "on": "part", "of": "all"},
	{"type": note, "actions": ["create", "modify", "delete"], "on": "part"},
	{"type": zaak_document, "actions": ["view", "view_list"], "on": "part", "of": "all"},
	{"type": zaak_document, "actions": ["create", "modify"], "on": "part"},
	{"type": widget, "actions": ["view"], "on": "started_on", "of": "all"},
	{"type": user_action, "actions": ["create"], "on": "starting"},
	{"type": user_action, "actions": ["create"], "on": "started_on"},
	{"type": task, "actions": ["view", "view_list", "claim", "complete", "assign", "assignable"], "on": "task", "of": "all"},
	{"type": upload, "actions": ["view", "view_list", "create", "modify", "delete"], "on": "anything"},
])

# ---- which complaints a scope covers ---------------------------------------------------------------

# One list of conditions per alternative; a complaint is in scope when it meets all conditions of one.
complaints(scope) := array.concat(dienst_complaints(scope), unassigned_complaints(scope))

dienst_complaints(scope) := [[klachten_zaaktype]] if {
	scope.diensten == "all"
} else := [array.concat(
	[klachten_zaaktype, json_value("content.content", dienst, "in", scope.diensten)],
	group_conditions(scope),
)] if {
	count(object.get(scope, "diensten", [])) > 0
} else := []

unassigned_complaints(scope) := [[klachten_zaaktype, json_value("content.content", dienst, "==", null)]] if {
	scope.unassigned
} else := []

group_conditions(scope) := array.concat(
	[json_value("content.content", autorisatiegroep, "in", [autorisatiegroepen[g] | some g in scope.autorisatiegroepen]) |
		scope.autorisatiegroepen],
	[json_value("content.content", autorisatiegroep, "!=", autorisatiegroepen[g]) |
		some g in object.get(scope, "except_autorisatiegroepen", [])],
)

klachten_zaaktype := related(case, [
	related("com.ritense.zakenapi.domain.ZaakTypeLink", [field("zaakTypeUrl", "==", zaaktype)]),
])

# The complaints a right applies to: the role's scope, or every klachten complaint.
scoped(right, scope) := [[klachten_zaaktype]] if {
	right.of == "all"
} else := complaints(scope)

# The field that names the case definition, per resource type.
case_key := {
	case: "id.key",
	document_definition: "id.name",
	search_field: "id.caseDefinitionKey",
}

conditions("anything", _, _, _) := [[]]

conditions("the_case", right, _, _) := [[field(case_key[right.type], "==", case_definition)]]

conditions("complaint", right, _, scope) := scoped(right, scope)

conditions("part", right, _, scope) := [[related(document, c)] | some c in scoped(right, scope)]

conditions("task", right, role, scope) := [[
	related("com.ritense.valtimo.operaton.domain.OperatonIdentityLink", [field("groupId", "==", role)]),
	related(document, c),
] | some c in scoped(right, scope)]

# ---- decision -------------------------------------------------------------------------------------

allow if {
	some role, scope in klachten_scopes
	has_role(role)
	some right in klachten_rights[scope.rights]
	has_resource_type(right.type)
	has_action(right.actions)
}

filter contains permission(role, right.type, right.actions, c) if {
	some role, scope in klachten_scopes
	some right in klachten_rights[scope.rights]
	has_resource_type(right.type)
	has_action(right.actions)
	not right.on in {"started_on", "starting"}
	some c in conditions(right.on, right, role, scope)
}

filter contains context_permission(role, right.type, right.actions, document, c) if {
	some role, scope in klachten_scopes
	some right in klachten_rights[scope.rights]
	has_resource_type(right.type)
	has_action(right.actions)
	right.on == "started_on"
	some c in scoped(right, scope)
}

filter contains context_permission(role, right.type, right.actions, "com.ritense.authorization.NoContext", []) if {
	some role, scope in klachten_scopes
	some right in klachten_rights[scope.rights]
	has_resource_type(right.type)
	has_action(right.actions)
	right.on == "starting"
}
