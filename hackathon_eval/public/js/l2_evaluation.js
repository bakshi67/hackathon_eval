const CRITERIA_FIELDS = [
	'coding',
	'solution_architecture',
	'outcome',
	'future_plan',
	'innovation',
	'collaboration',
	'mentor_score'
];

frappe.ui.form.on('L2 Evaluation', {
	setup: function(frm) {
		// Set field descriptions/hints
		CRITERIA_FIELDS.forEach(function(f) {
			frm.set_df_property(f, 'description', __('Score between 0.0 and 10.0'));
		});
	},

	refresh: function(frm) {
		calculate_live_total(frm);

		if (frm.doc.docstatus === 1) {
			frm.set_intro(__('This evaluation has been officially submitted and locked.'), 'green');
		} else if (frm.doc.docstatus === 0) {
			frm.set_intro(__('Enter marks out of 10 for each of the 7 criteria. Total is calculated out of 70 marks.'), 'blue');
		}
	},

	coding: function(frm) { validate_and_recalc(frm, 'coding'); },
	solution_architecture: function(frm) { validate_and_recalc(frm, 'solution_architecture'); },
	outcome: function(frm) { validate_and_recalc(frm, 'outcome'); },
	future_plan: function(frm) { validate_and_recalc(frm, 'future_plan'); },
	innovation: function(frm) { validate_and_recalc(frm, 'innovation'); },
	collaboration: function(frm) { validate_and_recalc(frm, 'collaboration'); },
	mentor_score: function(frm) { validate_and_recalc(frm, 'mentor_score'); }
});

function validate_and_recalc(frm, fieldname) {
	let val = flt(frm.doc[fieldname]);
	if (val < 0) {
		frappe.msgprint(__('Score cannot be negative. Setting to 0.'));
		frm.set_value(fieldname, 0);
	} else if (val > 10) {
		frappe.msgprint(__('Maximum score per criterion is 10. Setting to 10.'));
		frm.set_value(fieldname, 10);
	}
	calculate_live_total(frm);
}

function calculate_live_total(frm) {
	let total = 0.0;
	CRITERIA_FIELDS.forEach(function(f) {
		total += flt(frm.doc[f]);
	});
	frm.set_value('total', Math.round(total * 100) / 100);
}
