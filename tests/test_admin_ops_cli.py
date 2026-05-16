import pytest
from unittest.mock import patch, MagicMock
from src.admin_cli.app import main

def test_cli_help():
    with patch("sys.argv", ["ops", "--help"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

def test_cli_jobs_list():
    with patch("src.admin_cli.bootstrap.AdminCliBootstrap.bootstrap") as mock_boot:
        mock_app = MagicMock()
        mock_boot.return_value = mock_app
        mock_app.job_service.list_jobs.return_value = [{"job_name": "test_job"}]
        
        with patch("sys.argv", ["ops", "jobs", "list"]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 0
            mock_app.job_service.list_jobs.assert_called_once()
