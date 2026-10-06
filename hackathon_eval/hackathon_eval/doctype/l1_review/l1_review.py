# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from hackathon_eval.hackathon_eval.doctype.hackathon_settings.hackathon_settings import get_hackathon_settings


class L1Review(Document):
	def before_validate(self):
		if not self.reviewer:
			self.reviewer = frappe.session.user

	def validate(self):
		self.validate_scoring_locked()
		self.validate_uniqueness()
		self.validate_score()

	def validate_scoring_locked(self):
		settings = get_hackathon_settings()
		if settings.scoring_locked and not frappe.has_permission("Hackathon Settings", "write"):
			frappe.throw(_("Scoring is currently locked by Hackathon Admin."))

	def validate_uniqueness(self):
		existing = frappe.db.get_value(
			"L1 Review",
			{
				"team": self.team,
				"reviewer": self.reviewer,
				"docstatus": ["<", 2],
				"name": ["!=", self.name or ""]
			},
			"name"
		)
		if existing:
			frappe.throw(
				_("Reviewer {0} has already submitted or drafted an L1 Review for team {1} (Review: {2})").format(
					self.reviewer, self.team, existing
				)
			)

	def validate_score(self):
		settings = get_hackathon_settings()
		l1_max = float(settings.l1_max_marks or 20.0)

		if self.score is None:
			frappe.throw(_("Score is required"))

		val = float(self.score)
		if val < 0.0 or val > l1_max:
			frappe.throw(
				_("L1 Presentation Score must be between 0 and {0} (provided: {1})").format(
					l1_max, val
				)
			)

	def on_submit(self):
		self.recompute_team_l1()

	def on_cancel(self):
		self.recompute_team_l1()

	def recompute_team_l1(self):
		if not self.team:
			return

		# Average of submitted reviews (docstatus == 1)
		avg_score = frappe.db.sql(
			"""
			SELECT AVG(score) FROM `tabL1 Review`
			WHERE team = %s AND docstatus = 1
			""",
			(self.team,)
		)[0][0]

		l1_score = round(float(avg_score or 0.0), 2)
		team_doc = frappe.get_doc("Hackathon Team", self.team)
		team_doc.l1_score = l1_score

		# Recompute cumulative & final
		l2_component = float(
			team_doc.l2_normalized_avg
			if (team_doc.l2_normalized_avg and get_hackathon_settings().normalize_mentor_scores)
			else (team_doc.l2_avg or 0.0)
		)
		team_doc.cumulative_score = round(l1_score + l2_component, 2)
		team_doc.final_total = round(team_doc.cumulative_score + float(team_doc.l3_score or 0.0), 2)

		team_doc.flags.ignore_permissions = True
		team_doc.save(ignore_permissions=True)
