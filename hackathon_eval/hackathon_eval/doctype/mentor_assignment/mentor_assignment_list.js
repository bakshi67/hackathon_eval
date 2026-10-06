frappe.listview_settings['Mentor Assignment'] = {
	add_fields: ['status', 'team', 'mentor'],
	get_indicator: function(doc) {
		if (doc.status === 'Scored') {
			return [__('Scored'), 'green', 'status,=,Scored'];
		} else if (doc.status === 'Assigned') {
			return [__('Assigned'), 'orange', 'status,=,Assigned'];
		} else if (doc.status === 'Absent') {
			return [__('Absent'), 'red', 'status,=,Absent'];
		}
	},
	button: {
		show: function(doc) {
			return doc.status !== 'Scored';
		},
		get_label: function() {
			return __('Score Now');
		},
		get_description: function(doc) {
			return __('Open L2 Evaluation for team ' + doc.team);
		},
		action: function(doc) {
			frappe.new_doc('L2 Evaluation', {
				assignment: doc.name,
				team: doc.team,
				mentor: doc.mentor
			});
		}
	}
};
