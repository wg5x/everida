from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from everida.api import app as api_app
from everida.cli import app as cli_app


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "raw" / "【已评审需规】120078-未来星年金保险（分红.docx"
TEMPLATE = ROOT / "raw" / "产品配置模板.xlsx"
SQL = ROOT / "raw" / "120078_N_1_1.sql"


def test_cli_product_run_writes_manifest(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        cli_app,
        [
            "product",
            "run",
            "--spec",
            str(SPEC),
            "--template",
            str(TEMPLATE),
            "--sql",
            str(SQL),
            "--out-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "run_manifest.json").exists()
    assert "completed" in result.output


def test_api_product_run_returns_artifacts(tmp_path):
    client = TestClient(api_app)

    response = client.post(
        "/products/run",
        json={
            "spec": str(SPEC),
            "template": str(TEMPLATE),
            "sql": str(SQL),
            "out_dir": str(tmp_path),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert "product_json" in payload["artifacts"]
