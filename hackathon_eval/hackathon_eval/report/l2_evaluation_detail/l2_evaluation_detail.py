# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = [
		{"label": _("Mentor"), "fieldname": "mentor", "fieldtype": "Link", "options": "Mentor", "width": 140},
		{"label": _("Team Code"), "fieldname": "team_code", "fieldtype": "Link", "options": "Hackathon Team", "width": 110},
		{"label": _("Team Name"), "fieldname": "team_name", "fieldtype": "Data", "width": 170},
		{"label": _("Track"), "fieldname": "track", "fieldtype": "Data", "width": 120},
		{"label": _("Coding"), "fieldname": "coding", "fieldtype": "Float", "precision": 1, "width": 80},
		{"label": _("Architecture"), "fieldname": "solution_architecture", "fieldtype": "Float", "precision": 1, "width": 100},
		{"label": _("Outcome"), "fieldname": "outcome", "fieldtype": "Float", "precision": 1, "width": 80},
		{"label": _("Future Plan"), "fieldname": "future_plan", "fieldtype": "Float", "precision": 1, "width": 95},
		{"label": _("Innovation"), "fieldname": "innovation", "fieldtype": "Float", "precision": 1, "width": 90},
		{"label": _("Collaboration"), "fieldname": "collaboration", "fieldtype": "Float", "precision": 1, "width": 105},
		{"label": _("Mentor Score"), "fieldname": "mentor_score", "fieldtype": "Float", "precision": 1, "width": 105},
		{"label": _("Total (/70)"), "fieldname": "total", "fieldtype": "Float", "precision": 2, "width": 95},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 200},
	]

	conditions = ["e.docstatus = 1"]
	params = {}

	if filters.get("mentor"):
		conditions.append("e.mentor = %(mentor)s")
		params["mentor"] = filters.get("mentor")

	if filters.get("team"):
		conditions.append("e.team = %(team)s")
		params["team"] = filters.get("team")

	if filters.get("track"):
		conditions.append("t.track = %(track)s")
		params["track"] = filters.get("track")

	# Mentor permission condition if session user is mentor
	user_roles = frappe.get_roles()
	is_admin = "Hackathon Admin" in user_roles or frappe.session.user == "Administrator" or "System Manager" in user_roles
	if not is_admin and "Mentor" in user_roles:
		current_mentor = frappe.db.get_value("Mentor", {"user": frappe.session.user}, "name")
		conditions.append("e.mentor = %(current_mentor)s")
		params["current_mentor"] = current_mentor or ""

	where_clause = " AND ".join(conditions)

	data = frappe.db.sql(
		f"""
		SELECT
			e.mentor,
			t.team_code,
			t.team_name,
			t.track,
			e.coding,
			e.solution_architecture,
			e.outcome,
			e.future_plan,
			e.innovation,
			e.collaboration,
			e.mentor_score,
			e.total,
			e.remarks
		FROM `tabL2 Evaluation` e
		JOIN `tabHackathon Team` t ON e.team = t.name
		WHERE {where_clause}
		ORDER BY e.mentor asc, e.total desc
		""",
		params,
		as_dict=True
	)

	return columns, data
