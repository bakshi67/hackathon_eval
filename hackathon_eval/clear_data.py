import frappe

def clear_all():
    doctypes_to_clear = [
        "L2 Evaluation",
        "L1 Review",
        "Mentor Assignment",
        "Hackathon Team",
        "Mentor"
    ]
    
    frappe.flags.in_test = True
    
    for dt in doctypes_to_clear:
        # Get all records regardless of status
        records = frappe.get_all(dt, pluck="name")
        for name in records:
            doc = frappe.get_doc(dt, name)
            if hasattr(doc, 'docstatus') and doc.docstatus == 1:
                # Cancel if submitted
                doc.cancel()
            frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
            
    frappe.db.commit()
    print("All dummy data cleared successfully.")
