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
# This policy turns every scope into the permissions GZAC applies.

# ---- the klachten case ----------------------------------------------------------------------------

case_definition := "eerstelijns-klachten"

zaaktype := "http://host.docker.internal:8001/catalogi/api/v1/zaaktypen/dfab41b0-7baa-4efa-8e41-07cfd40f48bc"

dienst := "$.rapportageCategorieen.toegewezenDienst.dienst.name"

document := "com.ritense.document.domain.impl.JsonSchemaDocument"

# ---- rights per kind of role ------------------------------------------------------------------------
#
# `on` says which resources the actions apply to:
#   anything     every resource of that type
#   the_case     the klachten case definition
#   complaint    the complaints in the role's scope
#   part         what belongs to such a complaint (notes, zaak documents)
#   started_on   what is started on such a complaint (user actions, widgets)
#   task         the tasks of such a complaint that are meant for the role

klachten_rights["behandelaar"] := {
	"com.ritense.case.domain.CaseTab": {"actions": ["view"], "on": "anything"},
	"com.ritense.case_.domain.definition.CaseDefinition": {"actions": ["view", "view_list"], "on": "the_case"},
	"com.ritense.document.domain.impl.JsonSchemaDocumentDefinition": {"actions": ["view", "view_list"], "on": "the_case"},
	"com.ritense.document.domain.impl.searchfield.SearchField": {"actions": ["view_list"], "on": "the_case"},
	document: {"actions": ["view", "view_list", "modify", "claim", "assign", "assignable"], "on": "complaint"},
	"com.ritense.note.domain.Note": {"actions": ["view", "view_list", "create", "modify", "delete"], "on": "part"},
	"com.ritense.documentenapi.authorization.ZgwDocument": {"actions": ["view", "view_list", "create", "modify"], "on": "part"},
	"com.ritense.valtimo.operaton.domain.OperatonExecution": {"actions": ["create"], "on": "started_on"},
	"com.ritense.case_.domain.tab.CaseWidgetTabWidget": {"actions": ["view"], "on": "started_on"},
	"com.ritense.valtimo.operaton.domain.OperatonTask": {"actions": ["view", "view_list", "claim", "complete", "assign", "assignable"], "on": "task"},
	# temporary uploads, before the file belongs to a complaint
	"com.ritense.resource.authorization.ResourcePermission": {"actions": ["view", "view_list", "create", "modify", "delete"], "on": "anything"},
}

# ---- which complaints a scope covers ----------------------------------------------------------------

# One list of conditions per alternative; a complaint is in scope when it meets all conditions of one.
complaints(scope) := [[klachten_zaaktype, json_value("content.content", dienst, "in", scope.diensten)]]

klachten_zaaktype := related("com.ritense.case_.domain.definition.CaseDefinition", [
	related("com.ritense.zakenapi.domain.ZaakTypeLink", [field("zaakTypeUrl", "==", zaaktype)]),
])

# The field that names the case definition, per resource type.
case_key := {
	"com.ritense.case_.domain.definition.CaseDefinition": "id.key",
	"com.ritense.document.domain.impl.JsonSchemaDocumentDefinition": "id.name",
	"com.ritense.document.domain.impl.searchfield.SearchField": "id.caseDefinitionKey",
}

conditions("anything", _, _, _) := [[]]

conditions("the_case", resource_type, _, _) := [[field(case_key[resource_type], "==", case_definition)]]

conditions("complaint", _, _, scope) := complaints(scope)

conditions("part", _, _, scope) := [[related(document, c)] | some c in complaints(scope)]

conditions("task", _, role, scope) := [[
	related("com.ritense.valtimo.operaton.domain.OperatonIdentityLink", [field("groupId", "==", role)]),
	related(document, c),
] | some c in complaints(scope)]

# ---- decision -------------------------------------------------------------------------------------

allow if {
	some role, scope in klachten_scopes
	has_role(role)
	some resource_type, right in klachten_rights[scope.rights]
	has_resource_type(resource_type)
	has_action(right.actions)
}

filter contains permission(role, resource_type, right.actions, c) if {
	some role, scope in klachten_scopes
	some resource_type, right in klachten_rights[scope.rights]
	has_resource_type(resource_type)
	has_action(right.actions)
	right.on != "started_on"
	some c in conditions(right.on, resource_type, role, scope)
}

filter contains context_permission(role, resource_type, right.actions, document, c) if {
	some role, scope in klachten_scopes
	some resource_type, right in klachten_rights[scope.rights]
	has_resource_type(resource_type)
	has_action(right.actions)
	right.on == "started_on"
	some c in complaints(scope)
}
