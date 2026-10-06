import frappe
import json

def fix():
    # Update Hackathon workspace
    ws = frappe.get_doc('Workspace', 'Hackathon')
    ws.shortcuts = []
    
    shortcuts = [
        {'label': 'Control Panel', 'type': 'Page', 'link_to': 'hackathon_control_pa'},
        {'label': 'Hackathon Teams', 'type': 'DocType', 'link_to': 'Hackathon Team'},
        {'label': 'Mentors', 'type': 'DocType', 'link_to': 'Mentor'},
        {'label': 'Mentor Assignments', 'type': 'DocType', 'link_to': 'Mentor Assignment'},
        {'label': 'L1 Reviews', 'type': 'DocType', 'link_to': 'L1 Review'},
        {'label': 'L2 Evaluations', 'type': 'DocType', 'link_to': 'L2 Evaluation'},
        {'label': 'Hackathon Settings', 'type': 'DocType', 'link_to': 'Hackathon Settings'},
        {'label': 'Score Matrix', 'type': 'Report', 'link_to': 'Mentor Team Score Matrix', 'is_query_report': 1},
        {'label': 'Leaderboard', 'type': 'Report', 'link_to': 'Leaderboard', 'is_query_report': 1},
        {'label': 'Final Standings', 'type': 'Report', 'link_to': 'Final Standings', 'is_query_report': 1}
    ]
    
    content = [
        {"type": "header", "data": {"text": "National Hackathon Evaluation Center", "level": 3}},
        {"type": "paragraph", "data": {"text": "End-to-end evaluation management across 3 levels."}},
        {"type": "header", "data": {"text": "Shortcuts", "level": 4}}
    ]
    
    for s in shortcuts:
        ws.append('shortcuts', s)
        content.append({"type": "shortcut", "data": {"shortcut_name": s['label']}})
    
    ws.content = json.dumps(content)
    ws.save(ignore_permissions=True)
    
    # Update Mentor workspace
    ws2 = frappe.get_doc('Workspace', 'Mentor Desk')
    ws2.shortcuts = []
    
    m_shortcuts = [
        {'label': 'My Assigned Teams', 'type': 'DocType', 'link_to': 'Mentor Assignment'},
        {'label': 'My Submitted Evaluations', 'type': 'DocType', 'link_to': 'L2 Evaluation'},
        {'label': 'My Progress Report', 'type': 'Report', 'link_to': 'Mentor Progress', 'is_query_report': 1}
    ]
    
    content2 = [
        {"type": "header", "data": {"text": "Mentor Evaluation Desk", "level": 3}},
        {"type": "paragraph", "data": {"text": "Review your assigned teams and enter Demonstration round evaluations."}}
    ]
    
    for s in m_shortcuts:
        ws2.append('shortcuts', s)
        content2.append({"type": "shortcut", "data": {"shortcut_name": s['label']}})
        
    ws2.content = json.dumps(content2)
    ws2.save(ignore_permissions=True)
    
    frappe.db.commit()
    print('Workspaces fixed.')
