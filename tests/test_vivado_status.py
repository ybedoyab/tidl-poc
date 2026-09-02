from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tidl_poc.vivado.evidence import Carry4MismatchError, assert_mapped_carry4_matches
from tidl_poc.vivado.status import (
    reconcile_runner_status,
    reports_confirm_impl,
    reports_confirm_synth,
    terminate_process_tree,
)

EXPECTED_1CH32 = 1 * 8 * 32


def _write_synth_reports(case_dir: Path, *, carry4: int = EXPECTED_1CH32, synth_ok: bool = True) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    status = "ok" if synth_ok else "failed"
    (case_dir / "metrics.txt").write_text(
        f"TIDL_SYNTH_STATUS={status}\nTIDL_CARRY4_COUNT={carry4}\nTIDL_IMPL_STATUS=skipped\n",
        encoding="utf-8",
    )
    (case_dir / "utilization_synth.rpt").write_text(
        f"| Slice LUTs*             |  218 |     0 |          0 |    101400 |  0.21 |\n"
        f"| Slice Registers         | 1027 |  1024 |          0 |    202800 |  0.51 |\n"
        f"| CARRY4   |  {carry4} |          CarryLogic |\n",
        encoding="utf-8",
    )


def _write_impl_reports(case_dir: Path, *, carry4: int = EXPECTED_1CH32) -> None:
    _write_synth_reports(case_dir, carry4=carry4, synth_ok=True)
    (case_dir / "metrics.txt").write_text(
        f"TIDL_SYNTH_STATUS=ok\nTIDL_CARRY4_COUNT={carry4}\nTIDL_IMPL_STATUS=ok\n",
        encoding="utf-8",
    )
    (case_dir / "utilization_impl.rpt").write_text(
        f"| Slice LUTs*             |  218 |     0 |          0 |    101400 |  0.21 |\n"
        f"| Slice Registers         | 1027 |  1024 |          0 |    202800 |  0.51 |\n"
        f"| Slice                    |  416 |     0 |          0 |     25350 |  1.64 |\n"
        f"| CARRY4   |  {carry4} |          CarryLogic |\n",
        encoding="utf-8",
    )
    (case_dir / "timing_summary.rpt").write_text(
        "Worst Negative Slack (WNS): 0.144 ns\nTotal Negative Slack (TNS): 0.000 ns\n",
        encoding="utf-8",
    )
    (case_dir / "route_status.rpt").write_text(
        "# of fully routed nets............. :        1492 :\n"
        "# of routable nets..................... :        1492 :\n"
        "# of nets with routing errors.......... :           0 :\n",
        encoding="utf-8",
    )


def test_file_existence_alone_is_not_synth_success(tmp_path: Path):
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "utilization_synth.rpt").write_text("leftover empty file\n", encoding="utf-8")
    (case_dir / "metrics.txt").write_text("TIDL_SYNTH_STATUS=failed\nTIDL_CARRY4_COUNT=256\n", encoding="utf-8")
    assert reports_confirm_synth(case_dir, EXPECTED_1CH32) is False


def test_synth_requires_matching_carry4(tmp_path: Path):
    case_dir = tmp_path / "case"
    _write_synth_reports(case_dir, carry4=10)
    assert reports_confirm_synth(case_dir, EXPECTED_1CH32) is False
    _write_synth_reports(case_dir, carry4=EXPECTED_1CH32)
    assert reports_confirm_synth(case_dir, EXPECTED_1CH32) is True


def test_impl_requires_route_and_markers(tmp_path: Path):
    case_dir = tmp_path / "case"
    _write_synth_reports(case_dir)
    assert reports_confirm_impl(case_dir, EXPECTED_1CH32) is False
    _write_impl_reports(case_dir)
    assert reports_confirm_impl(case_dir, EXPECTED_1CH32) is True


def test_timeout_without_valid_reports_is_timeout(tmp_path: Path):
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    result = reconcile_runner_status(
        channels=1,
        chains_per_channel=8,
        carry4_per_chain=32,
        do_impl=True,
        case_dir=case_dir,
        timed_out=True,
        returncode=-1,
    )
    assert result["runner_status"] == "timeout"
    assert result["synth_status"] == "timeout"
    assert result["impl_status"] == "timeout"


def test_timeout_then_valid_reports_is_recovered(tmp_path: Path):
    case_dir = tmp_path / "case"
    _write_impl_reports(case_dir)
    result = reconcile_runner_status(
        channels=1,
        chains_per_channel=8,
        carry4_per_chain=32,
        do_impl=True,
        case_dir=case_dir,
        timed_out=True,
        returncode=-1,
    )
    assert result["runner_status"] == "recovered_after_timeout"
    assert result["synth_status"] == "ok"
    assert result["impl_status"] == "ok"


def test_nonzero_returncode_without_reports_is_failed(tmp_path: Path):
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    result = reconcile_runner_status(
        channels=1,
        chains_per_channel=8,
        carry4_per_chain=32,
        do_impl=False,
        case_dir=case_dir,
        timed_out=False,
        returncode=1,
    )
    assert result["runner_status"] == "failed"
    assert result["synth_status"] == "failed"


def test_zero_returncode_and_valid_synth_is_succeeded(tmp_path: Path):
    case_dir = tmp_path / "case"
    _write_synth_reports(case_dir)
    result = reconcile_runner_status(
        channels=1,
        chains_per_channel=8,
        carry4_per_chain=32,
        do_impl=False,
        case_dir=case_dir,
        timed_out=False,
        returncode=0,
    )
    assert result["runner_status"] == "succeeded"
    assert result["impl_status"] == "skipped"


def test_terminate_process_tree_windows_uses_taskkill():
    with patch("tidl_poc.vivado.status.os.name", "nt"), patch(
        "tidl_poc.vivado.status.subprocess.run"
    ) as run:
        run.return_value = MagicMock(returncode=0)
        terminate_process_tree(4242)
        args = run.call_args[0][0]
        assert args[:5] == ["taskkill", "/PID", "4242", "/T", "/F"]


def test_run_vivado_batch_timeout_kills_tree(tmp_path: Path):
    from tidl_poc.vivado.baseline import run_vivado_batch
    import subprocess

    proc = MagicMock()
    proc.pid = 99
    proc.communicate.side_effect = subprocess.TimeoutExpired(cmd="vivado", timeout=1)
    tcl_path = tmp_path / "run.tcl"
    tcl_path.write_text("# dummy\n", encoding="utf-8")
    log_path = tmp_path / "vivado.log"

    with (
        patch("tidl_poc.vivado.baseline.subprocess.Popen", return_value=proc),
        patch("tidl_poc.vivado.baseline.terminate_process_tree") as killer,
    ):
        code, blob, timed_out = run_vivado_batch(
            Path("vivado"),
            tcl_path,
            log_path,
            timeout_s=0.01,
        )
    assert timed_out is True
    assert code == -1
    assert "TIMEOUT" in blob
    killer.assert_called_once_with(99)


def test_assert_mapped_carry4_fails_on_mismatch():
    with pytest.raises(Carry4MismatchError):
        assert_mapped_carry4_matches(
            [
                {
                    "case_id": "ch16_nch08_c4_64",
                    "channels": 16,
                    "chains_per_channel": 8,
                    "carry4_per_chain": 64,
                    "mapped_carry4": 8000,
                }
            ]
        )
    assert_mapped_carry4_matches(
        [
            {
                "case_id": "ch16_nch08_c4_64",
                "channels": 16,
                "chains_per_channel": 8,
                "carry4_per_chain": 64,
                "mapped_carry4": 8192,
            }
        ]
    )
