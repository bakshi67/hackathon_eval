app_name = "hackathon_eval"
app_title = "Hackathon Eval"
app_publisher = "Hackathon Admin"
app_description = "Hackathon Evaluation System for 562 Teams across 3 Levels"
app_email = "admin@hackathon.local"
app_license = "mit"

# Includes in <head>
# ------------------
app_include_js = "/assets/hackathon_eval/js/hackathon_eval.js"

# DocType JS
# ----------
doctype_js = {
	"Hackathon Team": "public/js/hackathon_team.js",
	"L2 Evaluation": "public/js/l2_evaluation.js",
}

# Permission Query Conditions
# ----------------------------
permission_query_conditions = {
	"L2 Evaluation": "hackathon_eval.permissions.get_l2_evaluation_conditions",
	"Mentor Assignment": "hackathon_eval.permissions.get_mentor_assignment_conditions",
	"L1 Review": "hackathon_eval.permissions.get_l1_review_conditions",
}

# Has Permission
# --------------
has_permission = {
	"L2 Evaluation": "hackathon_eval.permissions.has_l2_evaluation_permission",
	"Mentor Assignment": "hackathon_eval.permissions.has_mentor_assignment_permission",
	"L1 Review": "hackathon_eval.permissions.has_l1_review_permission",
}

# Fixtures to export with bench export-fixtures
# ---------------------------------------------
fixtures = [
	{
		"dt": "Role",
		"filters": [
			["name", "in", ["Hackathon Admin", "L1 Reviewer", "Mentor"]]
		],
	},
	{
		"dt": "Custom Field",
		"filters": [
			["module", "=", "Hackathon Eval"]
		],
	},
	{
		"dt": "Property Setter",
		"filters": [
			["module", "=", "Hackathon Eval"]
		],
	},
	{
		"dt": "Workspace",
		"filters": [
			["module", "=", "Hackathon Eval"]
		],
	},
]
