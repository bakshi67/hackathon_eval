# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	# Fetch all mentors
	mentor_filters = {}
	if filters.get("mentor"):
		mentor_filters["name"] = filters.get("mentor")

	mentors = frappe.get_all(
		"Mentor",
		filters=mentor_filters,
		fields=["name", "full_name"],
		order_by="name asc"
	)

	# Build columns
	columns = [
		{"label": _("Team Code"), "fieldname": "team_code", "fieldtype": "Link", "options": "Hackathon Team", "width": 120},
		{"label": _("Team Name"), "fieldname": "team_name", "fieldtype": "Data", "width": 180},
		{"label": _("Track"), "fieldname": "track", "fieldtype": "Data", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
	]

	# One column per mentor
	for m in mentors:
		label = m.full_name or m.name
		columns.append({
			"label": label,
			"fieldname": f"mentor_{frappe.scrub(m.name)}",
			"fieldtype": "Float",
			"precision": 2,
			"width": 110
		})

	columns.append({"label": _("Reviews"), "fieldname": "reviews_count", "fieldtype": "Int", "width": 90})
	columns.append({"label": _("Average (/70)"), "fieldname": "average_score", "fieldtype": "Float", "precision": 2, "width": 120})

	# Fetch Teams according to filters
	team_filters = {}
	if filters.get("track"):
		team_filters["track"] = filters.get("track")
	if filters.get("status"):
		team_filters["status"] = filters.get("status")

	teams = frappe.get_all(
		"Hackathon Team",
		filters=team_filters,
		fields=["name", "team_code", "team_name", "track", "status"],
		order_by="team_code asc"
	)

	# Fetch submitted evaluations
	eval_filters = {"docstatus": 1}
	if filters.get("mentor"):
		eval_filters["mentor"] = filters.get("mentor")

	evaluations = frappe.get_all(
		"L2 Evaluation",
		filters=eval_filters,
		fields=["team", "mentor", "total"]
	)

	# Map: team -> {mentor: total}
	eval_map = {}
	for e in evaluations:
		eval_map.setdefault(e.team, {})[e.mentor] = float(e.total or 0.0)

	data = []
	for t in teams:
		row = {
			"team_code": t.team_code,
			"team_name": t.team_name,
			"track": t.track,
			"status": t.status,
		}
		t_evals = eval_map.get(t.name, {})

		# Only include team if mentor filter matched or not filtered
		if filters.get("mentor") and filters.get("mentor") not in t_evals:
			continue

		scores = []
		for m in mentors:
			col_key = f"mentor_{frappe.scrub(m.name)}"
			if m.name in t_evals:
				score = t_evals[m.name]
				row[col_key] = score
				scores.append(score)
			else:
				row[col_key] = None  # Blank in matrix

		review_count = len(scores)
		row["reviews_count"] = review_count
		row["average_score"] = round(sum(scores) / review_count, 2) if review_count > 0 else 0.0

		data.append(row)

	# Sort by average score descending
	data.sort(key=lambda x: -x["average_score"])

	return columns, data
