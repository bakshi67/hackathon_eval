frappe.query_reports["Leaderboard"] = {
	"filters": [
		{
			"fieldname": "track",
			"label": __("Track"),
			"fieldtype": "Select",
			"options": "\nWeb & Mobile\nAI/ML\nCloud & DevOps\nCybersecurity\nIoT & Hardware\nOpen Innovation\nFinTech\nHealthTech"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nEnrolled\nL1 Shortlisted\nL1 Eliminated\nL2 Evaluated\nRegional Selected\nFinal Selected\nNot Selected"
		}
	]
};
