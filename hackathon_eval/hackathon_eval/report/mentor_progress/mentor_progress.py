# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = [
		{"label": _("Mentor"), "fieldname": "mentor", "fieldtype": "Link", "options": "Mentor", "width": 150},
		{"label": _("Mentor Name"), "fieldname": "full_name", "fieldtype": "Data", "width": 180},
		{"label": _("Assigned Teams"), "fieldname": "assigned_count", "fieldtype": "Int", "width": 120},
		{"label": _("Submitted"), "fieldname": "submitted_count", "fieldtype": "Int", "width": 110},
		{"label": _("Pending"), "fieldname": "pending_count", "fieldtype": "Int", "width": 100},
		{"label": _("Completion %"), "fieldname": "completion_pct", "fieldtype": "Percent", "width": 120},
		{"label": _("Last Submission"), "fieldname": "last_submission_time", "fieldtype": "Datetime", "width": 170},
	]

	user_roles = frappe.get_roles()
	is_admin = "Hackathon Admin" in user_roles or frappe.session.user == "Administrator" or "System Manager" in user_roles

	mentor_filters = {}
	if not is_admin and "Mentor" in user_roles:
		current_mentor = frappe.db.get_value("Mentor", {"user": frappe.session.user}, "name")
		mentor_filters["name"] = current_mentor or ""
	elif filters.get("mentor"):
		mentor_filters["name"] = filters.get("mentor")

	mentors = frappe.get_all(
		"Mentor",
		filters=mentor_filters,
		fields=["name", "full_name"],
		order_by="name asc"
	)

	data = []
	for m in mentors:
		# Assigned count
		assigned_count = frappe.db.count("Mentor Assignment", {"mentor": m.name})

		# Submitted evaluations (docstatus = 1)
		submitted_evals = frappe.get_all(
			"L2 Evaluation",
			filters={"mentor": m.name, "docstatus": 1},
			fields=["name", "modified"],
			order_by="modified desc"
		)
		submitted_count = len(submitted_evals)
		pending_count = max(0, assigned_count - submitted_count)
		completion_pct = round((submitted_count / assigned_count * 100), 1) if assigned_count > 0 else 0.0
		last_sub = submitted_evals[0]["modified"] if submitted_evals else None

		data.append({
			"mentor": m.name,
			"full_name": m.full_name or m.name,
			"assigned_count": assigned_count,
			"submitted_count": submitted_count,
			"pending_count": pending_count,
			"completion_pct": completion_pct,
			"last_submission_time": last_sub
		})

	data.sort(key=lambda x: -x["completion_pct"])

	return columns, data
