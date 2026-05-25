import argparse
import sys
import json
import csv
import io
from typing import List, Dict, Any

from src.services.report_services import (
    ExecutionSummaryService,
    FailureDigestService,
    AlertDigestService,
    SellerHealthAnalysisService,
    EnvironmentHealthAnalysisService,
    ReportExportService
)

def format_output(data: List[Dict[str, Any]], fmt: str) -> str:
    if not data:
        return ""
    if fmt == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue().strip()
    else:  # table
        keys = list(data[0].keys())
        header = "| " + " | ".join(keys) + " |"
        sep = "|" + "|".join(["-" * (len(k) + 2) for k in keys]) + "|"
        rows = [header, sep]
        for row in data:
            rows.append("| " + " | ".join(str(row.get(k, "")) for k in keys) + " |")
        return "\n".join(rows)

def save_and_print(content: str, output_file: str = None):
    print(content)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved to: {output_file}")

def add_common_args(parser, formats=('table', 'json', 'csv'), default_format='table'):
    if formats:
        parser.add_argument('--format', choices=formats, default=default_format)
    parser.add_argument('--output-file')

def handle_summary(args):
    try:
        service = ExecutionSummaryService()
        dto = service.get_summary(args.period, args.seller, args.environment, args.date)
        if not dto:
            print("not found")
            sys.exit(1)
        save_and_print(format_output(dto.data, args.format), args.output_file)
    except ValueError as e:
        print(f"validation error: {e}")
        sys.exit(1)

def handle_failure_digest(args):
    try:
        service = FailureDigestService()
        dto = service.get_digest(args.from_date, args.to_date, args.limit)
        if not dto:
            print("not found")
            sys.exit(1)
        save_and_print(format_output(dto.data, args.format), args.output_file)
    except ValueError as e:
        print(f"validation error: {e}")
        sys.exit(1)

def handle_alert_digest(args):
    try:
        service = AlertDigestService()
        dto = service.get_digest(args.from_date, args.to_date)
        if not dto:
            print("not found")
            sys.exit(1)
        save_and_print(format_output(dto.data, args.format), args.output_file)
    except ValueError as e:
        print(f"validation error: {e}")
        sys.exit(1)

def handle_seller_health(args):
    try:
        service = SellerHealthAnalysisService()
        dto = service.analyze(args.seller, args.from_date, args.to_date)
        if not dto:
            print("not found")
            sys.exit(1)
        save_and_print(format_output(dto.data, args.format), args.output_file)
    except ValueError as e:
        print(f"validation error: {e}")
        sys.exit(1)

def handle_env_health(args):
    try:
        service = EnvironmentHealthAnalysisService()
        dto = service.analyze(args.environment, args.from_date, args.to_date)
        if not dto:
            print("not found")
            sys.exit(1)
        save_and_print(format_output(dto.data, args.format), args.output_file)
    except ValueError as e:
        print(f"validation error: {e}")
        sys.exit(1)

def handle_audit_export(args):
    try:
        service = ReportExportService()
        dto = service.export_audit(args.seller, args.from_date, args.to_date)
        if not dto:
            print("not found")
            sys.exit(1)
        save_and_print(format_output(dto.data, args.format), args.output_file)
    except ValueError as e:
        print(f"validation error: {e}")
        sys.exit(1)

def handle_artifacts(args):
    try:
        service = ReportExportService()
        dto = service.list_artifacts(args.limit, args.report_type, args.seller)
        save_and_print(format_output(dto.data, getattr(args, 'format', 'table')), args.output_file)
    except ValueError as e:
        if "unsupported" in str(e):
            print("unsupported report type")
        else:
            print(f"validation error: {e}")
        sys.exit(1)

def handle_show(args):
    try:
        service = ReportExportService()
        dto = service.show_report(args.report_id)
        if not dto:
            print("not found")
            sys.exit(1)
        save_and_print(format_output(dto.data, args.format), args.output_file)
    except ValueError as e:
        print(f"validation error: {e}")
        sys.exit(1)


def create_parser():
    parser = argparse.ArgumentParser(prog='ops report')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # summary
    summary_parser = subparsers.add_parser('summary')
    summary_parser.add_argument('--period', choices=['daily', 'weekly', 'monthly'], required=True)
    summary_parser.add_argument('--seller')
    summary_parser.add_argument('--environment')
    summary_parser.add_argument('--date')
    add_common_args(summary_parser)
    summary_parser.set_defaults(func=handle_summary)

    # failure-digest
    fd_parser = subparsers.add_parser('failure-digest')
    fd_parser.add_argument('--from-date')
    fd_parser.add_argument('--to-date')
    fd_parser.add_argument('--limit', type=int, default=50)
    add_common_args(fd_parser)
    fd_parser.set_defaults(func=handle_failure_digest)

    # alert-digest
    ad_parser = subparsers.add_parser('alert-digest')
    ad_parser.add_argument('--from-date')
    ad_parser.add_argument('--to-date')
    add_common_args(ad_parser)
    ad_parser.set_defaults(func=handle_alert_digest)

    # seller-health
    sh_parser = subparsers.add_parser('seller-health')
    sh_parser.add_argument('--seller', required=True)
    sh_parser.add_argument('--from-date')
    sh_parser.add_argument('--to-date')
    add_common_args(sh_parser)
    sh_parser.set_defaults(func=handle_seller_health)

    # env-health
    eh_parser = subparsers.add_parser('env-health')
    eh_parser.add_argument('--environment', required=True)
    eh_parser.add_argument('--from-date')
    eh_parser.add_argument('--to-date')
    add_common_args(eh_parser)
    eh_parser.set_defaults(func=handle_env_health)

    # audit-export
    ae_parser = subparsers.add_parser('audit-export')
    ae_parser.add_argument('--seller')
    ae_parser.add_argument('--from-date')
    ae_parser.add_argument('--to-date')
    add_common_args(ae_parser, formats=('csv', 'json'), default_format='csv')
    ae_parser.set_defaults(func=handle_audit_export)

    # artifacts
    art_parser = subparsers.add_parser('artifacts')
    art_parser.add_argument('--limit', type=int, default=20)
    art_parser.add_argument('--report-type')
    art_parser.add_argument('--seller')
    add_common_args(art_parser)
    art_parser.set_defaults(func=handle_artifacts)

    # show
    show_parser = subparsers.add_parser('show')
    show_parser.add_argument('--report-id', required=True)
    add_common_args(show_parser)
    show_parser.set_defaults(func=handle_show)

    return parser

def main(args=None):
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    parsed_args.func(parsed_args)

if __name__ == '__main__':
    main()
