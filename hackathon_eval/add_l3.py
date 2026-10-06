import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def create_l3_evaluation():
    # Inject Server Script to update Team on submit
    if not frappe.db.exists("Server Script", "L3 Evaluation Server Logic"):
        frappe.get_doc({
            "doctype": "Server Script",
            "name": "L3 Evaluation Server Logic",
            "script_type": "DocType Event",
            "reference_doctype": "L3 Evaluation",
            "doctype_event": "After Submit",
            "script": """
team_doc = frappe.get_doc("Hackathon Team", doc.team)
team_doc.db_set("l3_score", doc.l3_score)
team_doc.db_set("cumulative_score", (team_doc.l1_score or 0) + (team_doc.l2_avg or 0))
team_doc.db_set("final_total", team_doc.cumulative_score + doc.l3_score)
"""
        }).insert(ignore_permissions=True)
        
        frappe.get_doc({
            "doctype": "Server Script",
            "name": "L3 Evaluation Cancel Logic",
            "script_type": "DocType Event",
            "reference_doctype": "L3 Evaluation",
            "doctype_event": "After Cancel",
            "script": """
team_doc = frappe.get_doc("Hackathon Team", doc.team)
team_doc.db_set("l3_score", 0)
team_doc.db_set("final_total", team_doc.cumulative_score)
"""
        }).insert(ignore_permissions=True)
        print("Added Server Scripts")
        
    # Update Workspace
    import json
    ws = frappe.get_doc('Workspace', 'Hackathon')
    
    # Check if shortcut already exists
    exists = False
    for s in ws.shortcuts:
        if s.label == 'L3 Evaluations':
            exists = True
            break
            
    if not exists:
        ws.append('shortcuts', {
            'label': 'L3 Evaluations',
            'type': 'DocType',
            'link_to': 'L3 Evaluation'
        })
        
        content = json.loads(ws.content)
        content.append({"type": "shortcut", "data": {"shortcut_name": "L3 Evaluations"}})
        ws.content = json.dumps(content)
        ws.save(ignore_permissions=True)
        print("Added to Workspace")

    frappe.db.commit()

# create_l3_evaluation()
