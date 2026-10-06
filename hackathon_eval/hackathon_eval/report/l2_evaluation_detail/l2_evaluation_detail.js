frappe.query_reports["L2 Evaluation Detail"] = {
	"filters": [
		{
			"fieldname": "mentor",
			"label": __("Mentor"),
			"fieldtype": "Link",
			"options": "Mentor"
		},
		{
			"fieldname": "team",
			"label": __("Team"),
			"fieldtype": "Link",
			"options": "Hackathon Team"
		},
		{
			"fieldname": "track",
			"label": __("Track"),
			"fieldtype": "Select",
			"options": "\nWeb & Mobile\nAI/ML\nCloud & DevOps\nCybersecurity\nIoT & Hardware\nOpen Innovation\nFinTech\nHealthTech"
		}
	]
};
