# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from hackathon_eval.hackathon_eval.doctype.hackathon_settings.hackathon_settings import get_hackathon_settings

CRITERIA_FIELDS = [
	"coding",
	"solution_architecture",
	"outcome",
	"future_plan",
	"innovation",
	"collaboration",
	"mentor_score",
]


class L2Evaluation(Document):
	def before_validate(self):
		user_roles = frappe.get_roles()
		is_admin = "Hackathon Admin" in user_roles or frappe.session.user == "Administrator"

		# If mentor is not admin, mentor field is linked to current user's mentor record
		if not is_admin:
			mentor_name = frappe.db.get_value("Mentor", {"user": frappe.session.user}, "name")
			if not mentor_name:
				frappe.throw(_("Current user ({0}) is not linked to any registered Mentor record.").format(frappe.session.user))
			self.mentor = mentor_name

		# Auto-link assignment if not already linked
		if self.team and self.mentor and not self.assignment:
			self.assignment = frappe.db.get_value(
				"Mentor Assignment",
				{"team": self.team, "mentor": self.mentor},
				"name"
			)

	def validate(self):
		self.validate_scoring_locked()
		self.validate_assignment_and_permissions()
		self.validate_uniqueness()
		self.validate_criteria_and_total()

	def validate_scoring_locked(self):
		settings = get_hackathon_settings()
		user_roles = frappe.get_roles()
		is_admin = "Hackathon Admin" in user_roles or frappe.session.user == "Administrator"

		if settings.scoring_locked and not is_admin:
			frappe.throw(_("Scoring is currently locked by Hackathon Admin."))

	def validate_assignment_and_permissions(self):
		user_roles = frappe.get_roles()
		is_admin = "Hackathon Admin" in user_roles or frappe.session.user == "Administrator"

		if not is_admin:
			if not self.assignment and not frappe.db.exists("Mentor Assignment", {"team": self.team, "mentor": self.mentor}):
				frappe.throw(
					_("Team {0} is not assigned to you ({1}). Mentors can only evaluate assigned teams.").format(
						self.team, self.mentor
					)
				)

	def validate_uniqueness(self):
		existing = frappe.db.get_value(
			"L2 Evaluation",
			{
				"team": self.team,
				"mentor": self.mentor,
				"docstatus": ["<", 2],
				"name": ["!=", self.name or ""]
			},
			"name"
		)
		if existing:
			frappe.throw(
				_("An evaluation for team {0} by mentor {1} already exists ({2}). Only one evaluation per pair is permitted.").format(
					self.team, self.mentor, existing
				)
			)

	def validate_criteria_and_total(self):
		settings = get_hackathon_settings()
		criterion_max = float(settings.l2_criterion_max or 10.0)

		total_marks = 0.0
		for field in CRITERIA_FIELDS:
			val = getattr(self, field, None)
			if val is None:
				frappe.throw(_("{0} is required").format(field.replace("_", " ").title()))
			val = float(val)
			if val < 0.0 or val > criterion_max:
				frappe.throw(
					_("{0} must be between 0 and {1} (provided: {2})").format(
						field.replace("_", " ").title(), criterion_max, val
					)
				)
			total_marks += val

		self.total = round(total_marks, 2)

	def on_submit(self):
		# Update Mentor Assignment status to Scored
		if self.assignment:
			frappe.db.set_value("Mentor Assignment", self.assignment, "status", "Scored")
		elif self.team and self.mentor:
			assign = frappe.db.get_value("Mentor Assignment", {"team": self.team, "mentor": self.mentor}, "name")
			if assign:
				frappe.db.set_value("Mentor Assignment", assign, "status", "Scored")

		# Update Team status if it was L1 Shortlisted
		team_status = frappe.db.get_value("Hackathon Team", self.team, "status")
		if team_status in ["Enrolled", "L1 Shortlisted"]:
			frappe.db.set_value("Hackathon Team", self.team, "status", "L2 Evaluated")

		self.trigger_recompute()

	def on_cancel(self):
		user_roles = frappe.get_roles()
		is_admin = "Hackathon Admin" in user_roles or frappe.session.user == "Administrator"
		if not is_admin:
			frappe.throw(_("Only Hackathon Admin can cancel or amend an L2 Evaluation."))

		# Revert Mentor Assignment status to Assigned
		if self.assignment:
			frappe.db.set_value("Mentor Assignment", self.assignment, "status", "Assigned")
		elif self.team and self.mentor:
			assign = frappe.db.get_value("Mentor Assignment", {"team": self.team, "mentor": self.mentor}, "name")
			if assign:
				frappe.db.set_value("Mentor Assignment", assign, "status", "Assigned")

		self.trigger_recompute()

	def trigger_recompute(self):
		from hackathon_eval.api import recompute_l2
		recompute_l2(team=self.team)
