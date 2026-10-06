# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MentorAssignment(Document):
	def validate(self):
		self.validate_uniqueness()
		self.validate_conflicts()
		self.validate_max_teams()

	def validate_uniqueness(self):
		existing = frappe.db.get_value(
			"Mentor Assignment",
			{"team": self.team, "mentor": self.mentor, "name": ["!=", self.name or ""]},
			"name"
		)
		if existing:
			frappe.throw(
				_("Team {0} is already assigned to Mentor {1} (Assignment: {2})").format(
					self.team, self.mentor, existing
				)
			)

	def validate_conflicts(self):
		if not self.mentor or not self.team:
			return

		mentor_doc = frappe.get_doc("Mentor", self.mentor)
		conflict_teams = [c.team for c in mentor_doc.conflicts if c.team]
		if self.team in conflict_teams:
			conflict_reason = next((c.reason for c in mentor_doc.conflicts if c.team == self.team), "")
			frappe.throw(
				_("Conflict of interest: Mentor {0} has a registered conflict with team {1}. {2}").format(
					self.mentor, self.team, f"Reason: {conflict_reason}" if conflict_reason else ""
				)
			)

	def validate_max_teams(self):
		if not self.mentor:
			return

		mentor_doc = frappe.get_doc("Mentor", self.mentor)
		max_allowed = mentor_doc.max_teams or 0
		if max_allowed > 0:
			current_count = frappe.db.count(
				"Mentor Assignment",
				{"mentor": self.mentor, "name": ["!=", self.name or ""]}
			)
			if current_count >= max_allowed:
				frappe.throw(
					_("Mentor {0} has already reached the maximum team limit of {1}").format(
						self.mentor, max_allowed
					)
				)
