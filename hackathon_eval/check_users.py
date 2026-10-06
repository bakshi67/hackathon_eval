import frappe

def check_users():
    users = frappe.get_all("User", filters={"name": ("like", "%test%")}, pluck="name")
    print("Test users:", users)
    
    roles = frappe.get_all("Role", pluck="name")
    print("Total roles:", len(roles))
