# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from hackathon_eval.hackathon_eval.doctype.hackathon_settings.hackathon_settings import get_hackathon_settings


class HackathonTeam(Document):
	def validate(self):
		self.validate_team_code()
		self.validate_l3_score()
		self.compute_totals()

	def validate_team_code(self):
		if not self.team_code:
			frappe.throw(_("Team Code is required"))
		self.team_code = self.team_code.strip()

	def validate_l3_score(self):
		settings = get_hackathon_settings()
		l3_max = float(settings.l3_max_marks or 10.0)

		if self.l3_score is not None:
			val = float(self.l3_score)
			if val < 0 or val > l3_max:
				frappe.throw(_("L3 Score must be between 0 and {0} (provided: {1})").format(l3_max, val))

	def compute_totals(self):
		# Recompute cumulative if needed
		l1 = float(self.l1_score or 0.0)
		l2 = float(self.l2_normalized_avg if (getattr(self, "l2_normalized_avg", 0) and get_hackathon_settings().normalize_mentor_scores) else (self.l2_avg or 0.0))
		# If cumulative not set, set it
		if not self.cumulative_score:
			self.cumulative_score = round(l1 + l2, 2)

		l3 = float(self.l3_score or 0.0)
		self.final_total = round((self.cumulative_score or 0.0) + l3, 2)
