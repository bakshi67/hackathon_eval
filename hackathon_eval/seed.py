# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import random
import frappe
from hackathon_eval.api import (
	run_l1_shortlist,
	auto_assign_mentors,
	recompute_l2,
	select_regional,
	select_final,
	finalize_winners,
)
from hackathon_eval.hackathon_eval.doctype.hackathon_settings.hackathon_settings import get_hackathon_settings


def create_user_if_missing(email, first_name, role_name):
	if not frappe.db.exists("User", email):
		user = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"enabled": 1,
			"send_welcome_email": 0,
			"roles": [{"role": role_name}]
		})
		user.insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", email)
		user_roles = [r.role for r in user.roles]
		if role_name not in user_roles:
			user.add_roles(role_name)
	return email


def run(clean=False):
	"""
	Seed script to generate realistic demonstration data.
	bench execute hackathon_eval.seed.run
	"""
	print("--- Starting Hackathon Evaluation Demo Seeding ---")

	if clean:
		reset()

	# 1. Setup Hackathon Settings
	settings = frappe.get_doc("Hackathon Settings")
	settings.l1_max_marks = 20.0
	settings.l2_max_marks = 70.0
	settings.l3_max_marks = 10.0
	settings.overall_max = 100.0
	settings.l2_criterion_max = 10.0
	settings.l1_shortlist_target_min = 15  # Scaled for 30 demo teams
	settings.l1_shortlist_target_max = 20
	settings.regional_count = 10
	settings.final_count = 4
	settings.winners_count = 3
	settings.min_mentors_per_team = 3
	settings.normalize_mentor_scores = 0
	settings.scoring_locked = 0
	settings.flags.ignore_permissions = True
	settings.save(ignore_permissions=True)
	print("Hackathon Settings configured.")

	# 2. Create Users & Roles
	create_user_if_missing("admin_eval@hackathon.local", "Hackathon Admin", "Hackathon Admin")
	reviewer1 = create_user_if_missing("reviewer1@hackathon.local", "Reviewer One", "L1 Reviewer")
	reviewer2 = create_user_if_missing("reviewer2@hackathon.local", "Reviewer Two", "L1 Reviewer")

	mentor_data = [
		{"email": "mentor1@hackathon.local", "name": "Dr. Rajesh Gupta", "org": "IIT Delhi / AI Labs", "exp": "AI/ML"},
		{"email": "mentor2@hackathon.local", "name": "Prof. Sunita Rao", "org": "CloudMatrix Systems", "exp": "Cloud & DevOps"},
		{"email": "mentor3@hackathon.local", "name": "Amit Deshmukh", "org": "FinPay India", "exp": "FinTech & Security"},
		{"email": "mentor4@hackathon.local", "name": "Vikram Joshi", "org": "Hardware Innovations Ltd", "exp": "IoT & Embedded"},
		{"email": "mentor5@hackathon.local", "name": "Deepa Nair", "org": "WebScale Labs", "exp": "Web & Mobile"},
		{"email": "mentor6@hackathon.local", "name": "Sanjay Sinha", "org": "OpenTech Foundation", "exp": "Open Innovation"},
	]

	for m in mentor_data:
		create_user_if_missing(m["email"], m["name"], "Mentor")
		if not frappe.db.exists("Mentor", m["email"]):
			mentor_doc = frappe.get_doc({
				"doctype": "Mentor",
				"user": m["email"],
				"full_name": m["name"],
				"email": m["email"],
				"organization": m["org"],
				"expertise": m["exp"],
				"max_teams": 25
			})
			mentor_doc.insert(ignore_permissions=True)
		else:
			mentor_doc = frappe.get_doc("Mentor", m["email"])
			mentor_doc.full_name = m["name"]
			mentor_doc.organization = m["org"]
			mentor_doc.expertise = m["exp"]
			mentor_doc.save(ignore_permissions=True)

	print("6 Mentors and Reviewers initialized.")

	# 3. Create 30 Teams
	tracks = ["AI/ML", "Cybersecurity", "FinTech", "IoT & Hardware", "Cloud & DevOps", "Web & Mobile"]
	states = ["Delhi", "Maharashtra", "Karnataka", "Tamil Nadu", "Punjab", "Telangana", "West Bengal", "Uttar Pradesh"]
	institutions = ["IIT Delhi", "IIT Bombay", "BITS Pilani", "IIT Madras", "NIT Trichy", "IIIT Hyderabad", "Jadavpur University", "Delhi University"]

	for i in range(1, 31):
		code = f"HK-{i:04d}"
		track = tracks[(i - 1) % len(tracks)]
		inst = institutions[(i - 1) % len(institutions)]
		state = states[(i - 1) % len(states)]

		if not frappe.db.exists("Hackathon Team", code):
			team_doc = frappe.get_doc({
				"doctype": "Hackathon Team",
				"team_code": code,
				"team_name": f"Team Alpha {i:02d}",
				"track": track,
				"institution": inst,
				"state": state,
				"team_lead": f"Lead Student {i}",
				"lead_email": f"lead{i}@hackathon.local",
				"lead_phone": f"+91-98000{i:05d}",
				"project_title": f"Project Genesis {track} {i}",
				"project_summary": f"Cutting edge solution addressing grand challenges in {track}.",
				"status": "Enrolled",
				"members": [
					{"member_name": f"Lead Student {i}", "email": f"lead{i}@hackathon.local", "role": "Team Lead"},
					{"member_name": f"Developer {i}A", "email": f"dev{i}a@hackathon.local", "role": "Software Dev"},
					{"member_name": f"Developer {i}B", "email": f"dev{i}b@hackathon.local", "role": "Research & Design"}
				]
			})
			team_doc.insert(ignore_permissions=True)

	frappe.db.commit()
	print("30 Hackathon Teams created.")

	# Register a conflict for mentor1 on HK-0005 to demonstrate conflict handling
	m1 = frappe.get_doc("Mentor", "mentor1@hackathon.local")
	m1.conflicts = []
	m1.append("conflicts", {"team": "HK-0005", "reason": "Academic Advisor to Team Lead"})
	m1.save(ignore_permissions=True)
	print("Conflict registered: Mentor 1 has conflict with Team HK-0005.")

	# 4. Create L1 Reviews (out of 20 marks)
	for i in range(1, 31):
		code = f"HK-{i:04d}"
		base_score = 11.0 + ((i * 7) % 9) + round(((i % 5) * 0.2), 1)
		base_score = min(20.0, max(5.0, base_score))

		frappe.db.sql("DELETE FROM `tabL1 Review` WHERE team = %s", (code,))

		r1 = frappe.get_doc({
			"doctype": "L1 Review",
			"team": code,
			"reviewer": reviewer1,
			"score": base_score,
			"strengths": "Clear problem statement and good slide design.",
			"weaknesses": "Market viability needs more clarity.",
			"remarks": "Solid demonstration of concept."
		})
		r1.insert(ignore_permissions=True)
		r1.submit()

		score2 = min(20.0, max(5.0, round(base_score + ((i % 3) - 1) * 0.5, 1)))
		r2 = frappe.get_doc({
			"doctype": "L1 Review",
			"team": code,
			"reviewer": reviewer2,
			"score": score2,
			"strengths": "Feasible technical stack.",
			"weaknesses": "Time management during presentation.",
			"remarks": "Promising project."
		})
		r2.insert(ignore_permissions=True)
		r2.submit()

	frappe.db.commit()
	print("L1 Reviews scored and submitted for all 30 teams.")

	# 5. Run L1 Shortlisting
	shortlist_res = run_l1_shortlist()
	print(f"L1 Shortlist executed: {shortlist_res['shortlisted_count']} teams shortlisted, {shortlist_res['eliminated_count']} eliminated.")

	# 6. Auto-Assign Mentors
	assign_res = auto_assign_mentors()
	print(f"Auto-assigned mentors: {assign_res['new_assignments_created']} assignments created.")

	# 7. Create L2 Evaluations (Each criterion 0-10, total out of 70)
	assignments = frappe.get_all(
		"Mentor Assignment",
		fields=["name", "team", "mentor"]
	)

	frappe.db.sql("DELETE FROM `tabL2 Evaluation`")

	eval_count = 0
	for idx, a in enumerate(assignments, start=1):
		mod = (idx * 3) % 4
		coding = min(10.0, 7.0 + mod * 0.8)
		arch = min(10.0, 6.5 + mod * 0.9)
		outcome = min(10.0, 7.5 + mod * 0.7)
		future = min(10.0, 6.0 + mod * 1.0)
		innov = min(10.0, 7.0 + mod * 0.9)
		collab = min(10.0, 8.0 + mod * 0.5)
		mentor_sc = min(10.0, 7.5 + mod * 0.6)

		ev = frappe.get_doc({
			"doctype": "L2 Evaluation",
			"team": a.team,
			"mentor": a.mentor,
			"assignment": a.name,
			"coding": coding,
			"solution_architecture": arch,
			"outcome": outcome,
			"future_plan": future,
			"innovation": innov,
			"collaboration": collab,
			"mentor_score": mentor_sc,
			"remarks": f"Demonstration review by {a.mentor}. Working prototypes validated."
		})
		ev.insert(ignore_permissions=True)
		ev.submit()
		eval_count += 1

	frappe.db.commit()
	print(f"{eval_count} L2 Evaluations submitted.")

	# 8. Recompute L2 Scores & Rankings
	recompute_res = recompute_l2()
	print("L2 scores, averages, and rankings recomputed.")

	# 9. Select Regional Finalists (Top 10)
	reg_res = select_regional()
	print(f"Selected {reg_res['regional_selected_count']} Regional finalists.")

	# 10. Select Grand Finale (Top 4)
	fin_res = select_final()
	print(f"Selected {fin_res['final_selected_count']} Grand Finale teams.")

	# 11. Enter L3 Scores for Grand Finalists (out of 10)
	finalists = frappe.get_all(
		"Hackathon Team",
		filters={"status": "Final Selected"},
		fields=["name", "team_code"],
		order_by="cumulative_score desc"
	)

	l3_marks = [9.5, 9.0, 8.5, 7.5]
	for idx, f in enumerate(finalists):
		score = l3_marks[idx] if idx < len(l3_marks) else 8.0
		frappe.db.set_value("Hackathon Team", f.name, "l3_score", score)

	frappe.db.commit()
	print(f"Assigned Level 3 Jammu scores to {len(finalists)} finalists.")

	# 12. Finalize Winners
	win_res = finalize_winners()
	print("\n🏆 --- HACKATHON WINNERS PODIUM --- 🏆")
	for w in win_res["winners"]:
		print(f"{w['award']}: {w['team_code']} - {w['team_name']} | Final Total: {w['final_total']}/100 (L1: {w['l1_score']}, L2 Avg: {w['l2_avg']}, L3: {w['l3_score']})")

	print("\n--- Demo Seeding Completed Successfully! ---")
	return win_res


def reset():
	"""Reset demo data."""
	print("Resetting Hackathon data...")
	frappe.db.sql("DELETE FROM `tabL2 Evaluation`")
	frappe.db.sql("DELETE FROM `tabMentor Assignment`")
	frappe.db.sql("DELETE FROM `tabL1 Review`")
	frappe.db.sql("DELETE FROM `tabHackathon Team`")
	frappe.db.sql("DELETE FROM `tabTeam Member`")
	frappe.db.sql("DELETE FROM `tabMentor Conflict`")
	frappe.db.commit()
	print("All hackathon team data cleaned.")
