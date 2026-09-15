package authz

import rego.v1

# ---- com.ritense.case.domain.CaseTab -------------------------------------------------------------
#
# Note the package: `case`, not `case_`, unlike CaseDefinition and CaseWidgetTabWidget below. That
# asymmetry is in the deployed rows, so it is reproduced rather than tidied.

case_tab_view_admin if {
	has_resource_type("com.ritense.case.domain.CaseTab")
	has_action(["view"])
	has_role("ROLE_ADMIN")
}

allow if case_tab_view_admin

filter contains {
	"resourceType": "com.ritense.case.domain.CaseTab",
	"actions": ["view"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
  	has_resource_type("com.ritense.case.domain.CaseTab")
  	has_action(["view"])
}

case_tab_view_user if {
	has_resource_type("com.ritense.case.domain.CaseTab")
	has_action(["view"])
	has_role("ROLE_USER")
}

allow if case_tab_view_user

filter contains {
	"resourceType": "com.ritense.case.domain.CaseTab",
	"actions": ["view"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.case.domain.CaseTab")
     	has_action(["view"])
     	}

# ---- com.ritense.case_.domain.definition.CaseDefinition -------------------------------------------

case_definition_view_admin if {
	has_resource_type("com.ritense.case_.domain.definition.CaseDefinition")
	has_action(["view", "view_list"])
	has_role("ROLE_ADMIN")
}

allow if case_definition_view_admin

filter contains {
	"resourceType": "com.ritense.case_.domain.definition.CaseDefinition",
	"actions": ["view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.case_.domain.definition.CaseDefinition")
     	has_action(["view", "view_list"])
     	}

case_definition_view_user if {
	has_resource_type("com.ritense.case_.domain.definition.CaseDefinition")
	has_action(["view", "view_list"])
	has_role("ROLE_USER")
}

allow if case_definition_view_user

filter contains {
	"resourceType": "com.ritense.case_.domain.definition.CaseDefinition",
	"actions": ["view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.case_.domain.definition.CaseDefinition")
     	has_action(["view", "view_list"])
     	}

# ---- com.ritense.case_.domain.tab.CaseWidgetTabWidget ---------------------------------------------

case_widget_tab_widget_view_admin if {
	has_resource_type("com.ritense.case_.domain.tab.CaseWidgetTabWidget")
	has_action(["view"])
	has_role("ROLE_ADMIN")
}

allow if case_widget_tab_widget_view_admin

filter contains {
	"resourceType": "com.ritense.case_.domain.tab.CaseWidgetTabWidget",
	"actions": ["view"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.case_.domain.tab.CaseWidgetTabWidget")
     	has_action(["view"])
     	}

case_widget_tab_widget_view_user if {
	has_resource_type("com.ritense.case_.domain.tab.CaseWidgetTabWidget")
	has_action(["view"])
	has_role("ROLE_USER")
}

allow if case_widget_tab_widget_view_user

filter contains {
	"resourceType": "com.ritense.case_.domain.tab.CaseWidgetTabWidget",
	"actions": ["view"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.case_.domain.tab.CaseWidgetTabWidget")
     	has_action(["view"])
     	}

# ---- com.ritense.dashboard.domain.Dashboard -------------------------------------------------------

dashboard_view_admin if {
	has_resource_type("com.ritense.dashboard.domain.Dashboard")
	has_action(["view"])
	has_role("ROLE_ADMIN")
}

allow if dashboard_view_admin

filter contains {
	"resourceType": "com.ritense.dashboard.domain.Dashboard",
	"actions": ["view"],
	"conditionContainer": {"conditions": [{
		"type": "field",
		"field": "key",
		"operator": "==",
		"value": "my_admin_dashboard",
	}]},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.dashboard.domain.Dashboard")
     	has_action(["view"])
     	}

# The row grants `view` and `view_list`; the guard, as deployed, tests `view` only.
dashboard_view_user if {
	has_resource_type("com.ritense.dashboard.domain.Dashboard")
	has_action(["view", "view_list"])
	has_role("ROLE_USER")
}

allow if dashboard_view_user

filter contains {
	"resourceType": "com.ritense.dashboard.domain.Dashboard",
	"actions": ["view", "view_list"],
	"conditionContainer": {"conditions": [{
		"type": "field",
		"field": "key",
		"operator": "==",
		"value": "user-dashboard",
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.dashboard.domain.Dashboard")
     	has_action(["view", "view_list"])
}

# ---- com.ritense.document.domain.impl.JsonSchemaDocument ------------------------------------------
#
# Six rows, five of them ROLE_USER. The `${currentUsername}` and `${currentUserTeams}` values are
# Valtimo's own placeholders, resolved by the condition when it runs against an entity — the PDP
# never looks inside `conditionContainer`, so they pass through untouched.

document_all_admin if {
	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
	has_action([
		"assign",
		"assignable",
		"claim",
		"create",
		"delete",
		"export",
		"inspect",
		"inspect_modify",
		"modify",
		"view",
		"view_list",
	])
}

allow if document_all_admin

filter contains {
	"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocument",
	"actions": [
		"assign",
		"assignable",
		"claim",
		"create",
		"delete",
		"export",
		"inspect",
		"inspect_modify",
		"modify",
		"view",
		"view_list",
	],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
     	has_action([
     		"assign",
     		"assignable",
     		"claim",
     		"create",
     		"delete",
     		"export",
     		"inspect",
     		"inspect_modify",
     		"modify",
     		"view",
     		"view_list",
     	])
     	}

# Claimable by a member of the team the case is already assigned to.
document_claim_team_user if {
	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
	has_action(["assign", "assignable", "claim"])
	has_role("ROLE_USER")
}

allow if document_claim_team_user

filter contains {
	"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocument",
	"actions": ["assign", "assignable", "claim"],
	"conditionContainer": {"conditions": [
		{
			"type": "field",
			"field": "assigneeId",
			"operator": "==",
			"value": null,
		},
		{
			"type": "field",
			"field": "assignedTeamKey",
			"operator": "==",
			"value": "${currentUserTeams}",
		},
		{
			"type": "container",
			"resourceType": "com.ritense.case_.domain.definition.CaseDefinition",
			"conditions": [{
				"type": "field",
				"field": "id.key",
				"operator": "==",
				"value": "bezwaar",
			}],
		},
	]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
     	has_action(["assign", "assignable", "claim"])
     	}

# Claimable while unassigned to any team at all. Same guard as the row above — the two rows differ
# only in their conditions, which the PDP does not read, so one condition rule would serve both.
# They are kept apart so each row still has a name of its own.
document_claim_unassigned_user if {
	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
	has_action(["assign", "assignable", "claim"])
	has_role("ROLE_USER")
}

allow if document_claim_unassigned_user

filter contains {
	"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocument",
	"actions": ["assign", "assignable", "claim"],
	"conditionContainer": {"conditions": [
		{
			"type": "field",
			"field": "assigneeId",
			"operator": "==",
			"value": null,
		},
		{
			"type": "field",
			"field": "assignedTeamKey",
			"operator": "==",
			"value": null,
		},
		{
			"type": "container",
			"resourceType": "com.ritense.case_.domain.definition.CaseDefinition",
			"conditions": [{
				"type": "field",
				"field": "id.key",
				"operator": "==",
				"value": "bezwaar",
			}],
		},
	]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
     	has_action(["assign", "assignable", "claim"])
     	}

document_create_user if {
	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
	has_action(["create"])
	has_role("ROLE_USER")
}

allow if document_create_user

filter contains {
	"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocument",
	"actions": ["create"],
	"conditionContainer": {"conditions": [{
		"type": "container",
		"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocumentDefinition",
		"conditions": [{
			"type": "field",
			"field": "id.name",
			"operator": "in",
			"value": ["leningen", "bezwaar"],
		}],
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
     	has_action(["create"])
     	}

# Viewable because the case is assigned to one of the user's teams.
document_view_team_user if {
	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
	has_action(["export", "modify", "view", "view_list"])
	has_role("ROLE_USER")
}

allow if document_view_team_user

filter contains {
	"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocument",
	"actions": ["export", "modify", "view", "view_list"],
	"conditionContainer": {"conditions": [
		{
			"type": "field",
			"field": "assignedTeamKey",
			"operator": "in",
			"value": "${currentUserTeams}",
		},
		{
			"type": "container",
			"resourceType": "com.ritense.case_.domain.definition.CaseDefinition",
			"conditions": [{
				"type": "field",
				"field": "id.key",
				"operator": "==",
				"value": "bezwaar",
			}],
		},
	]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
     	has_action(["export", "modify", "view", "view_list"])
     	}

# Viewable because the case is assigned to the user personally.
document_view_assignee_user if {
	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
	has_action(["export", "modify", "view", "view_list"])
	has_role("ROLE_USER")
}

allow if document_view_assignee_user

filter contains {
	"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocument",
	"actions": ["export", "modify", "view", "view_list"],
	"conditionContainer": {"conditions": [
		{
			"type": "field",
			"field": "assigneeId",
			"operator": "==",
			"value": "${currentUsername}",
		},
		{
			"type": "container",
			"resourceType": "com.ritense.case_.domain.definition.CaseDefinition",
			"conditions": [{
				"type": "field",
				"field": "id.key",
				"operator": "==",
				"value": "bezwaar",
			}],
		},
	]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocument")
     	has_action(["export", "modify", "view", "view_list"])
     	}

# ---- com.ritense.document.domain.impl.JsonSchemaDocumentDefinition --------------------------------

document_definition_all_admin if {
	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocumentDefinition")
	has_action(["create", "delete", "modify", "view", "view_list"])
	has_role("ROLE_ADMIN")
}

allow if document_definition_all_admin

filter contains {
	"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocumentDefinition",
	"actions": ["create", "delete", "modify", "view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocumentDefinition")
     	has_action(["create", "delete", "modify", "view", "view_list"])
     	}

document_definition_view_user if {
	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocumentDefinition")
	has_action(["view", "view_list"])
	has_role("ROLE_USER")
}

allow if document_definition_view_user

filter contains {
	"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocumentDefinition",
	"actions": ["view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.JsonSchemaDocumentDefinition")
     	has_action(["view", "view_list"])
     	}

# ---- com.ritense.document.domain.impl.searchfield.SearchField -------------------------------------

search_field_view_list_admin if {
	has_resource_type("com.ritense.document.domain.impl.searchfield.SearchField")
	has_action(["view_list"])
	has_role("ROLE_ADMIN")
}

allow if search_field_view_list_admin

filter contains {
	"resourceType": "com.ritense.document.domain.impl.searchfield.SearchField",
	"actions": ["view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.searchfield.SearchField")
     	has_action(["view_list"])
     	}

search_field_view_list_user if {
	has_resource_type("com.ritense.document.domain.impl.searchfield.SearchField")
	has_action(["view_list"])
	has_role("ROLE_USER")
}

allow if search_field_view_list_user

filter contains {
	"resourceType": "com.ritense.document.domain.impl.searchfield.SearchField",
	"actions": ["view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.searchfield.SearchField")
     	has_action(["view_list"])
     	}

# ---- com.ritense.document.domain.impl.snapshot.JsonSchemaDocumentSnapshot -------------------------
#
# ROLE_USER only. There is no ROLE_ADMIN row for snapshots in the deployed set.

document_snapshot_view_user if {
	has_resource_type("com.ritense.document.domain.impl.snapshot.JsonSchemaDocumentSnapshot")
	has_action(["view", "view_list"])
	has_role("ROLE_USER")
}

allow if document_snapshot_view_user

filter contains {
	"resourceType": "com.ritense.document.domain.impl.snapshot.JsonSchemaDocumentSnapshot",
	"actions": ["view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.document.domain.impl.snapshot.JsonSchemaDocumentSnapshot")
     	has_action(["view", "view_list"])
     	}

# ---- com.ritense.documentenapi.authorization.ZgwDocument ------------------------------------------

zgw_document_all_admin if {
	has_resource_type("com.ritense.documentenapi.authorization.ZgwDocument")
	has_action(["create", "delete", "modify", "view", "view_list"])
	has_role("ROLE_ADMIN")
}

allow if zgw_document_all_admin

filter contains {
	"resourceType": "com.ritense.documentenapi.authorization.ZgwDocument",
	"actions": ["create", "delete", "modify", "view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.documentenapi.authorization.ZgwDocument")
     	has_action(["create", "delete", "modify", "view", "view_list"])
     	}

zgw_document_bezwaar_user if {
	has_resource_type("com.ritense.documentenapi.authorization.ZgwDocument")
	has_action(["create", "delete", "modify", "view", "view_list"])
	has_role("ROLE_USER")
}

allow if zgw_document_bezwaar_user

filter contains {
	"resourceType": "com.ritense.documentenapi.authorization.ZgwDocument",
	"actions": ["create", "delete", "modify", "view", "view_list"],
	"conditionContainer": {"conditions": [{
		"type": "container",
		"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocument",
		"conditions": [{
			"type": "field",
			"field": "documentDefinitionId.caseDefinitionId.key",
			"operator": "in",
			"value": ["bezwaar"],
		}],
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.documentenapi.authorization.ZgwDocument")
     	has_action(["create", "delete", "modify", "view", "view_list"])
     	}

# ---- com.ritense.iko.domain.IkoView ---------------------------------------------------------------
#
# ROLE_ADMIN only.

iko_view_admin if {
	has_resource_type("com.ritense.iko.domain.IkoView")
	has_action(["view", "view_list"])
	has_role("ROLE_ADMIN")
}

allow if iko_view_admin

filter contains {
	"resourceType": "com.ritense.iko.domain.IkoView",
	"actions": ["view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.iko.domain.IkoView")
     	has_action(["view", "view_list"])
     	}

# ---- com.ritense.note.domain.Note -----------------------------------------------------------------
#
# The ROLE_USER rows nest a container inside a container: Note -> JsonSchemaDocument ->
# CaseDefinition, reaching the case definition key two hops from the note.

note_all_admin if {
	has_resource_type("com.ritense.note.domain.Note")
	has_action(["create", "delete", "modify", "view_list"])
	has_role("ROLE_ADMIN")
}

allow if note_all_admin

filter contains {
	"resourceType": "com.ritense.note.domain.Note",
	"actions": ["create", "delete", "modify", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.note.domain.Note")
     	has_action(["create", "delete", "modify", "view_list"])
     	}

note_create_user if {
	has_resource_type("com.ritense.note.domain.Note")
	has_action(["create", "view_list"])
	has_role("ROLE_USER")
}

allow if note_create_user

filter contains {
	"resourceType": "com.ritense.note.domain.Note",
	"actions": ["create", "view_list"],
	"conditionContainer": {"conditions": [{
		"type": "container",
		"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocument",
		"conditions": [{
			"type": "container",
			"resourceType": "com.ritense.case_.domain.definition.CaseDefinition",
			"conditions": [{
				"type": "field",
				"field": "id.key",
				"operator": "==",
				"value": "bezwaar",
			}],
		}],
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.note.domain.Note")
     	has_action(["create", "view_list"])
     	}

# Deleting or editing a note is the author's alone.
note_own_modify_user if {
	has_resource_type("com.ritense.note.domain.Note")
	has_action(["delete", "modify"])
	has_role("ROLE_USER")
}

allow if note_own_modify_user

filter contains {
	"resourceType": "com.ritense.note.domain.Note",
	"actions": ["delete", "modify"],
	"conditionContainer": {"conditions": [
		{
			"type": "field",
			"field": "createdByUserId",
			"operator": "==",
			"value": "${currentUsername}",
		},
		{
			"type": "container",
			"resourceType": "com.ritense.document.domain.impl.JsonSchemaDocument",
			"conditions": [{
				"type": "container",
				"resourceType": "com.ritense.case_.domain.definition.CaseDefinition",
				"conditions": [{
					"type": "field",
					"field": "id.key",
					"operator": "==",
					"value": "bezwaar",
				}],
			}],
		},
	]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.note.domain.Note")
     	has_action(["delete", "modify"])
     	}

# ---- com.ritense.objectenapi.security.Object ------------------------------------------------------

object_all_admin if {
	has_resource_type("com.ritense.objectenapi.security.Object")
	has_action(["create", "delete", "modify", "view", "view_list"])
	has_role("ROLE_ADMIN")
}

allow if object_all_admin

filter contains {
	"resourceType": "com.ritense.objectenapi.security.Object",
	"actions": ["create", "delete", "modify", "view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.objectenapi.security.Object")
     	has_action(["create", "delete", "modify", "view", "view_list"])
     	}

object_view_user if {
	has_resource_type("com.ritense.objectenapi.security.Object")
	has_action(["view", "view_list"])
	has_role("ROLE_USER")
}

allow if object_view_user

filter contains {
	"resourceType": "com.ritense.objectenapi.security.Object",
	"actions": ["view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.objectenapi.security.Object")
     	has_action(["view", "view_list"])
     	}

# ---- com.ritense.objectmanagement.domain.ObjectManagement -----------------------------------------

object_management_view_list_admin if {
	has_resource_type("com.ritense.objectmanagement.domain.ObjectManagement")
	has_action(["view_list"])
	has_role("ROLE_ADMIN")
}

allow if object_management_view_list_admin

filter contains {
	"resourceType": "com.ritense.objectmanagement.domain.ObjectManagement",
	"actions": ["view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.objectmanagement.domain.ObjectManagement")
     	has_action(["view_list"])
     	}

object_management_view_list_user if {
	has_resource_type("com.ritense.objectmanagement.domain.ObjectManagement")
	has_action(["view_list"])
	has_role("ROLE_USER")
}

allow if object_management_view_list_user

filter contains {
	"resourceType": "com.ritense.objectmanagement.domain.ObjectManagement",
	"actions": ["view_list"],
	"conditionContainer": {"conditions": [{
		"type": "field",
		"field": "title",
		"operator": "==",
		"value": "Bomen",
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.objectmanagement.domain.ObjectManagement")
     	has_action(["view_list"])
     	}

# ---- com.ritense.team.domain.Team -----------------------------------------------------------------
#
# `list_contains` is the mirror of `in`: the field holds the list and the value is the single item
# looked for, where `in` has it the other way round.

team_all_admin if {
	has_resource_type("com.ritense.team.domain.Team")
	has_action(["assign", "create", "delete", "modify", "view", "view_list"])
	has_role("ROLE_ADMIN")
}

allow if team_all_admin

filter contains {
	"resourceType": "com.ritense.team.domain.Team",
	"actions": ["assign", "create", "delete", "modify", "view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.team.domain.Team")
     	has_action(["assign", "create", "delete", "modify", "view", "view_list"])
     	}

team_member_user if {
	has_resource_type("com.ritense.team.domain.Team")
	has_action(["assign", "delete", "modify", "view", "view_list"])
	has_role("ROLE_USER")
}

allow if team_member_user

filter contains {
	"resourceType": "com.ritense.team.domain.Team",
	"actions": ["assign", "delete", "modify", "view", "view_list"],
	"conditionContainer": {"conditions": [{
		"type": "field",
		"field": "users",
		"operator": "list_contains",
		"value": "${currentUsername}",
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.team.domain.Team")
     	has_action(["assign", "delete", "modify", "view", "view_list"])
     	}

# ---- com.ritense.valtimo.contract.authentication.User ---------------------------------------------
#
# The rows this file's header describes. `managed_user` is the AuthZEN resource type for them; the
# `resourceType` here stays the Valtimo class, because that is the column's value.

managed_user_view_admin if {
	has_resource_type("com.ritense.valtimo.contract.authentication.User")
	has_action(["view", "view_list"])
	has_role("ROLE_ADMIN")
}

allow if managed_user_view_admin

filter contains {
	"resourceType": "com.ritense.valtimo.contract.authentication.User",
	"actions": ["view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.valtimo.contract.authentication.User")
     	has_action(["view", "view_list"])
     	}

# A plain user sees other plain users, not administrators.
#
# The guard tests ROLE_ADMIN while the row it publishes is the ROLE_USER one — carried over as it
# was written, not deliberate as far as the deployed rows go. As it stands a ROLE_USER request never
# yields this row, and a ROLE_ADMIN request yields it beside the admin row above.
managed_user_view_user if {
	has_resource_type("com.ritense.valtimo.contract.authentication.User")
	has_action(["view", "view_list"])
	has_role("ROLE_USER")
}

allow if managed_user_view_user

filter contains {
	"resourceType": "com.ritense.valtimo.contract.authentication.User",
	"actions": ["view", "view_list"],
	"conditionContainer": {"conditions": [{
		"type": "field",
		"field": "roles",
		"operator": "list_contains",
		"value": "ROLE_USER",
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if  {
     	has_resource_type("com.ritense.valtimo.contract.authentication.User")
     	has_action(["view", "view_list"])
     	}

# ---- com.ritense.valtimo.operaton.domain.OperatonExecution ----------------------------------------

operaton_execution_create_admin if {
	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonExecution")
	has_action(["create"])
	has_role("ROLE_ADMIN")
}

allow if operaton_execution_create_admin

filter contains {
	"resourceType": "com.ritense.valtimo.operaton.domain.OperatonExecution",
	"actions": ["create"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonExecution")
     	has_action(["create"])
     	}

operaton_execution_create_user if {
	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonExecution")
	has_action(["create"])
	has_role("ROLE_USER")
}

allow if operaton_execution_create_user

filter contains {
	"resourceType": "com.ritense.valtimo.operaton.domain.OperatonExecution",
	"actions": ["create"],
	"conditionContainer": {"conditions": [{
		"type": "container",
		"resourceType": "com.ritense.case_.domain.definition.CaseDefinition",
		"conditions": [{
			"type": "field",
			"field": "id.key",
			"operator": "==",
			"value": "bezwaar",
		}],
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if  {
     	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonExecution")
     	has_action(["create"])
     	}

# ---- com.ritense.valtimo.operaton.domain.OperatonTask ---------------------------------------------
#
# Five rows. `assignable` is split off from the rest for both roles, once per way a task's identity
# link can match — a candidate group naming the role, or one of the user's teams — because a
# permission's conditions are a conjunction, so two alternatives need two rows.

operaton_task_all_admin if {
	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
	has_action(["assign", "claim", "complete", "view", "view_list"])
	has_role("ROLE_ADMIN")
}

allow if operaton_task_all_admin

filter contains {
	"resourceType": "com.ritense.valtimo.operaton.domain.OperatonTask",
	"actions": ["assign", "claim", "complete", "view", "view_list"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
     	has_action(["assign", "claim", "complete", "view", "view_list"])
     	}

operaton_task_assignable_role_admin if {
	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
	has_action(["assignable"])
	has_role("ROLE_ADMIN")
}

allow if operaton_task_assignable_role_admin

filter contains {
	"resourceType": "com.ritense.valtimo.operaton.domain.OperatonTask",
	"actions": ["assignable"],
	"conditionContainer": {"conditions": [{
		"type": "container",
		"resourceType": "com.ritense.valtimo.operaton.domain.OperatonIdentityLink",
		"conditions": [{
			"type": "field",
			"field": "groupId",
			"operator": "==",
			"value": "ROLE_ADMIN",
		}],
	}]},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
     	has_action(["assignable"])
     	}

operaton_task_assignable_teams_admin if {
	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
	has_action(["assignable"])
	has_role("ROLE_ADMIN")
}

allow if operaton_task_assignable_teams_admin

filter contains {
	"resourceType": "com.ritense.valtimo.operaton.domain.OperatonTask",
	"actions": ["assignable"],
	"conditionContainer": {"conditions": [{
		"type": "container",
		"resourceType": "com.ritense.valtimo.operaton.domain.OperatonIdentityLink",
		"conditions": [{
			"type": "field",
			"field": "groupId",
			"operator": "in",
			"value": "${currentUserTeams}",
		}],
	}]},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
     	has_action(["assignable"])
     	}

operaton_task_all_role_user if {
	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
	has_action(["assign", "assignable", "claim", "complete", "view", "view_list"])
	has_role("ROLE_USER")
}

allow if operaton_task_all_role_user

filter contains {
	"resourceType": "com.ritense.valtimo.operaton.domain.OperatonTask",
	"actions": ["assign", "assignable", "claim", "complete", "view", "view_list"],
	"conditionContainer": {"conditions": [{
		"type": "container",
		"resourceType": "com.ritense.valtimo.operaton.domain.OperatonIdentityLink",
		"conditions": [{
			"type": "field",
			"field": "groupId",
			"operator": "==",
			"value": "ROLE_USER",
		}],
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
     	has_action(["assign", "assignable", "claim", "complete", "view", "view_list"])
     	}

operaton_task_all_teams_user if {
	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
	has_action(["assign", "assignable", "claim", "complete", "view", "view_list"])
	has_role("ROLE_USER")
}

allow if operaton_task_all_teams_user

filter contains {
	"resourceType": "com.ritense.valtimo.operaton.domain.OperatonTask",
	"actions": ["assign", "assignable", "claim", "complete", "view", "view_list"],
	"conditionContainer": {"conditions": [{
		"type": "container",
		"resourceType": "com.ritense.valtimo.operaton.domain.OperatonIdentityLink",
		"conditions": [{
			"type": "field",
			"field": "groupId",
			"operator": "in",
			"value": "${currentUserTeams}",
		}],
	}]},
	"role": "ROLE_USER",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTask")
     	has_action(["assign", "assignable", "claim", "complete", "view", "view_list"])
     	}

# ---- com.ritense.valtimo.operaton.domain.OperatonTimer --------------------------------------------
#
# ROLE_ADMIN only.
#
# The guard is OperatonTask's, for ROLE_USER — carried over as it was written. A `complete` request
# on an OperatonTimer therefore never yields this row, while a ROLE_USER OperatonTask request does.
operaton_timer_complete_admin if {
	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTimer")
	has_action(["complete"])
	has_role("ROLE_ADMIN")
}

allow if operaton_timer_complete_admin

filter contains {
	"resourceType": "com.ritense.valtimo.operaton.domain.OperatonTimer",
	"actions": ["complete"],
	"conditionContainer": {"conditions": []},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.valtimo.operaton.domain.OperatonTimer")
     	has_action(["complete"])
     	}

# ---- com.ritense.zakenapi.security.Zaak -----------------------------------------------------------
#
# The one row zaak-role-admin-view.rego also models, there as a `field`/`op`/`value` constraint on a
# `view_list` request. Both entries land in the same `filter` set, in their two different shapes.

zaak_view_admin if {
	has_resource_type("com.ritense.zakenapi.security.Zaak")
	has_action(["view"])
	has_role("ROLE_ADMIN")
}

allow if zaak_view_admin

filter contains {
	"resourceType": "com.ritense.zakenapi.security.Zaak",
	"actions": ["view"],
	"conditionContainer": {"conditions": [{
		"type": "field",
		"field": "zaaktype",
		"operator": "==",
		"value": "http://localhost:8001/catalogi/api/v1/zaaktypen/744ca059-f412-49d4-8963-5800e4afd486",
	}]},
	"role": "ROLE_ADMIN",
	"contextResourceType": null,
	"contextConditionContainer": {"conditions": []},
} if {
     	has_resource_type("com.ritense.zakenapi.security.Zaak")
     	has_action(["view"])
}

context := {
    "filter": sort(filter)
}
