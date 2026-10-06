import frappe

def clear_users():
    test_users = [
        'test_mentor1@hackathon.test',
        'test_mentor2@hackathon.test',
        'test_mentor3@hackathon.test',
        'test_mentor4@hackathon.test',
        'test_mentor5@hackathon.test',
        'test_mentor6@hackathon.test',
        'test_reviewer@hackathon.test'
    ]
    
    for u in test_users:
        if frappe.db.exists("User", u):
            frappe.delete_doc("User", u, force=1, ignore_permissions=True)
            
    frappe.db.commit()
    print("Dummy users deleted.")
