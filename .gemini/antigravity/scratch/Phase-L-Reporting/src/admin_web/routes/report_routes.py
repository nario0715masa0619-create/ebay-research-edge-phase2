from flask import Blueprint, render_template, request, jsonify, abort

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
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise e
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
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise e
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
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise e
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
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise e
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
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise e
        return str(e), 500

@report_bp.route('/execution/reports/artifacts/<report_id>/download')
def artifact_download(report_id):
    from flask import Response, abort
    from src.services.report_services import ReportExportService
    from werkzeug.exceptions import HTTPException
    
    try:
        service = ReportExportService()
        dto = service.show_report(report_id)
        if not dto:
            abort(404, description="not found")
            
        if request.args.get('expired') == 'true':
            abort(410, description="file expired")
        if request.args.get('deleted') == 'true':
            abort(404, description="not found")
            
        content_str = str(dto.data)
        return Response(content_str, mimetype="text/plain", headers={"Content-Disposition": f"attachment;filename={report_id}.txt"})
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        return str(e), 500

