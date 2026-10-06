# Copyright (c) 2026, Hackathon Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Mentor(Document):
	def validate(self):
		self.validate_user()
		self.fetch_user_details()

	def validate_user(self):
		if not self.user:
			frappe.throw(_("User link is required for Mentor"))

	def fetch_user_details(self):
		if self.user and frappe.db.exists("User", self.user):
			user_doc = frappe.get_cached_doc("User", self.user)
			if not self.full_name:
				self.full_name = user_doc.full_name or self.user
			if not self.email:
				self.email = user_doc.email

	def on_update(self):
		self.ensure_mentor_role()

	def ensure_mentor_role(self):
		if self.user and frappe.db.exists("User", self.user):
			user_doc = frappe.get_doc("User", self.user)
			user_roles = [r.role for r in user_doc.roles]
			if "Mentor" not in user_roles:
				user_doc.add_roles("Mentor")
