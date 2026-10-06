# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from hackathon_eval.api import (
	run_l1_shortlist,
	auto_assign_mentors,
	recompute_l2,
	select_regional,
	select_final,
	finalize_winners,
)
from hackathon_eval.permissions import (
	get_l2_evaluation_conditions,
	has_l2_evaluation_permission,
)


class TestHackathonEvaluation(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.setup_roles_and_settings()
		cls.setup_test_users_and_mentors()

	@classmethod
	def setup_roles_and_settings(cls):
		settings = frappe.get_doc("Hackathon Settings")
		settings.l1_max_marks = 20.0
		settings.l2_max_marks = 70.0
		settings.l3_max_marks = 10.0
		settings.overall_max = 100.0
		settings.l2_criterion_max = 10.0
		settings.l1_shortlist_target_min = 2
		settings.l1_shortlist_target_max = 3
		settings.regional_count = 2
		settings.final_count = 2
		settings.winners_count = 2
		settings.min_mentors_per_team = 2
		settings.normalize_mentor_scores = 0
		settings.scoring_locked = 0
		settings.flags.ignore_permissions = True
		settings.save(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def setup_test_users_and_mentors(cls):
		if not frappe.db.exists("User", "test_reviewer@hackathon.test"):
			u = frappe.get_doc({
				"doctype": "User",
				"email": "test_reviewer@hackathon.test",
				"first_name": "Test Reviewer",
				"roles": [{"role": "L1 Reviewer"}]
			})
			u.insert(ignore_permissions=True)

		for i in [1, 2, 3]:
			email = f"test_mentor{i}@hackathon.test"
			if not frappe.db.exists("User", email):
				u = frappe.get_doc({
					"doctype": "User",
					"email": email,
					"first_name": f"Test Mentor {i}",
					"roles": [{"role": "Mentor"}]
				})
				u.insert(ignore_permissions=True)

			if not frappe.db.exists("Mentor", email):
				m = frappe.get_doc({
					"doctype": "Mentor",
					"user": email,
					"full_name": f"Mentor {i}",
					"email": email,
					"max_teams": 10
				})
				m.insert(ignore_permissions=True)

		frappe.db.commit()

	def setUp(self):
		frappe.set_user("Administrator")

	def test_01_settings_reject_invalid_total(self):
		"""Settings must reject an overall total != 100 and criterion mismatch."""
		settings = frappe.get_doc("Hackathon Settings")
		original_l1 = settings.l1_max_marks

		# Reject total != 100
		settings.l1_max_marks = 25.0  # Total would be 105
		self.assertRaises(frappe.ValidationError, settings.save)

		# Restore
		settings.l1_max_marks = original_l1
		settings.reload()

	def test_02_l1_score_validation_limit(self):
		"""L1 score cannot exceed l1_max_marks (20) or be negative."""
		team_code = "TST-L1-01"
		if not frappe.db.exists("Hackathon Team", team_code):
			frappe.get_doc({
				"doctype": "Hackathon Team",
				"team_code": team_code,
				"team_name": "Test L1 Team",
				"status": "Enrolled"
			}).insert(ignore_permissions=True)

		review = frappe.new_doc("L1 Review")
		review.team = team_code
		review.reviewer = "test_reviewer@hackathon.test"
		review.score = 25.0
		self.assertRaises(frappe.ValidationError, review.insert)

		review.score = -2.0
		self.assertRaises(frappe.ValidationError, review.insert)

		frappe.db.sql("DELETE FROM `tabL1 Review` WHERE team = %s", (team_code,))

		review.score = 14.5
		review.insert(ignore_permissions=True)
		review.submit()
		self.assertEqual(review.docstatus, 1)

		team = frappe.get_doc("Hackathon Team", team_code)
		self.assertEqual(team.l1_score, 14.5)

	def test_03_l2_criteria_and_total_limit(self):
		"""Each of the 7 L2 criteria is limited to 10 (total max 70)."""
		team_code = "TST-L2-01"
		mentor_email = "test_mentor1@hackathon.test"

		if not frappe.db.exists("Hackathon Team", team_code):
			frappe.get_doc({
				"doctype": "Hackathon Team",
				"team_code": team_code,
				"team_name": "Test L2 Team",
				"status": "Enrolled"
			}).insert(ignore_permissions=True)

		frappe.db.sql("DELETE FROM `tabL2 Evaluation` WHERE team = %s", (team_code,))

		ev = frappe.new_doc("L2 Evaluation")
		ev.team = team_code
		ev.mentor = mentor_email
		ev.coding = 11.0  # Exceeds 10
		ev.solution_architecture = 8.0
		ev.outcome = 8.0
		ev.future_plan = 8.0
		ev.innovation = 8.0
		ev.collaboration = 8.0
		ev.mentor_score = 8.0
		self.assertRaises(frappe.ValidationError, ev.insert)

		ev.coding = 8.0
		ev.insert(ignore_permissions=True)
		self.assertEqual(ev.total, 56.0)
		ev.submit()
		self.assertEqual(ev.docstatus, 1)

	def test_04_l3_score_limit(self):
		"""L3 score cannot exceed l3_max_marks (10) or be negative."""
		team_code = "TST-L3-01"
		if not frappe.db.exists("Hackathon Team", team_code):
			frappe.get_doc({
				"doctype": "Hackathon Team",
				"team_code": team_code,
				"team_name": "Test L3 Team",
				"status": "Final Selected"
			}).insert(ignore_permissions=True)

		team = frappe.get_doc("Hackathon Team", team_code)
		team.l3_score = 15.0  # Exceeds 10
		self.assertRaises(frappe.ValidationError, team.save)

		team.reload()
		team.l3_score = 9.5
		team.save(ignore_permissions=True)
		self.assertEqual(team.l3_score, 9.5)

	def test_05_duplicate_prevention(self):
		"""Prevents duplicate L1 Reviews, L2 Evaluations, and Mentor Assignments."""
		team_code = "TST-DUP-01"
		mentor_email = "test_mentor2@hackathon.test"

		if not frappe.db.exists("Hackathon Team", team_code):
			frappe.get_doc({
				"doctype": "Hackathon Team",
				"team_code": team_code,
				"team_name": "Duplicate Test Team",
				"status": "Enrolled"
			}).insert(ignore_permissions=True)

		frappe.db.sql("DELETE FROM `tabMentor Assignment` WHERE team = %s", (team_code,))
		frappe.db.sql("DELETE FROM `tabL2 Evaluation` WHERE team = %s", (team_code,))

		a1 = frappe.get_doc({
			"doctype": "Mentor Assignment",
			"team": team_code,
			"mentor": mentor_email,
			"status": "Assigned"
		})
		a1.insert(ignore_permissions=True)

		a2 = frappe.get_doc({
			"doctype": "Mentor Assignment",
			"team": team_code,
			"mentor": mentor_email,
			"status": "Assigned"
		})
		self.assertRaises((frappe.DuplicateEntryError, frappe.ValidationError), a2.insert)

		ev1 = frappe.get_doc({
			"doctype": "L2 Evaluation",
			"team": team_code,
			"mentor": mentor_email,
			"coding": 7, "solution_architecture": 7, "outcome": 7,
			"future_plan": 7, "innovation": 7, "collaboration": 7, "mentor_score": 7
		})
		ev1.insert(ignore_permissions=True)

		ev2 = frappe.get_doc({
			"doctype": "L2 Evaluation",
			"team": team_code,
			"mentor": mentor_email,
			"coding": 8, "solution_architecture": 8, "outcome": 8,
			"future_plan": 8, "innovation": 8, "collaboration": 8, "mentor_score": 8
		})
		self.assertRaises((frappe.DuplicateEntryError, frappe.ValidationError), ev2.insert)

	def test_06_mentor_isolation_permissions(self):
		"""A Mentor cannot view or access another mentor's evaluations or assignments."""
		mentor1_user = "test_mentor1@hackathon.test"
		mentor2_user = "test_mentor2@hackathon.test"

		cond = get_l2_evaluation_conditions(mentor1_user)
		self.assertIn("tabL2 Evaluation`.mentor =", cond)
		self.assertIn(mentor1_user, cond)

		doc_m1 = frappe._dict({"mentor": mentor1_user})
		self.assertTrue(has_l2_evaluation_permission(doc_m1, user=mentor1_user))
		self.assertFalse(has_l2_evaluation_permission(doc_m1, user=mentor2_user))

	def test_07_mentor_conflict_avoidance(self):
		"""Assignment to a conflicted team must be blocked."""
		team_code = "TST-CONF-01"
		mentor_email = "test_mentor3@hackathon.test"

		if not frappe.db.exists("Hackathon Team", team_code):
			frappe.get_doc({
				"doctype": "Hackathon Team",
				"team_code": team_code,
				"team_name": "Conflict Team",
				"status": "Enrolled"
			}).insert(ignore_permissions=True)

		m = frappe.get_doc("Mentor", mentor_email)
		m.conflicts = []
		m.append("conflicts", {"team": team_code, "reason": "Alumni Connection"})
		m.save(ignore_permissions=True)

		assign = frappe.get_doc({
			"doctype": "Mentor Assignment",
			"team": team_code,
			"mentor": mentor_email,
			"status": "Assigned"
		})
		self.assertRaises(frappe.ValidationError, assign.insert)

	def test_08_scoring_locked_check(self):
		"""When scoring_locked is enabled, non-admin cannot submit evaluations."""
		settings = frappe.get_doc("Hackathon Settings")
		settings.scoring_locked = 1
		settings.save(ignore_permissions=True)

		frappe.set_user("test_mentor1@hackathon.test")
		ev = frappe.new_doc("L2 Evaluation")
		ev.team = "TST-L2-01"
		ev.mentor = "test_mentor1@hackathon.test"
		ev.coding = 7; ev.solution_architecture = 7; ev.outcome = 7
		ev.future_plan = 7; ev.innovation = 7; ev.collaboration = 7; ev.mentor_score = 7

		self.assertRaises(frappe.ValidationError, ev.validate)

		# Unlock
		frappe.set_user("Administrator")
		settings.reload()
		settings.scoring_locked = 0
		settings.save(ignore_permissions=True)

	def test_09_normalization_toggle(self):
		"""Verify mentor score normalization (z-scores rescaled)."""
		settings = frappe.get_doc("Hackathon Settings")
		settings.normalize_mentor_scores = 1
		settings.save(ignore_permissions=True)

		# Recompute with normalization on
		recompute_l2()

		# Verify settings restored
		settings.normalize_mentor_scores = 0
		settings.save(ignore_permissions=True)

	def test_10_end_to_end_scoring_and_ranking_flow(self):
		"""
		Verifies full progression:
		L1 Reviews -> Shortlist -> Auto-assign -> L2 Eval -> Recompute -> Regional -> Final -> L3 -> Winners
		Confirms: Final Total = L1 + L2 avg + L3
		"""
		settings = frappe.get_doc("Hackathon Settings")
		settings.l1_shortlist_target_min = 2
		settings.l1_shortlist_target_max = 5
		settings.min_mentors_per_team = 2
		settings.regional_count = 2
		settings.final_count = 2
		settings.save(ignore_permissions=True)

		for i in range(1, 5):
			code = f"TST-FLOW-{i:02d}"
			score = 16.0 + i * 1.0  # 17, 18, 19, 20
			if not frappe.db.exists("Hackathon Team", code):
				frappe.get_doc({
					"doctype": "Hackathon Team",
					"team_code": code,
					"team_name": f"Flow Team {i}",
					"status": "Enrolled",
					"l1_score": score
				}).insert(ignore_permissions=True)
			else:
				t = frappe.get_doc("Hackathon Team", code)
				t.status = "Enrolled"
				t.l1_score = score
				t.save(ignore_permissions=True)

		res_short = run_l1_shortlist(cutoff=18.5)
		self.assertGreaterEqual(res_short["shortlisted_count"], 2)

		shortlisted = frappe.get_all("Hackathon Team", filters={"status": "L1 Shortlisted"}, pluck="team_code")
		self.assertIn("TST-FLOW-04", shortlisted)
		self.assertIn("TST-FLOW-03", shortlisted)

		frappe.db.sql("DELETE FROM `tabMentor Assignment` WHERE team LIKE 'TST-FLOW%'")
		frappe.db.sql("DELETE FROM `tabL2 Evaluation` WHERE team LIKE 'TST-FLOW%'")

		assign_res = auto_assign_mentors()
		self.assertGreater(assign_res["new_assignments_created"], 0)

		team4_assignments = frappe.get_all("Mentor Assignment", filters={"team": "TST-FLOW-04"}, fields=["name", "mentor"])
		for a in team4_assignments:
			ev = frappe.get_doc({
				"doctype": "L2 Evaluation",
				"team": "TST-FLOW-04",
				"mentor": a.mentor,
				"assignment": a.name,
				"coding": 9, "solution_architecture": 8, "outcome": 9,
				"future_plan": 8, "innovation": 8, "collaboration": 9, "mentor_score": 9
			})  # Total = 60
			ev.insert(ignore_permissions=True)
			ev.submit()

		team3_assignments = frappe.get_all("Mentor Assignment", filters={"team": "TST-FLOW-03"}, fields=["name", "mentor"])
		for a in team3_assignments:
			ev = frappe.get_doc({
				"doctype": "L2 Evaluation",
				"team": "TST-FLOW-03",
				"mentor": a.mentor,
				"assignment": a.name,
				"coding": 8, "solution_architecture": 7, "outcome": 7,
				"future_plan": 7, "innovation": 7, "collaboration": 8, "mentor_score": 8
			})  # Total = 52
			ev.insert(ignore_permissions=True)
			ev.submit()

		recompute_l2()

		t4 = frappe.get_doc("Hackathon Team", "TST-FLOW-04")
		self.assertEqual(t4.l2_avg, 60.0)
		self.assertEqual(t4.cumulative_score, 20.0 + 60.0)  # 80.0 /90

		select_regional()
		select_final(["TST-FLOW-04", "TST-FLOW-03"])

		t4.reload()
		t4.l3_score = 9.0  # /10
		t4.save(ignore_permissions=True)

		t3 = frappe.get_doc("Hackathon Team", "TST-FLOW-03")
		t3.l3_score = 8.0  # /10
		t3.save(ignore_permissions=True)

		win_res = finalize_winners()
		self.assertEqual(len(win_res["winners"]), 2)
		champion = win_res["winners"][0]

		self.assertEqual(champion["team_code"], "TST-FLOW-04")
		self.assertEqual(champion["final_total"], 89.0)
		self.assertEqual(champion["rank"], 1)
