# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe


def is_admin(user=None):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	user_roles = frappe.get_roles(user)
	return "Hackathon Admin" in user_roles or "System Manager" in user_roles


# --- L2 Evaluation ---
def get_l2_evaluation_conditions(user):
	if is_admin(user):
		return None
	user_roles = frappe.get_roles(user)
	if "Mentor" in user_roles:
		mentor = frappe.db.get_value("Mentor", {"user": user}, "name")
		if mentor:
			return f"`tabL2 Evaluation`.mentor = {frappe.db.escape(mentor)}"
	return "1=0"


def has_l2_evaluation_permission(doc, ptype="read", user=None):
	if not user:
		user = frappe.session.user
	if is_admin(user):
		return True
	user_roles = frappe.get_roles(user)
	if "Mentor" in user_roles:
		if ptype == "cancel":
			return False
		mentor = frappe.db.get_value("Mentor", {"user": user}, "name")
		if mentor and doc.mentor == mentor:
			return True
	return False


# --- Mentor Assignment ---
def get_mentor_assignment_conditions(user):
	if is_admin(user):
		return None
	user_roles = frappe.get_roles(user)
	if "Mentor" in user_roles:
		mentor = frappe.db.get_value("Mentor", {"user": user}, "name")
		if mentor:
			return f"`tabMentor Assignment`.mentor = {frappe.db.escape(mentor)}"
	return "1=0"


def has_mentor_assignment_permission(doc, ptype="read", user=None):
	if not user:
		user = frappe.session.user
	if is_admin(user):
		return True
	user_roles = frappe.get_roles(user)
	if "Mentor" in user_roles:
		if ptype in ["read", "select"]:
			mentor = frappe.db.get_value("Mentor", {"user": user}, "name")
			if mentor and doc.mentor == mentor:
				return True
	return False


# --- L1 Review ---
def get_l1_review_conditions(user):
	if is_admin(user):
		return None
	user_roles = frappe.get_roles(user)
	if "L1 Reviewer" in user_roles:
		return f"`tabL1 Review`.reviewer = {frappe.db.escape(user)}"
	return "1=0"


def has_l1_review_permission(doc, ptype="read", user=None):
	if not user:
		user = frappe.session.user
	if is_admin(user):
		return True
	user_roles = frappe.get_roles(user)
	if "L1 Reviewer" in user_roles:
		if ptype == "cancel":
			return False
		if doc.reviewer == user:
			return True
	return False
