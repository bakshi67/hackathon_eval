# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	threshold = float(filters.get("threshold") or 20.0)

	columns = [
		{"label": _("Team Code"), "fieldname": "team_code", "fieldtype": "Link", "options": "Hackathon Team", "width": 120},
		{"label": _("Team Name"), "fieldname": "team_name", "fieldtype": "Data", "width": 180},
		{"label": _("Track"), "fieldname": "track", "fieldtype": "Data", "width": 130},
		{"label": _("Evaluations"), "fieldname": "review_count", "fieldtype": "Int", "width": 90},
		{"label": _("Min Score (/70)"), "fieldname": "min_score", "fieldtype": "Float", "precision": 2, "width": 110},
		{"label": _("Max Score (/70)"), "fieldname": "max_score", "fieldtype": "Float", "precision": 2, "width": 110},
		{"label": _("Disagreement Delta"), "fieldname": "delta", "fieldtype": "Float", "precision": 2, "width": 140},
		{"label": _("Average (/70)"), "fieldname": "avg_score", "fieldtype": "Float", "precision": 2, "width": 110},
		{"label": _("Score Breakdown"), "fieldname": "breakdown", "fieldtype": "Data", "width": 260},
	]

	eval_filters = {"docstatus": 1}
	evals = frappe.get_all(
		"L2 Evaluation",
		filters=eval_filters,
		fields=["team", "mentor", "total"]
	)

	# Group by team
	team_evals = {}
	for e in evals:
		team_evals.setdefault(e.team, []).append((e.mentor, float(e.total or 0.0)))

	team_filters = {}
	if filters.get("track"):
		team_filters["track"] = filters.get("track")

	teams = frappe.get_all(
		"Hackathon Team",
		filters=team_filters,
		fields=["name", "team_code", "team_name", "track"]
	)

	data = []
	for t in teams:
		scores_tuples = team_evals.get(t.name, [])
		if len(scores_tuples) < 2:
			continue  # Need at least 2 evaluations to measure disagreement

		score_values = [st[1] for st in scores_tuples]
		min_s = min(score_values)
		max_s = max(score_values)
		delta = round(max_s - min_s, 2)

		if delta >= threshold:
			breakdown = ", ".join([f"{st[0]}: {st[1]}" for st in scores_tuples])
			avg_s = round(sum(score_values) / len(score_values), 2)
			data.append({
				"team_code": t.team_code,
				"team_name": t.team_name,
				"track": t.track,
				"review_count": len(scores_tuples),
				"min_score": min_s,
				"max_score": max_s,
				"delta": delta,
				"avg_score": avg_s,
				"breakdown": breakdown
			})

	# Sort by delta descending
	data.sort(key=lambda x: -x["delta"])

	return columns, data
