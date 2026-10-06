# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import csv
import io
import math
import frappe
from frappe import _
from hackathon_eval.hackathon_eval.doctype.hackathon_settings.hackathon_settings import get_hackathon_settings
from hackathon_eval.permissions import is_admin


def log_hackathon_activity(operation, subject, details=None):
	"""Log admin actions to Frappe's Activity Log."""
	try:
		al = frappe.get_doc({
			"doctype": "Activity Log",
			"subject": subject,
			"operation": operation,
			"user": frappe.session.user or "Administrator",
			"status": "Success",
		})
		al.insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"Failed to log activity: {str(e)}", "Hackathon Activity Log")


def verify_admin_access():
	if not is_admin():
		frappe.throw(_("Access denied: This operation requires Hackathon Admin privileges."), frappe.PermissionError)


@frappe.whitelist()
def import_teams(file=None, csv_content=None):
	"""
	Import teams from a CSV file.
	Accepts either a file URL/path or raw CSV content string.
	"""
	verify_admin_access()

	if file:
		# If file is a file_url or path
		if file.startswith("/files/") or file.startswith("/private/files/"):
			file_doc = frappe.get_doc("File", {"file_url": file})
			csv_content = file_doc.get_content()
		elif frappe.db.exists("File", file):
			file_doc = frappe.get_doc("File", file)
			csv_content = file_doc.get_content()
		else:
			# Try reading directly from filesystem
			with open(file, "r", encoding="utf-8") as f:
				csv_content = f.read()

	if not csv_content:
		frappe.throw(_("No CSV data provided for team import"))

	if isinstance(csv_content, bytes):
		csv_content = csv_content.decode("utf-8")

	reader = csv.DictReader(io.StringIO(csv_content.strip()))
	created = 0
	updated = 0

	for row in reader:
		code = row.get("team_code", "").strip()
		name = row.get("team_name", "").strip()
		if not code or not name:
			continue

		if frappe.db.exists("Hackathon Team", code):
			doc = frappe.get_doc("Hackathon Team", code)
			updated += 1
		else:
			doc = frappe.new_doc("Hackathon Team")
			doc.team_code = code
			created += 1

		doc.team_name = name
		doc.institution = row.get("institution", "").strip()
		doc.state = row.get("state", "").strip()
		doc.track = row.get("track", "").strip()
		doc.team_lead = row.get("team_lead", "").strip()
		doc.lead_email = row.get("lead_email", "").strip()
		doc.lead_phone = row.get("lead_phone", "").strip()
		doc.project_title = row.get("project_title", "").strip()
		doc.project_summary = row.get("project_summary", "").strip()
		doc.repo_url = row.get("repo_url", "").strip()
		doc.demo_url = row.get("demo_url", "").strip()
		doc.ppt_url = row.get("ppt_url", "").strip()
		if not doc.status:
			doc.status = "Enrolled"

		# Parse members if provided as "Name:email:role|Name2:email2:role2"
		members_raw = row.get("members", "").strip()
		if members_raw:
			doc.members = []
			for m in members_raw.split("|"):
				parts = [p.strip() for p in m.split(":")]
				if parts and parts[0]:
					doc.append("members", {
						"member_name": parts[0],
						"email": parts[1] if len(parts) > 1 else "",
						"role": parts[2] if len(parts) > 2 else "Member"
					})

		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)

	frappe.db.commit()
	msg = f"Teams Import completed: {created} created, {updated} updated."
	log_hackathon_activity("Team Import", msg)
	return {"message": msg, "created": created, "updated": updated}


@frappe.whitelist()
def run_l1_shortlist(cutoff=None):
	"""
	Run presentation round shortlist (mass elimination).
	Human-based scoring: Reviewers submit L1 reviews (out of 20).
	If cutoff is specified: teams with l1_score >= cutoff are shortlisted.
	If cutoff is None: auto-calculates cutoff so shortlisted count is within settings range [min, max].
	Ties at cutoff boundary resolved by earliest team_code.
	Provides clear elimination breakdown by track and score.
	"""
	verify_admin_access()
	settings = get_hackathon_settings()
	target_min = int(settings.l1_shortlist_target_min or 250)
	target_max = int(settings.l1_shortlist_target_max or 300)

	# Fetch all teams with their current L1 scores
	teams = frappe.get_all(
		"Hackathon Team",
		fields=["name", "team_code", "team_name", "track", "l1_score", "status"],
		order_by="l1_score desc, team_code asc"
	)

	if not teams:
		frappe.throw(_("No teams found to shortlist."))

	total_teams = len(teams)

	# If target_max exceeds total teams, adjust target_max
	effective_max = min(target_max, total_teams)
	effective_min = min(target_min, total_teams)

	selected_cutoff = None
	if cutoff is not None:
		selected_cutoff = float(cutoff)
		# Qualified teams are those >= selected_cutoff
		shortlisted_names = [t.name for t in teams if float(t.l1_score or 0) >= selected_cutoff]
	else:
		# Auto-determine cutoff score
		# We want a cutoff such that count is between effective_min and effective_max
		distinct_scores = sorted(list(set(float(t.l1_score or 0) for t in teams)), reverse=True)
		best_cutoff = None
		best_count = 0

		for s in distinct_scores:
			c = sum(1 for t in teams if float(t.l1_score or 0) >= s)
			if effective_min <= c <= effective_max:
				best_cutoff = s
				best_count = c
				break
			elif c > effective_max:
				# Score s exceeds max; previous score was below min.
				# We will use this score and tie-break by earliest team_code up to effective_max
				best_cutoff = s
				best_count = c
				break

		if best_cutoff is None:
			best_cutoff = distinct_scores[-1] if distinct_scores else 0.0

		selected_cutoff = best_cutoff
		# Apply cutoff with tie-break limit
		# Collect all >= best_cutoff
		potential = [t for t in teams if float(t.l1_score or 0) > selected_cutoff]
		tied = [t for t in teams if float(t.l1_score or 0) == selected_cutoff]
		# Sort tied by earliest team_code
		tied.sort(key=lambda x: x.team_code)

		needed = max(0, min(len(tied), effective_max - len(potential)))
		shortlisted_names = [t.name for t in potential] + [t.name for t in tied[:needed]]

		# If potential was already below min, take up to min or effective_max
		if len(shortlisted_names) < effective_min and len(teams) >= effective_min:
			shortlisted_names = [t.name for t in teams[:effective_min]]

	shortlisted_set = set(shortlisted_names)
	eliminated_by_track = {}
	shortlisted_by_track = {}
	shortlisted_count = 0
	eliminated_count = 0

	for t in teams:
		track = t.track or "General"
		if t.name in shortlisted_set:
			new_status = "L1 Shortlisted"
			shortlisted_count += 1
			shortlisted_by_track[track] = shortlisted_by_track.get(track, 0) + 1
		else:
			new_status = "L1 Eliminated"
			eliminated_count += 1
			eliminated_by_track[track] = eliminated_by_track.get(track, 0) + 1

		if t.status != new_status:
			frappe.db.set_value("Hackathon Team", t.name, "status", new_status, update_modified=False)

	frappe.db.commit()

	summary = {
		"cutoff": selected_cutoff,
		"shortlisted_count": shortlisted_count,
		"eliminated_count": eliminated_count,
		"total_teams": total_teams,
		"target_min": target_min,
		"target_max": target_max,
		"shortlisted_by_track": shortlisted_by_track,
		"eliminated_by_track": eliminated_by_track,
	}

	msg = f"L1 Shortlist executed: {shortlisted_count} shortlisted, {eliminated_count} eliminated (Cutoff: {selected_cutoff}/20)."
	log_hackathon_activity("L1 Shortlist", msg, summary)
	return summary


@frappe.whitelist()
def auto_assign_mentors():
	"""
	Evenly assigns min_mentors_per_team mentors to all L1 Shortlisted teams.
	- Respects mentor conflicts (skips conflict teams)
	- Respects max_teams per mentor
	- Deterministic, load-balanced, and idempotent (fills existing gaps without duplicates)
	"""
	verify_admin_access()
	settings = get_hackathon_settings()
	min_mentors = int(settings.min_mentors_per_team or 3)

	shortlisted_teams = frappe.get_all(
		"Hackathon Team",
		filters={"status": "L1 Shortlisted"},
		fields=["name", "team_code"],
		order_by="team_code asc"
	)

	if not shortlisted_teams:
		frappe.throw(_("No L1 Shortlisted teams available to assign."))

	# Fetch all registered mentors
	mentors = frappe.get_all(
		"Mentor",
		fields=["name", "max_teams", "full_name"],
		order_by="name asc"
	)

	if not mentors:
		frappe.throw(_("No registered Mentors found."))

	# Preload conflicts for each mentor
	conflicts_by_mentor = {}
	for m in mentors:
		conflicts = frappe.get_all(
			"Mentor Conflict",
			filters={"parent": m.name},
			pluck="team"
		)
		conflicts_by_mentor[m.name] = set(conflicts)

	# Preload existing assignments: (team, mentor) -> assignment_name
	existing_assignments = frappe.get_all(
		"Mentor Assignment",
		fields=["name", "team", "mentor"]
	)
	team_assigned_mentors = {}
	mentor_assignment_counts = {m.name: 0 for m in mentors}

	for a in existing_assignments:
		team_assigned_mentors.setdefault(a.team, set()).add(a.mentor)
		if a.mentor in mentor_assignment_counts:
			mentor_assignment_counts[a.mentor] += 1

	new_assignments_created = 0
	unassigned_or_partial_teams = []

	for t in shortlisted_teams:
		team_name = t.name
		current_mentors = team_assigned_mentors.get(team_name, set())
		needed = min_mentors - len(current_mentors)

		if needed <= 0:
			continue

		for _ in range(needed):
			# Pick available mentor with least assignments, no conflict, not already assigned, not exceeding max_teams
			candidates = []
			for m in mentors:
				m_name = m.name
				if m_name in current_mentors:
					continue
				if team_name in conflicts_by_mentor.get(m_name, set()):
					continue
				max_limit = m.max_teams or 9999
				if mentor_assignment_counts[m_name] >= max_limit:
					continue
				candidates.append(m_name)

			if not candidates:
				break

			# Load balance: pick candidate with lowest current count; tie-break deterministically by name
			best_mentor = min(candidates, key=lambda mn: (mentor_assignment_counts[mn], mn))

			# Create assignment
			assignment_doc = frappe.get_doc({
				"doctype": "Mentor Assignment",
				"team": team_name,
				"mentor": best_mentor,
				"status": "Assigned"
			})
			assignment_doc.flags.ignore_permissions = True
			assignment_doc.insert(ignore_permissions=True)

			current_mentors.add(best_mentor)
			team_assigned_mentors[team_name] = current_mentors
			mentor_assignment_counts[best_mentor] += 1
			new_assignments_created += 1

		if len(team_assigned_mentors.get(team_name, set())) < min_mentors:
			unassigned_or_partial_teams.append({
				"team_code": t.team_code,
				"assigned_count": len(team_assigned_mentors.get(team_name, set())),
				"required": min_mentors
			})

	frappe.db.commit()

	summary = {
		"total_teams_shortlisted": len(shortlisted_teams),
		"new_assignments_created": new_assignments_created,
		"unassigned_or_partial_teams": unassigned_or_partial_teams,
		"mentor_workloads": mentor_assignment_counts,
	}

	msg = f"Auto-assignment complete: {new_assignments_created} assignments created across {len(shortlisted_teams)} teams."
	log_hackathon_activity("Mentor Auto-Assignment", msg, summary)
	return summary


@frappe.whitelist()
def recompute_l2(team=None):
	"""
	Recomputes Level 2 aggregates:
	- l2_review_count
	- l2_avg (raw average of submitted totals /70)
	- l2_normalized_avg (per-mentor z-scores rescaled to 0-70 range if enabled)
	- cumulative_score = l1_score + (normalized if enabled, else raw l2_avg) /90
	- final_total = cumulative_score + l3_score /100
	- assigns l2_rank descending (tie-breakers: l2_avg, avg coding, team_code)
	  Only ranks teams with >= min_mentors_per_team submitted evaluations.
	"""
	settings = get_hackathon_settings()
	min_mentors = int(settings.min_mentors_per_team or 3)
	normalize = bool(settings.normalize_mentor_scores)

	# Fetch all submitted evaluations
	eval_filters = {"docstatus": 1}
	all_evals = frappe.get_all(
		"L2 Evaluation",
		filters=eval_filters,
		fields=["name", "team", "mentor", "total", "coding", "solution_architecture", "outcome", "future_plan", "innovation", "collaboration", "mentor_score"]
	)

	# Compute mentor stats for normalization if requested
	mentor_stats = {}
	overall_eval_totals = [float(e.total or 0.0) for e in all_evals]
	overall_mean = (sum(overall_eval_totals) / len(overall_eval_totals)) if overall_eval_totals else 35.0
	overall_variance = (sum((x - overall_mean) ** 2 for x in overall_eval_totals) / len(overall_eval_totals)) if overall_eval_totals else 100.0
	overall_std = math.sqrt(overall_variance) if overall_variance > 0 else 10.0

	if normalize:
		mentor_eval_groups = {}
		for e in all_evals:
			mentor_eval_groups.setdefault(e.mentor, []).append(float(e.total or 0.0))

		for m_name, scores in mentor_eval_groups.items():
			m_mean = sum(scores) / len(scores)
			m_variance = (sum((x - m_mean) ** 2 for x in scores) / len(scores)) if len(scores) > 1 else 0.0
			m_std = math.sqrt(m_variance)
			mentor_stats[m_name] = {"mean": m_mean, "std": m_std}

	# Group evaluations by team
	team_evals = {}
	for e in all_evals:
		team_evals.setdefault(e.team, []).append(e)

	# Get teams to update
	team_filter = {"name": team} if team else {}
	teams_to_update = frappe.get_all(
		"Hackathon Team",
		filters=team_filter,
		fields=["name", "team_code", "l1_score", "l3_score", "status"]
	)

	# Process team metrics
	team_metrics = []
	for t in teams_to_update:
		evals = team_evals.get(t.name, [])
		review_count = len(evals)

		if review_count > 0:
			totals = [float(e.total or 0.0) for e in evals]
			raw_avg = round(sum(totals) / review_count, 2)
			coding_avg = round(sum(float(e.coding or 0.0) for e in evals) / review_count, 2)

			if normalize:
				norm_scores = []
				for e in evals:
					raw_tot = float(e.total or 0.0)
					m_stat = mentor_stats.get(e.mentor, {"mean": raw_tot, "std": 0.0})
					if m_stat["std"] > 0.01:
						z = (raw_tot - m_stat["mean"]) / m_stat["std"]
						# Rescale back to 70-mark range
						rescaled = overall_mean + (z * overall_std)
						# Clamp within [0, 70]
						rescaled = max(0.0, min(70.0, rescaled))
						norm_scores.append(rescaled)
					else:
						norm_scores.append(raw_tot)
				norm_avg = round(sum(norm_scores) / len(norm_scores), 2)
			else:
				norm_avg = 0.0
		else:
			raw_avg = 0.0
			norm_avg = 0.0
			coding_avg = 0.0

		l1 = float(t.l1_score or 0.0)
		l2_comp = norm_avg if (normalize and norm_avg > 0) else raw_avg
		cum_score = round(l1 + l2_comp, 2)
		l3 = float(t.l3_score or 0.0)
		fin_tot = round(cum_score + l3, 2)

		team_metrics.append({
			"name": t.name,
			"team_code": t.team_code,
			"l1_score": l1,
			"l2_avg": raw_avg,
			"l2_normalized_avg": norm_avg,
			"l2_review_count": review_count,
			"coding_avg": coding_avg,
			"cumulative_score": cum_score,
			"l3_score": l3,
			"final_total": fin_tot,
			"qualifies_for_rank": review_count >= min_mentors
		})

	# If we are recomputing globally, assign L2 ranks
	if not team:
		# Qualified teams are ranked
		qualified = [tm for tm in team_metrics if tm["qualifies_for_rank"]]
		unqualified = [tm for tm in team_metrics if not tm["qualifies_for_rank"]]

		# Sort qualified by:
		# 1. cumulative_score DESC
		# 2. l2_avg DESC
		# 3. coding_avg DESC
		# 4. team_code ASC
		qualified.sort(
			key=lambda x: (
				-x["cumulative_score"],
				-x["l2_avg"],
				-x["coding_avg"],
				x["team_code"]
			)
		)

		for rank_idx, q in enumerate(qualified, start=1):
			q["l2_rank"] = rank_idx

		for u in unqualified:
			u["l2_rank"] = 0

	# Update database
	for m in team_metrics:
		updates = {
			"l2_avg": m["l2_avg"],
			"l2_normalized_avg": m["l2_normalized_avg"],
			"l2_review_count": m["l2_review_count"],
			"cumulative_score": m["cumulative_score"],
			"final_total": m["final_total"],
		}
		if "l2_rank" in m:
			updates["l2_rank"] = m["l2_rank"]

		frappe.db.set_value("Hackathon Team", m["name"], updates, update_modified=False)

	frappe.db.commit()

	msg = f"Recomputed L2 scores for {len(team_metrics)} teams (Normalization={'ON' if normalize else 'OFF'})."
	log_hackathon_activity("L2 Recompute", msg)
	return {"message": msg, "teams_processed": len(team_metrics)}


@frappe.whitelist()
def select_regional():
	"""
	Selects top regional_count teams by l2_rank to advance to Regional Hackathon.
	Other evaluated teams are set to Not Selected.
	"""
	verify_admin_access()
	settings = get_hackathon_settings()
	reg_count = int(settings.regional_count or 80)

	# Ensure ranks are up-to-date
	recompute_l2()

	# Get qualified teams by rank
	ranked_teams = frappe.get_all(
		"Hackathon Team",
		filters={"l2_rank": [">", 0]},
		fields=["name", "team_code", "team_name", "l2_rank", "cumulative_score", "status"],
		order_by="l2_rank asc"
	)

	if not ranked_teams:
		frappe.throw(_("No ranked teams found. Ensure L2 evaluations are submitted and meet minimum reviewer count."))

	selected = ranked_teams[:reg_count]
	selected_names = set(t.name for t in selected)

	# Teams in competition (shortlisted, evaluated)
	competing = frappe.get_all(
		"Hackathon Team",
		filters={"status": ["in", ["L1 Shortlisted", "L2 Evaluated", "Regional Selected", "Not Selected"]]},
		fields=["name", "status"]
	)

	selected_count = 0
	not_selected_count = 0

	for t in competing:
		if t.name in selected_names:
			new_status = "Regional Selected"
			selected_count += 1
		else:
			new_status = "Not Selected"
			not_selected_count += 1

		if t.status != new_status:
			frappe.db.set_value("Hackathon Team", t.name, "status", new_status, update_modified=False)

	frappe.db.commit()

	summary = {
		"regional_selected_count": selected_count,
		"not_selected_count": not_selected_count,
		"quota": reg_count,
		"teams": [{"team_code": t.team_code, "name": t.team_name, "rank": t.l2_rank} for t in selected]
	}

	msg = f"Regional Selection completed: {selected_count} teams selected (Quota: {reg_count}), {not_selected_count} set to Not Selected."
	log_hackathon_activity("Regional Selection", msg, summary)
	return summary


@frappe.whitelist()
def select_final(team_codes=None):
	"""
	Selects top final_count teams to advance to Jammu Grand Finale.
	Accepts optional explicit override list of team codes from Admin.
	"""
	verify_admin_access()
	settings = get_hackathon_settings()
	fin_count = int(settings.final_count or 8)

	if team_codes:
		if isinstance(team_codes, str):
			import json
			try:
				team_codes = json.loads(team_codes)
			except Exception:
				team_codes = [c.strip() for c in team_codes.split(",") if c.strip()]

		selected_teams = frappe.get_all(
			"Hackathon Team",
			filters={"team_code": ["in", team_codes]},
			fields=["name", "team_code", "team_name", "status", "cumulative_score"]
		)
		if len(selected_teams) != len(team_codes):
			found_codes = [t.team_code for t in selected_teams]
			missing = set(team_codes) - set(found_codes)
			frappe.throw(_("The following team codes were not found: {0}").format(", ".join(missing)))
	else:
		# Auto select top final_count among Regional Selected
		selected_teams = frappe.get_all(
			"Hackathon Team",
			filters={"status": "Regional Selected"},
			fields=["name", "team_code", "team_name", "status", "cumulative_score"],
			order_by="cumulative_score desc, l2_rank asc",
			limit=fin_count
		)

	if not selected_teams:
		frappe.throw(_("No eligible Regional Selected teams found to advance to the Grand Finale."))

	selected_names = set(t.name for t in selected_teams)

	for t in selected_teams:
		frappe.db.set_value("Hackathon Team", t.name, "status", "Final Selected", update_modified=False)

	frappe.db.commit()

	summary = {
		"final_selected_count": len(selected_teams),
		"quota": fin_count,
		"teams": [{"team_code": t.team_code, "team_name": t.team_name, "cumulative": t.cumulative_score} for t in selected_teams]
	}

	msg = f"Final Selection completed: {len(selected_teams)} teams advanced to Jammu Grand Finale."
	log_hackathon_activity("Final Selection", msg, summary)
	return summary


@frappe.whitelist()
def finalize_winners():
	"""
	Final round adjudication (Level 3 out of 10 marks).
	Computes final_total = cumulative_score (L1+L2 /90) + l3_score (/10) out of 100.
	Assigns final_rank (1 to 8), and flags top 3 as 1st, 2nd, and 3rd winners.
	"""
	verify_admin_access()
	settings = get_hackathon_settings()
	winners_count = int(settings.winners_count or 3)
	l3_max = float(settings.l3_max_marks or 10.0)

	finalists = frappe.get_all(
		"Hackathon Team",
		filters={"status": "Final Selected"},
		fields=["name", "team_code", "team_name", "l1_score", "l2_avg", "cumulative_score", "l3_score", "final_total", "track"]
	)

	if not finalists:
		frappe.throw(_("No Final Selected teams found to finalize winners."))

	# Validate L3 scores and compute final_total
	for f in finalists:
		l3 = float(f.l3_score or 0.0)
		if l3 < 0 or l3 > l3_max:
			frappe.throw(_("Team {0} has an invalid L3 score: {1}. Must be between 0 and {2}.").format(f.team_code, l3, l3_max))
		cum = float(f.cumulative_score or 0.0)
		f["final_total"] = round(cum + l3, 2)

	# Sort finalists by:
	# 1. final_total DESC
	# 2. cumulative_score DESC
	# 3. l2_avg DESC
	# 4. l1_score DESC
	# 5. team_code ASC
	finalists.sort(
		key=lambda x: (
			-x["final_total"],
			-float(x["cumulative_score"] or 0),
			-float(x["l2_avg"] or 0),
			-float(x["l1_score"] or 0),
			x["team_code"]
		)
	)

	podium_titles = {
		1: "1st Place - Champion",
		2: "2nd Place - 1st Runner Up",
		3: "3rd Place - 2nd Runner Up"
	}

	winners_list = []
	for rank_idx, f in enumerate(finalists, start=1):
		f["final_rank"] = rank_idx
		award = podium_titles.get(rank_idx, f"Finalist (Rank {rank_idx})")
		f["award"] = award

		frappe.db.set_value(
			"Hackathon Team",
			f["name"],
			{
				"final_total": f["final_total"],
				"final_rank": rank_idx
			},
			update_modified=False
		)

		if rank_idx <= winners_count:
			winners_list.append({
				"rank": rank_idx,
				"award": award,
				"team_code": f["team_code"],
				"team_name": f["team_name"],
				"l1_score": f["l1_score"],
				"l2_avg": f["l2_avg"],
				"cumulative_score": f["cumulative_score"],
				"l3_score": f["l3_score"],
				"final_total": f["final_total"]
			})

	frappe.db.commit()

	summary = {
		"winners": winners_list,
		"all_finalists": [
			{
				"rank": f["final_rank"],
				"award": f["award"],
				"team_code": f["team_code"],
				"team_name": f["team_name"],
				"final_total": f["final_total"]
			}
			for f in finalists
		]
	}

	winner_str = ", ".join([f"{w['award']}: {w['team_code']} ({w['team_name']})" for w in winners_list])
	msg = f"Hackathon Winners Finalized! {winner_str}"
	log_hackathon_activity("Finalize Winners", msg, summary)
	return summary
