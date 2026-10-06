frappe.pages['hackathon_control_pa'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Hackathon Control Panel',
		single_column: true
	});

	page.set_secondary_action('Refresh Stats', function() {
		load_dashboard_stats(page);
	}, 'octicon octicon-sync');

	// Quick Settings button
	page.add_inner_button('Configure Settings', function() {
		frappe.set_route('Form', 'Hackathon Settings');
	}, 'Quick Navigation');

	page.add_inner_button('Mentor Score Matrix', function() {
		frappe.set_route('query-report', 'Mentor Team Score Matrix');
	}, 'Quick Navigation');

	page.add_inner_button('Leaderboard', function() {
		frappe.set_route('query-report', 'Leaderboard');
	}, 'Quick Navigation');

	page.add_inner_button('Final Standings', function() {
		frappe.set_route('query-report', 'Final Standings');
	}, 'Quick Navigation');

	render_control_panel(page);
	load_dashboard_stats(page);
};

function render_control_panel(page) {
	let html = `
	<div class="hackathon-control-panel-wrapper" style="padding: 15px 0;">
		<!-- Overview Banner -->
		<div class="card mb-4" style="background: linear-gradient(135deg, #1f2937, #111827); color: #fff; border-radius: 8px; padding: 20px;">
			<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
				<div>
					<h3 style="margin: 0; color: #fff; font-weight: 700;">National Hackathon Evaluation Center</h3>
					<p style="margin: 6px 0 0; color: #9ca3af; font-size: 14px;">
						Human-Centric 3-Tier Marking Architecture (Total: 100 Marks) &bull; 562 Participating Teams
					</p>
				</div>
				<div style="display: flex; gap: 12px; margin-top: 10px;">
					<span class="badge" style="background: #3b82f6; font-size: 13px; padding: 8px 12px; border-radius: 6px;">Level 1: 20M</span>
					<span class="badge" style="background: #8b5cf6; font-size: 13px; padding: 8px 12px; border-radius: 6px;">Level 2: 70M</span>
					<span class="badge" style="background: #10b981; font-size: 13px; padding: 8px 12px; border-radius: 6px;">Level 3: 10M</span>
				</div>
			</div>
		</div>

		<!-- Real-time Status Metric Counters -->
		<div class="row mb-4" id="stats-container">
			<div class="col-sm-2">
				<div class="card text-center" style="padding: 12px; border-left: 4px solid #6b7280;">
					<div style="font-size: 12px; color: #6b7280; font-weight: 600;">TOTAL TEAMS</div>
					<div id="stat-total-teams" style="font-size: 24px; font-weight: bold; color: #111827;">-</div>
				</div>
			</div>
			<div class="col-sm-2">
				<div class="card text-center" style="padding: 12px; border-left: 4px solid #f59e0b;">
					<div style="font-size: 12px; color: #f59e0b; font-weight: 600;">L1 SHORTLISTED</div>
					<div id="stat-l1-shortlisted" style="font-size: 24px; font-weight: bold; color: #111827;">-</div>
				</div>
			</div>
			<div class="col-sm-2">
				<div class="card text-center" style="padding: 12px; border-left: 4px solid #ef4444;">
					<div style="font-size: 12px; color: #ef4444; font-weight: 600;">L1 ELIMINATED</div>
					<div id="stat-l1-eliminated" style="font-size: 24px; font-weight: bold; color: #111827;">-</div>
				</div>
			</div>
			<div class="col-sm-2">
				<div class="card text-center" style="padding: 12px; border-left: 4px solid #8b5cf6;">
					<div style="font-size: 12px; color: #8b5cf6; font-weight: 600;">L2 EVALUATED</div>
					<div id="stat-l2-evaluated" style="font-size: 24px; font-weight: bold; color: #111827;">-</div>
				</div>
			</div>
			<div class="col-sm-2">
				<div class="card text-center" style="padding: 12px; border-left: 4px solid #06b6d4;">
					<div style="font-size: 12px; color: #06b6d4; font-weight: 600;">REGIONAL (TOP 80)</div>
					<div id="stat-regional" style="font-size: 24px; font-weight: bold; color: #111827;">-</div>
				</div>
			</div>
			<div class="col-sm-2">
				<div class="card text-center" style="padding: 12px; border-left: 4px solid #10b981;">
					<div style="font-size: 12px; color: #10b981; font-weight: 600;">GRAND FINALE (TOP 8)</div>
					<div id="stat-finalists" style="font-size: 24px; font-weight: bold; color: #111827;">-</div>
				</div>
			</div>
		</div>

		<!-- Action Workflow Grid -->
		<div class="row">
			<!-- Stage 1 & 2 -->
			<div class="col-md-6 mb-4">
				<div class="card" style="padding: 20px; height: 100%;">
					<h5 style="font-weight: 700; color: #1f2937; margin-bottom: 8px;">
						<span style="background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px;">STAGE 1</span>
						Import & Presentation Shortlisting
					</h5>
					<p style="color: #6b7280; font-size: 13px;">
						Import registered teams from CSV or execute mass elimination based on human presentation reviews (out of 20 marks).
					</p>
					<div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">
						<button class="btn btn-default btn-sm" id="btn-import-teams">
							<i class="fa fa-upload"></i> Import Teams CSV
						</button>
						<button class="btn btn-primary btn-sm" id="btn-run-l1">
							<i class="fa fa-filter"></i> Run L1 Shortlist (Mass Elimination)
						</button>
					</div>
					<div id="l1-result-box" style="margin-top: 15px; display: none;"></div>
				</div>
			</div>

			<!-- Stage 3 & 4 -->
			<div class="col-md-6 mb-4">
				<div class="card" style="padding: 20px; height: 100%;">
					<h5 style="font-weight: 700; color: #1f2937; margin-bottom: 8px;">
						<span style="background: #f3e8ff; color: #6b21a8; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px;">STAGE 2</span>
						Mentor Assignment & L2 Scoring
					</h5>
					<p style="color: #6b7280; font-size: 13px;">
						Evenly distribute shortlisted teams to ~25 mentors (min 3 mentors/team), preventing conflicts and balancing quotas. Recompute scores out of 70 marks.
					</p>
					<div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">
						<button class="btn btn-primary btn-sm" id="btn-auto-assign">
							<i class="fa fa-users"></i> Auto-Assign Mentors
						</button>
						<button class="btn btn-default btn-sm" id="btn-recompute-l2">
							<i class="fa fa-calculator"></i> Recompute L2 & Ranks
						</button>
					</div>
					<div id="l2-result-box" style="margin-top: 15px; display: none;"></div>
				</div>
			</div>

			<!-- Stage 5 & 6 -->
			<div class="col-md-6 mb-4">
				<div class="card" style="padding: 20px; height: 100%;">
					<h5 style="font-weight: 700; color: #1f2937; margin-bottom: 8px;">
						<span style="background: #ccfbf1; color: #0f766e; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px;">STAGE 3</span>
						Regional & Grand Finale Selection
					</h5>
					<p style="color: #6b7280; font-size: 13px;">
						Advance top 80 teams to Regional Hackathons. Then shortlist top 8 teams to the Jammu Grand Finale with automatic ranking or manual override.
					</p>
					<div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">
						<button class="btn btn-primary btn-sm" id="btn-select-regional">
							<i class="fa fa-trophy"></i> Select Regional (Top 80)
						</button>
						<button class="btn btn-default btn-sm" id="btn-select-final">
							<i class="fa fa-star"></i> Select Finalists (Top 8)
						</button>
					</div>
					<div id="selection-result-box" style="margin-top: 15px; display: none;"></div>
				</div>
			</div>

			<!-- Stage 7 -->
			<div class="col-md-6 mb-4">
				<div class="card" style="padding: 20px; height: 100%;">
					<h5 style="font-weight: 700; color: #1f2937; margin-bottom: 8px;">
						<span style="background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px;">STAGE 4</span>
						Level 3 & Winners Finalization
					</h5>
					<p style="color: #6b7280; font-size: 13px;">
						Adjudicate final presentation marks (out of 10) in Jammu. Calculate 100-mark final total (L1 20M + L2 70M + L3 10M) and determine 1st, 2nd, and 3rd place!
					</p>
					<div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">
						<button class="btn btn-success btn-sm" id="btn-finalize-winners">
							<i class="fa fa-award"></i> Finalize Winners & Podium
						</button>
					</div>
					<div id="winners-result-box" style="margin-top: 15px; display: none;"></div>
				</div>
			</div>
		</div>
	</div>
	`;

	$(page.main).html(html);
	bind_panel_events(page);
}

function load_dashboard_stats(page) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Hackathon Team',
			fields: ['status', 'count(name) as count'],
			group_by: 'status'
		},
		callback: function(r) {
			let total = 0;
			let status_map = {};
			if (r.message) {
				r.message.forEach(function(item) {
					status_map[item.status] = item.count;
					total += item.count;
				});
			}
			$('#stat-total-teams').text(total);
			$('#stat-l1-shortlisted').text(status_map['L1 Shortlisted'] || 0);
			$('#stat-l1-eliminated').text(status_map['L1 Eliminated'] || 0);
			$('#stat-l2-evaluated').text(status_map['L2 Evaluated'] || 0);
			$('#stat-regional').text(status_map['Regional Selected'] || 0);
			$('#stat-finalists').text(status_map['Final Selected'] || 0);
		}
	});
}

function bind_panel_events(page) {
	// 1. Import Teams CSV
	$('#btn-import-teams').on('click', function() {
		let d = new frappe.ui.Dialog({
			title: 'Import Teams via CSV',
			fields: [
				{
					fieldname: 'csv_data',
					fieldtype: 'Code',
					label: 'Paste CSV Data (or upload file below)',
					description: 'Columns: team_code, team_name, institution, state, track, team_lead, lead_email, lead_phone'
				},
				{
					fieldname: 'file_upload',
					fieldtype: 'Attach',
					label: 'Or Attach CSV File'
				}
			],
			primary_action_label: 'Import Teams',
			primary_action: function(data) {
				frappe.call({
					method: 'hackathon_eval.api.import_teams',
					args: {
						file: data.file_upload,
						csv_content: data.csv_data
					},
					freeze: true,
					freeze_message: 'Importing teams...',
					callback: function(res) {
						d.hide();
						frappe.msgprint(res.message.message);
						load_dashboard_stats(page);
					}
				});
			}
		});
		d.show();
	});

	// 2. Run L1 Shortlist
	$('#btn-run-l1').on('click', function() {
		let d = new frappe.ui.Dialog({
			title: 'Execute Level 1 Presentation Shortlist',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'desc',
					options: '<p style="color:#6b7280; font-size:13px;">This will execute mass elimination based on submitted L1 Presentation scores (/20). Teams will be categorized into <b>L1 Shortlisted</b> and <b>L1 Eliminated</b>.</p>'
				},
				{
					fieldname: 'cutoff',
					fieldtype: 'Float',
					label: 'Manual Cutoff Score (/20)',
					description: 'Leave empty to auto-calculate cutoff targeting 250-300 teams as configured in Settings.'
				}
			],
			primary_action_label: 'Run Shortlisting',
			primary_action: function(data) {
				frappe.confirm(
					'Are you sure you want to run the L1 Shortlisting & Mass Elimination process?',
					function() {
						frappe.call({
							method: 'hackathon_eval.api.run_l1_shortlist',
							args: { cutoff: data.cutoff || null },
							freeze: true,
							freeze_message: 'Evaluating L1 scores and eliminating...',
							callback: function(r) {
								d.hide();
								let s = r.message;
								let resHtml = `
									<div class="alert alert-success" style="font-size: 13px;">
										<strong>L1 Shortlist Completed!</strong><br>
										&bull; Cutoff Score: <b>${s.cutoff}/20</b><br>
										&bull; Shortlisted: <b>${s.shortlisted_count} teams</b><br>
										&bull; Eliminated: <b>${s.eliminated_count} teams</b>
									</div>
								`;
								$('#l1-result-box').html(resHtml).show();
								load_dashboard_stats(page);
							}
						});
					}
				);
			}
		});
		d.show();
	});

	// 3. Auto-assign mentors
	$('#btn-auto-assign').on('click', function() {
		frappe.confirm(
			'This will evenly allocate min 3 mentors to all L1 Shortlisted teams, avoiding conflicts and respecting mentor capacity. Proceed?',
			function() {
				frappe.call({
					method: 'hackathon_eval.api.auto_assign_mentors',
					freeze: true,
					freeze_message: 'Balancing mentor assignments...',
					callback: function(r) {
						let s = r.message;
						let resHtml = `
							<div class="alert alert-info" style="font-size: 13px;">
								<strong>Auto-Assignment Complete!</strong><br>
								&bull; New Assignments Created: <b>${s.new_assignments_created}</b><br>
								&bull; Teams Processed: <b>${s.total_teams_shortlisted}</b><br>
								${s.unassigned_or_partial_teams.length > 0 ? `&bull; Partial/Unassigned Teams: <b style="color:red;">${s.unassigned_or_partial_teams.length}</b>` : '&bull; All teams received required mentors!'}
							</div>
						`;
						$('#l2-result-box').html(resHtml).show();
						load_dashboard_stats(page);
					}
				});
			}
		);
	});

	// 4. Recompute L2
	$('#btn-recompute-l2').on('click', function() {
		frappe.call({
			method: 'hackathon_eval.api.recompute_l2',
			freeze: true,
			freeze_message: 'Recomputing scores and rankings...',
			callback: function(r) {
				frappe.msgprint(r.message.message);
				load_dashboard_stats(page);
			}
		});
	});

	// 5. Select Regional
	$('#btn-select-regional').on('click', function() {
		frappe.confirm(
			'Select the top 80 teams by Level 2 Rank to advance to the Regional Hackathon? (Other teams will be marked Not Selected).',
			function() {
				frappe.call({
					method: 'hackathon_eval.api.select_regional',
					freeze: true,
					freeze_message: 'Selecting regional finalists...',
					callback: function(r) {
						let s = r.message;
						let resHtml = `
							<div class="alert alert-success" style="font-size: 13px;">
								<strong>Regional Selection Completed!</strong><br>
								&bull; Regional Selected: <b>${s.regional_selected_count} teams</b><br>
								&bull; Not Selected: <b>${s.not_selected_count} teams</b>
							</div>
						`;
						$('#selection-result-box').html(resHtml).show();
						load_dashboard_stats(page);
					}
				});
			}
		);
	});

	// 6. Select Finalists
	$('#btn-select-final').on('click', function() {
		let d = new frappe.ui.Dialog({
			title: 'Select Jammu Grand Finale Teams (Top 8)',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'desc',
					options: '<p style="color:#6b7280; font-size:13px;">By default, top 8 teams from Regional Selected by cumulative score (L1+L2) are selected. You may optionally supply specific team codes to override.</p>'
				},
				{
					fieldname: 'team_codes',
					fieldtype: 'Small Text',
					label: 'Manual Override Team Codes (Comma separated)',
					description: 'e.g. HK-0001, HK-0012, HK-0045 (Leave blank for automatic top 8 selection)'
				}
			],
			primary_action_label: 'Confirm Finalists',
			primary_action: function(data) {
				frappe.call({
					method: 'hackathon_eval.api.select_final',
					args: { team_codes: data.team_codes || null },
					freeze: true,
					freeze_message: 'Shortlisting Grand Finalists...',
					callback: function(r) {
						d.hide();
						let s = r.message;
						let resHtml = `
							<div class="alert alert-success" style="font-size: 13px;">
								<strong>Finalists Selected!</strong><br>
								&bull; Teams Advanced to Jammu: <b>${s.final_selected_count}</b>
							</div>
						`;
						$('#selection-result-box').html(resHtml).show();
						load_dashboard_stats(page);
					}
				});
			}
		});
		d.show();
	});

	// 7. Finalize Winners
	$('#btn-finalize-winners').on('click', function() {
		frappe.confirm(
			'Finalize winners and standings for Jammu Grand Finale? This computes Final Total (L1 20M + L2 70M + L3 10M = 100M) and awards 1st, 2nd, and 3rd place podium.',
			function() {
				frappe.call({
					method: 'hackathon_eval.api.finalize_winners',
					freeze: true,
					freeze_message: 'Adjudicating Final Standings...',
					callback: function(r) {
						let s = r.message;
						let winnersHtml = s.winners.map(w => `
							<div style="padding: 6px 0; border-bottom: 1px solid #e5e7eb;">
								<b>${w.award}</b>: ${w.team_code} - ${w.team_name} 
								<span class="badge badge-success" style="float: right;">Total: ${w.final_total}/100</span>
								<div style="font-size: 11px; color: #6b7280;">L1: ${w.l1_score} | L2 Avg: ${w.l2_avg} | L3: ${w.l3_score}</div>
							</div>
						`).join('');

						let resHtml = `
							<div class="card" style="padding: 15px; border: 2px solid #10b981; background: #f0fdf4;">
								<h6 style="color: #065f46; font-weight: bold; margin-bottom: 10px;">🏆 Grand Finale Podium Winners</h6>
								${winnersHtml}
								<div style="margin-top: 10px; text-align: right;">
									<button class="btn btn-xs btn-primary" onclick="frappe.set_route('query-report', 'Final Standings')">
										View Full Final Standings Report &rarr;
									</button>
								</div>
							</div>
						`;
						$('#winners-result-box').html(resHtml).show();
						load_dashboard_stats(page);
					}
				});
			}
		);
	});
}