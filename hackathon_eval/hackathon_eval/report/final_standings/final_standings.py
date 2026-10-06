# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = [
		{"label": _("Final Rank"), "fieldname": "final_rank", "fieldtype": "Int", "width": 90},
		{"label": _("Award / Standing"), "fieldname": "award", "fieldtype": "Data", "width": 190},
		{"label": _("Team Code"), "fieldname": "team_code", "fieldtype": "Link", "options": "Hackathon Team", "width": 120},
		{"label": _("Team Name"), "fieldname": "team_name", "fieldtype": "Data", "width": 200},
		{"label": _("Track"), "fieldname": "track", "fieldtype": "Data", "width": 130},
		{"label": _("L1 (/20)"), "fieldname": "l1_score", "fieldtype": "Float", "precision": 2, "width": 95},
		{"label": _("L2 Avg (/70)"), "fieldname": "l2_avg", "fieldtype": "Float", "precision": 2, "width": 105},
		{"label": _("Cumulative (/90)"), "fieldname": "cumulative_score", "fieldtype": "Float", "precision": 2, "width": 125},
		{"label": _("L3 (/10)"), "fieldname": "l3_score", "fieldtype": "Float", "precision": 2, "width": 95},
		{"label": _("Final Total (/100)"), "fieldname": "final_total", "fieldtype": "Float", "precision": 2, "width": 135},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
	]

	conditions = ["status = 'Final Selected' OR final_rank > 0"]
	params = {}

	if filters.get("track"):
		conditions.append("track = %(track)s")
		params["track"] = filters.get("track")

	where_clause = f"WHERE {' AND '.join(conditions)}"

	teams = frappe.db.sql(
		f"""
		SELECT
			final_rank,
			team_code,
			team_name,
			track,
			l1_score,
			l2_avg,
			cumulative_score,
			l3_score,
			final_total,
			status
		FROM `tabHackathon Team`
		{where_clause}
		ORDER BY
			CASE WHEN final_rank > 0 THEN final_rank ELSE 99999 END asc,
			final_total desc,
			team_code asc
		""",
		params,
		as_dict=True
	)

	podium = {
		1: "🥇 1st Place (Champion)",
		2: "🥈 2nd Place (1st Runner Up)",
		3: "🥉 3rd Place (2nd Runner Up)"
	}

	data = []
	for t in teams:
		r = t["final_rank"]
		if r and r in podium:
			t["award"] = podium[r]
		elif r and r > 0:
			t["award"] = f"Finalist (Rank {r})"
		else:
			t["award"] = "Finalist"
			t["final_rank"] = "-"
		data.append(t)

	return columns, data
