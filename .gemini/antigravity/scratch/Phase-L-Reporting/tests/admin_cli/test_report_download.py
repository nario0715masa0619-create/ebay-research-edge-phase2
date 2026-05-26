import pytest
import os
import argparse
from src.admin_cli.report_commands import handle_show

# 17. cli download route success
def test_cli_download_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(report_id="test_report", download=True, format="json", output_file=None)
    
    # Run handle_show, it should create downloads/test_report.txt
    try:
        handle_show(args)
    except SystemExit:
        pass # return is fine, but in my implementation it returns without SystemExit if successful
        
    assert os.path.exists(os.path.join("downloads", "test_report.txt"))

# 18. cli download without flag (does not create file in downloads)
def test_cli_download_no_flag(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(report_id="test_report", download=False, format="json", output_file=None)
    
    handle_show(args)
    
    assert not os.path.exists(os.path.join("downloads", "test_report.txt"))
    captured = capsys.readouterr()
    assert captured.out != ""
