# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HackathonSettings(Document):
	def validate(self):
		self.validate_positive_values()
		self.validate_max_marks()

	def validate_positive_values(self):
		numeric_fields = {
			"l1_max_marks": _("L1 Max Marks"),
			"l2_max_marks": _("L2 Max Marks"),
			"l3_max_marks": _("L3 Max Marks"),
			"l2_criterion_max": _("L2 Criterion Max"),
			"l1_shortlist_target_min": _("L1 Shortlist Target Min"),
			"l1_shortlist_target_max": _("L1 Shortlist Target Max"),
			"regional_count": _("Regional Count"),
			"final_count": _("Final Count"),
			"winners_count": _("Winners Count"),
			"min_mentors_per_team": _("Min Mentors per Team"),
		}

		for fieldname, label in numeric_fields.items():
			val = getattr(self, fieldname, None)
			if val is None or val <= 0:
				frappe.throw(_("{0} must be a positive number greater than 0").format(label))

		if self.l1_shortlist_target_max < self.l1_shortlist_target_min:
			frappe.throw(_("L1 Shortlist Target Max cannot be less than Target Min"))

	def validate_max_marks(self):
		l1 = float(self.l1_max_marks or 0)
		l2 = float(self.l2_max_marks or 0)
		l3 = float(self.l3_max_marks or 0)
		crit_max = float(self.l2_criterion_max or 0)

		self.overall_max = round(l1 + l2 + l3, 2)
		if self.overall_max != 100.0:
			frappe.throw(
				_("Overall Max Marks (L1 + L2 + L3) must equal exactly 100. Currently: {0}").format(
					self.overall_max
				)
			)

		expected_l2 = round(7 * crit_max, 2)
		if round(l2, 2) != expected_l2:
			frappe.throw(
				_("7 x L2 Criterion Max ({0} x 7 = {1}) must equal L2 Max Marks ({2})").format(
					crit_max, expected_l2, l2
				)
			)


def get_hackathon_settings():
	"""Helper to get cached or default settings without hardcoding."""
	try:
		return frappe.get_cached_doc("Hackathon Settings")
	except Exception:
		return frappe._dict({
			"l1_max_marks": 20.0,
			"l2_max_marks": 70.0,
			"l3_max_marks": 10.0,
			"overall_max": 100.0,
			"l2_criterion_max": 10.0,
			"l1_shortlist_target_min": 250,
			"l1_shortlist_target_max": 300,
			"regional_count": 80,
			"final_count": 8,
			"winners_count": 3,
			"min_mentors_per_team": 3,
			"normalize_mentor_scores": 0,
			"scoring_locked": 0,
		})
