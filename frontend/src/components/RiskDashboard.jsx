const riskRows = [
	["Critical", "8 scenarios", "0 failed", "Release blocking"],
	["High", "24 scenarios", "1 failed", "Needs reviewer sign-off"],
	["Medium", "41 scenarios", "2 failed", "Track regression dataset"],
	["Low", "19 scenarios", "0 failed", "Monitor only"],
];

const gates = [
	["Risk-adjusted pass rate", "94%", "minimum 80%"],
	["Safety-critical failures", "0", "maximum 0"],
	["High-risk failures", "1", "maximum 0"],
	["Critical violations", "0", "maximum 0"],
];

export default function RiskDashboard() {
	return (
		<section className="section risk-section" id="risk">
			<div className="container risk-grid">
				<div className="section-header reveal">
					<p className="eyebrow">Risk-aware release gates</p>
					<h2>Aggregate confidence is not enough for autonomous agents.</h2>
					<p>
						Ozark separates low-impact failures from high-risk and
						safety-critical failures, then blocks releases when the risky paths
						regress.
					</p>
				</div>

				<div
					className="risk-card reveal"
					aria-label="Risk adjusted evaluation summary"
				>
					<div className="risk-score">
						<span>risk-adjusted pass rate</span>
						<strong>94%</strong>
						<p>Weighted by low, medium, high, and critical scenario impact.</p>
					</div>

					<div
						className="risk-table"
						role="table"
						aria-label="Scenario risk coverage"
					>
						<div className="risk-table-head" role="row">
							<span role="columnheader">Risk</span>
							<span role="columnheader">Coverage</span>
							<span role="columnheader">Failures</span>
							<span role="columnheader">Action</span>
						</div>
						{riskRows.map(([level, coverage, failures, action]) => (
							<div className="risk-table-row" role="row" key={level}>
								<strong role="cell">{level}</strong>
								<span role="cell">{coverage}</span>
								<span role="cell">{failures}</span>
								<span role="cell">{action}</span>
							</div>
						))}
					</div>
				</div>

				<div className="gate-card reveal" aria-label="Configured release gates">
					<div className="gate-card-top">
						<span>release policy</span>
						<b>deterministic</b>
					</div>
					{gates.map(([name, value, limit]) => (
						<article key={name}>
							<div>
								<h3>{name}</h3>
								<p>{limit}</p>
							</div>
							<strong>{value}</strong>
						</article>
					))}
				</div>
			</div>
		</section>
	);
}
