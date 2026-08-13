"""Sanitized, self-contained AwardLens HTML report."""

from html import escape

from opsgraph.domains.awardlens.models import AuditRun


def render_audit_report(audit: AuditRun) -> str:
    rows = "".join(_finding_row(finding) for finding in audit.findings)
    sources = ", ".join(escape(source) for source in audit.source_ids)
    limitations = "".join(f"<li>{escape(value)}</li>" for value in audit.limitations)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AwardLens synthetic audit {escape(audit.audit_id)}</title>
  <style>
    body{{font:14px system-ui,sans-serif;color:#162033;margin:36px;line-height:1.45}}
    h1{{margin-bottom:4px}} .notice{{padding:12px;background:#fff5e6;border:1px solid #f2cd8f}}
    .summary{{display:flex;gap:24px;margin:24px 0}} .summary strong{{display:block;font-size:22px}}
    table{{width:100%;border-collapse:collapse}} th,td{{padding:9px;border:1px solid #d8e0eb;text-align:left}}
    th{{background:#f5f7fa}} .manual{{color:#9a5a00}} footer{{margin-top:24px;color:#536178}}
  </style>
</head>
<body>
  <header><h1>AwardLens AU synthetic audit</h1><p>Rule MA000004 · version {escape(audit.rule_version)}</p></header>
  <p class="notice">Educational synthetic-data comparison only. This report is not legal or payroll advice.</p>
  <section class="summary">
    <div>Records<strong>{audit.record_count}</strong></div>
    <div>Manual review<strong>{audit.manual_review_count}</strong></div>
    <div>Potential difference<strong>{_money(audit.total_liability_cents)}</strong></div>
  </section>
  <table>
    <thead><tr><th>Record</th><th>Employee</th><th>Status</th><th>Expected</th><th>Paid</th><th>Difference</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <h2>Limitations</h2><ul>{limitations}</ul>
  <footer>Sources: {sources} · Input SHA-256: {escape(audit.input_sha256)}</footer>
</body>
</html>"""


def _finding_row(finding) -> str:
    status_class = " class=\"manual\"" if finding.status == "manual_review" else ""
    return (
        "<tr>"
        f"<td>{escape(finding.record_id)}</td>"
        f"<td>{escape(finding.employee_id)}</td>"
        f"<td{status_class}>{escape(finding.status.replace('_', ' ').title())}</td>"
        f"<td>{_optional_money(finding.expected_gross_cents)}</td>"
        f"<td>{_money(finding.paid_gross_cents)}</td>"
        f"<td>{_optional_money(finding.liability_cents)}</td>"
        "</tr>"
    )


def _optional_money(cents: int | None) -> str:
    return "Manual review" if cents is None else _money(cents)


def _money(cents: int) -> str:
    return f"${cents / 100:,.2f}"
