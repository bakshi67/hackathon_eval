# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = [
		{"label": _("Rank"), "fieldname": "l2_rank", "fieldtype": "Int", "width": 80},
		{"label": _("Team Code"), "fieldname": "team_code", "fieldtype": "Link", "options": "Hackathon Team", "width": 120},
		{"label": _("Team Name"), "fieldname": "team_name", "fieldtype": "Data", "width": 200},
		{"label": _("Track"), "fieldname": "track", "fieldtype": "Data", "width": 130},
		{"label": _("L1 Score (/20)"), "fieldname": "l1_score", "fieldtype": "Float", "precision": 2, "width": 120},
		{"label": _("L2 Avg (/70)"), "fieldname": "l2_avg", "fieldtype": "Float", "precision": 2, "width": 120},
		{"label": _("Cumulative (/90)"), "fieldname": "cumulative_score", "fieldtype": "Float", "precision": 2, "width": 140},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 140},
	]

	conditions = []
	params = {}

	if filters.get("track"):
		conditions.append("track = %(track)s")
		params["track"] = filters.get("track")

	if filters.get("status"):
		conditions.append("status = %(status)s")
		params["status"] = filters.get("status")

	where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

	data = frappe.db.sql(
		f"""
		SELECT
			CASE WHEN l2_rank > 0 THEN l2_rank ELSE '-' END as l2_rank,
			team_code,
			team_name,
			track,
			l1_score,
			l2_avg,
			cumulative_score,
			status
		FROM `tabHackathon Team`
		{where_clause}
		ORDER BY
			CASE WHEN l2_rank > 0 THEN l2_rank ELSE 99999 END asc,
			cumulative_score desc,
			team_code asc
		""",
		params,
		as_dict=True
	)

	return columns, data
