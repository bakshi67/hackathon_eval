frappe.ui.form.on('Mentor Assignment', {
	refresh: function(frm) {
		if (!frm.is_new() && frm.doc.status !== 'Scored') {
			frm.add_custom_button(__('Score Now'), function() {
				frappe.new_doc('L2 Evaluation', {
					assignment: frm.doc.name,
					team: frm.doc.team,
					mentor: frm.doc.mentor
				});
			}).addClass('btn-primary');
		}
	}
});
