frappe.query_reports["Score Disagreement"] = {
	"filters": [
		{
			"fieldname": "threshold",
			"label": __("Disagreement Threshold (Max - Min >=)"),
			"fieldtype": "Float",
			"default": 20.0
		},
		{
			"fieldname": "track",
			"label": __("Track"),
			"fieldtype": "Select",
			"options": "\nWeb & Mobile\nAI/ML\nCloud & DevOps\nCybersecurity\nIoT & Hardware\nOpen Innovation\nFinTech\nHealthTech"
		}
	]
};
