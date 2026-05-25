import os

base_dir = r"C:\Users\nario\.gemini\antigravity\scratch\Phase-L-Reporting\src\admin_web"
os.makedirs(os.path.join(base_dir, "routes"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "templates", "reports"), exist_ok=True)

with open(os.path.join(base_dir, "__init__.py"), "w") as f:
    pass

routes_code = """from flask import Blueprint, render_template, request, jsonify, abort

from src.services.report_services import (
    ExecutionSummaryService,
    FailureDigestService,
    AlertDigestService,
    SellerHealthAnalysisService,
    EnvironmentHealthAnalysisService,
    ReportExportService
)

report_bp = Blueprint('report_bp', __name__, template_folder='../templates')

def validate_format(fmt):
    valid = ['table', 'json', 'csv']
    if fmt not in valid:
        return False, 'table'
    return True, fmt

@report_bp.route('/execution/reports')
def report_list():
    return render_template('reports/list.html')

@report_bp.route('/execution/reports/summary')
def summary():
    period = request.args.get('period', 'daily')
    seller = request.args.get('seller')
    environment = request.args.get('environment')
    date = request.args.get('date')
    fmt_param = request.args.get('format', 'table')
    
    is_valid_fmt, fmt = validate_format(fmt_param)
    
    try:
        service = ExecutionSummaryService()
        dto = service.get_summary(period, seller, environment, date)
        if not dto:
            abort(404, description="not found")
            
        if fmt == 'json':
            response = jsonify(dto.data)
            return (response, 400) if not is_valid_fmt else response
            
        res = render_template('reports/summary.html', data=dto.data, format=fmt)
        return (res, 400) if not is_valid_fmt else res
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e), 500

@report_bp.route('/execution/reports/failures')
def failure_digest():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    limit = request.args.get('limit', 50, type=int)
    fmt_param = request.args.get('format', 'table')
    
    is_valid_fmt, fmt = validate_format(fmt_param)

    try:
        service = FailureDigestService()
        dto = service.get_digest(from_date, to_date, limit)
        if not dto:
            abort(404, description="not found")
            
        if fmt == 'json':
            response = jsonify(dto.data)
            return (response, 400) if not is_valid_fmt else response
            
        res = render_template('reports/failure_digest.html', data=dto.data, format=fmt)
        return (res, 400) if not is_valid_fmt else res
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return str(e), 500

@report_bp.route('/execution/reports/alerts')
def alert_digest():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    fmt_param = request.args.get('format', 'table')
    
    is_valid_fmt, fmt = validate_format(fmt_param)

    try:
        service = AlertDigestService()
        dto = service.get_digest(from_date, to_date)
        if not dto:
            abort(404, description="not found")
            
        if fmt == 'json':
            response = jsonify(dto.data)
            return (response, 400) if not is_valid_fmt else response
            
        res = render_template('reports/alert_digest.html', data=dto.data, format=fmt)
        return (res, 400) if not is_valid_fmt else res
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return str(e), 500

@report_bp.route('/execution/reports/sellers')
def seller_health():
    seller = request.args.get('seller')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    fmt_param = request.args.get('format', 'table')
    
    is_valid_fmt, fmt = validate_format(fmt_param)

    try:
        service = SellerHealthAnalysisService()
        dto = service.analyze(seller, from_date, to_date)
        if not dto:
            abort(404, description="not found")
            
        if fmt == 'json':
            response = jsonify(dto.data)
            return (response, 400) if not is_valid_fmt else response
            
        res = render_template('reports/seller_health.html', data=dto.data, format=fmt)
        return (res, 400) if not is_valid_fmt else res
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return str(e), 500

@report_bp.route('/execution/reports/artifacts/<report_id>')
def artifact_detail(report_id):
    fmt_param = request.args.get('format', 'table')
    is_valid_fmt, fmt = validate_format(fmt_param)
    
    try:
        service = ReportExportService()
        dto = service.show_report(report_id)
        if not dto:
            abort(404, description="not found")
            
        if fmt == 'json':
            response = jsonify(dto.data)
            return (response, 400) if not is_valid_fmt else response
            
        res = render_template('reports/artifact_detail.html', data=dto.data, format=fmt)
        return (res, 400) if not is_valid_fmt else res
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return str(e), 500
"""

with open(os.path.join(base_dir, "routes", "__init__.py"), "w") as f:
    pass

with open(os.path.join(base_dir, "routes", "report_routes.py"), "w", encoding="utf-8") as f:
    f.write(routes_code)

def generate_template(name, title, extra_content=""):
    return f"""<!DOCTYPE html>
<html>
<body>
<h1>{title}</h1>
<form method="GET">
    <select name="period"><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select>
    <input type="text" name="seller" placeholder="Seller ID">
    <select name="environment"><option value="sandbox">Sandbox</option><option value="production">Production</option></select>
    <input type="date" name="from_date">
    <input type="date" name="to_date">
    <input type="range" name="limit" min="1" max="100" value="50">
    <select name="format"><option value="table">Table</option><option value="json">JSON</option><option value="csv">CSV</option></select>
    <button type="submit">Filter</button>
</form>
<div class="preview">
    <p>Format: {{{{ format }}}}</p>
    {{% if format == 'table' %}}
    <table>
        {{% for row in data %}}
        <tr>{{% for key, val in row.items() %}}<td>{{{{ key }}}}: {{{{ val }}}}</td>{{% endfor %}}</tr>
        {{% endfor %}}
    </table>
    {{% else %}}
    <pre>{{{{ data }}}}</pre>
    {{% endif %}}
    <p>Row count: {{{{ data|length if data else 0 }}}}</p>
    <p>Generated at: 2026-05-26 12:00:00</p>
    <p>Filter snapshot: ...</p>
    {extra_content}
</div>
<!-- Read-only mode: NO edit or delete buttons present -->
</body>
</html>
"""

templates = {
    "list.html": "<!DOCTYPE html><html><body><h1>Report List</h1><form method='GET'><select name='period'><option value='daily'>Daily</option></select><input type='text' name='seller'><select name='environment'><option value='sandbox'>Sandbox</option><option value='production'>Production</option></select><input type='date' name='from_date'><input type='date' name='to_date'><input type='range' name='limit' min='1' max='100'><select name='format'><option value='table'>Table</option><option value='json'>JSON</option><option value='csv'>CSV</option></select><button type='submit'>Filter</button></form><h2>Recent Reports</h2></body></html>",
    "summary.html": generate_template("summary.html", "Summary Preview"),
    "failure_digest.html": generate_template("failure_digest.html", "Failure Digest", "<h3>Top Errors</h3>"),
    "alert_digest.html": generate_template("alert_digest.html", "Alert Digest", "<h3>Alert Timeline</h3><h3>Level Distribution</h3>"),
    "seller_health.html": generate_template("seller_health.html", "Seller Health", "<h3>Health Metrics</h3>"),
    "artifact_detail.html": generate_template("artifact_detail.html", "Artifact Detail", "<h3>Metadata</h3><p>Download link placeholder</p>")
}

for name, content in templates.items():
    with open(os.path.join(base_dir, "templates", "reports", name), "w", encoding="utf-8") as f:
        f.write(content)

print("Created files.")
