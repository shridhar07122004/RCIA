from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone


def csv_bytes(test_cases: list[dict]) -> bytes:
    output = io.StringIO()
    fields = ["test_case_id", "objective", "preconditions", "steps", "expected_result", "related_requirement_id", "category"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows({key: case.get(key, "") for key in fields} for case in test_cases)
    return output.getvalue().encode("utf-8-sig")


def html_report(document_name: str, proposed_change: str, result: dict) -> str:
    rows = "".join(f"<tr><td>{item['requirement_code']}</td><td>{item['impact_type']}</td><td>{item['severity']}</td><td>{item['impact_score']:.2f}</td><td>{item['explanation']}</td></tr>" for item in result.get("impacts", []))
    risks = "".join(f"<li><strong>{risk['name']}:</strong> {risk['reason']} Mitigation: {risk['mitigation']}</li>" for risk in result.get("risks", [])) or "<li>No rule-based risks were detected.</li>"
    considered = "".join(f"<li><strong>{item['requirement_code']}</strong> — {item['description']}</li>" for item in result.get("requirements_considered", []))
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>RCIA impact report</title><style>body{{font-family:Arial,sans-serif;color:#172033;max-width:1100px;margin:40px auto;line-height:1.5}}h1{{color:#174ea6}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d9e2ef;padding:10px;text-align:left;vertical-align:top}}th{{background:#eef4fc}}.meta{{background:#f5f8fc;padding:16px;border-radius:8px}}</style></head><body><h1>Requirement Change Impact Report</h1><div class='meta'><p><strong>Document:</strong> {document_name}</p><p><strong>Generated:</strong> {datetime.now(timezone.utc).isoformat()}</p><p><strong>Proposed change:</strong> {proposed_change}</p><p><strong>Summary:</strong> {result.get('summary', '')}</p><p><strong>Effort:</strong> {result.get('effort', {}).get('level', '')} — {result.get('effort', {}).get('range', '')}</p></div><h2>Requirements considered</h2><ul>{considered or '<li>No requirements were extracted.</li>'}</ul><h2>Impact candidates</h2><table><thead><tr><th>Requirement</th><th>Type</th><th>Severity</th><th>Score</th><th>Explanation</th></tr></thead><tbody>{rows or '<tr><td colspan=5>No strong impact detected.</td></tr>'}</tbody></table><h2>Risks</h2><ul>{risks}</ul><h2>Recommended actions</h2><ul>{''.join(f'<li>{item}</li>' for item in result.get('recommendations', []))}</ul><h2>Suggested test cases</h2><ul>{''.join(f"<li><strong>{case['test_case_id']} — {case['objective']}</strong>: {case['expected_result']}</li>" for case in result.get('test_cases', []))}</ul></body></html>"""
