# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Add composite indexes on (team, mentor) for high performance."""
	try:
		frappe.db.add_index("Mentor Assignment", ["team", "mentor"], "idx_assignment_team_mentor")
	except Exception:
		pass

	try:
		frappe.db.add_index("L2 Evaluation", ["team", "mentor"], "idx_evaluation_team_mentor")
	except Exception:
		pass
