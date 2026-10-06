frappe.ui.form.on('Hackathon Team', {
	refresh: function(frm) {
		let is_admin = frappe.user.has_role('Hackathon Admin') || frappe.session.user === 'Administrator' || frappe.user.has_role('System Manager');

		// Status Indicator
		frm.page.set_indicator(frm.doc.status, {
			'Enrolled': 'blue',
			'L1 Shortlisted': 'orange',
			'L1 Eliminated': 'red',
			'L2 Evaluated': 'purple',
			'Regional Selected': 'cyan',
			'Final Selected': 'green',
			'Not Selected': 'gray'
		}[frm.doc.status] || 'blue');

		if (is_admin && !frm.is_new()) {
			// Quick Action Buttons
			frm.add_custom_button(__('L1 Shortlist'), function() {
				frm.set_value('status', 'L1 Shortlisted');
				frm.save();
			}, __('Quick Status'));

			frm.add_custom_button(__('L1 Eliminate'), function() {
				frm.set_value('status', 'L1 Eliminated');
				frm.save();
			}, __('Quick Status'));

			frm.add_custom_button(__('Select Regional'), function() {
				frm.set_value('status', 'Regional Selected');
				frm.save();
			}, __('Quick Status'));

			frm.add_custom_button(__('Select Final'), function() {
				frm.set_value('status', 'Final Selected');
				frm.save();
			}, __('Quick Status'));

			// Render "Scores by Mentor" section
			render_mentor_scores(frm);
		}
	}
});

function render_mentor_scores(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'L2 Evaluation',
			filters: {
				team: frm.doc.name,
				docstatus: 1
			},
			fields: [
				'name', 'mentor', 'coding', 'solution_architecture',
				'outcome', 'future_plan', 'innovation', 'collaboration',
				'mentor_score', 'total', 'remarks'
			]
		},
		callback: function(r) {
			let evals = r.message || [];
			let html = `
				<div class="mentor-scores-panel" style="margin-top: 15px; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; background: #fafafa;">
					<h5 style="margin-top: 0; font-weight: 700; color: #1f2937;">Scores by Mentor (Level 2 Detailed Audit)</h5>
					<p style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">Submitted evaluations by assigned mentors out of 70 marks.</p>
			`;

			if (evals.length === 0) {
				html += `<div class="text-muted" style="font-size: 13px;">No submitted evaluations recorded for this team yet.</div>`;
			} else {
				html += `
					<div class="table-responsive">
						<table class="table table-bordered table-sm" style="font-size: 12px; background: #fff;">
							<thead style="background: #f3f4f6;">
								<tr>
									<th>Mentor</th>
									<th>Coding</th>
									<th>Arch</th>
									<th>Outcome</th>
									<th>Future Plan</th>
									<th>Innov</th>
									<th>Collab</th>
									<th>Mentor Sc</th>
									<th>Total (/70)</th>
									<th>Remarks</th>
									<th>Action</th>
								</tr>
							</thead>
							<tbody>
				`;
				evals.forEach(function(ev) {
					html += `
						<tr>
							<td><b>${ev.mentor}</b></td>
							<td>${ev.coding}</td>
							<td>${ev.solution_architecture}</td>
							<td>${ev.outcome}</td>
							<td>${ev.future_plan}</td>
							<td>${ev.innovation}</td>
							<td>${ev.collaboration}</td>
							<td>${ev.mentor_score}</td>
							<td><b style="color: #2563eb;">${ev.total}</b></td>
							<td>${ev.remarks || '-'}</td>
							<td>
								<a href="/app/l2-evaluation/${ev.name}" class="btn btn-xs btn-default" target="_blank">
									View Doc
								</a>
							</td>
						</tr>
					`;
				});
				html += `</tbody></table></div>`;
			}
			html += `</div>`;

			// Append or update in form layout
			frm.dashboard.clear_headline();
			$(frm.wrapper).find('.mentor-scores-panel').remove();
			$(frm.wrapper).find('.form-page').append(html);
		}
	});
}
