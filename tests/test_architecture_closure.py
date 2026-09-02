"""Tests for front-end datasheet arithmetic and UTC epoch arming."""

import pytest

from tidl_poc.models.frontend_electrical import (
    baseline_decision,
    evaluate_corner,
    pecl_levels,
)
from tidl_poc.models.utc_timestamp import SIGNED_INTERVAL_LIMIT_S, UtcEpochController


def test_pecl_typ_2p5_inside_lvds25_typ_window():
    c = evaluate_corner(2.5, "typ")
    assert c.kintex_both_ok
    assert abs(c.vcm_v - 1.365) < 1e-9
    assert abs(c.vod_v - 0.395) < 1e-9


def test_pecl_3p3_typ_needs_translator_for_kintex():
    c = evaluate_corner(3.3, "typ")
    assert c.ds15_both_ok
    assert not c.kintex_vicm_ok  # CM ~2.16 V above LVDS_25 VICM max


def test_baseline_prefers_translator_path():
    d = baseline_decision()
    assert "DS15BR401" in d["poc_baseline"]
    assert d["direct_adcmp582_to_kintex_status"] == "optional_optimization_not_baseline"
    assert d["translator_typ_3p3_ds15_ok"]


def test_pecl_levels_corners_ordered():
    vod_min, _, _, _ = pecl_levels(3.3, "min")
    vod_typ, _, _, _ = pecl_levels(3.3, "typ")
    vod_max, _, _, _ = pecl_levels(3.3, "max")
    assert vod_min < vod_typ < vod_max


def test_set_utc_epoch_on_next_pps_applies_exactly_once():
    ctrl = UtcEpochController()
    ctrl.set_utc_epoch_on_next_pps(100)
    ev = ctrl.on_pps(pps_present=True, mhz_ok=True, coarse_phase_s=0.25, fine_phase_s=1e-12)
    assert ev["utc_second"] == 100
    assert ev["utc_valid"] is True
    assert abs(ev["timestamp_s"] - (100 + 0.25 + 1e-12)) < 1e-15
    ev2 = ctrl.on_pps(pps_present=True, mhz_ok=True, coarse_phase_s=0.0, fine_phase_s=0.0)
    assert ev2["utc_second"] == 101


def test_missing_pps_clears_utc_valid():
    ctrl = UtcEpochController()
    ctrl.set_utc_epoch_on_next_pps(50)
    ctrl.on_pps(pps_present=True, mhz_ok=True)
    ev = ctrl.on_pps(pps_present=False, mhz_ok=True)
    assert ev["utc_valid"] is False


def test_holdover_on_reference_loss():
    ctrl = UtcEpochController()
    ctrl.set_utc_epoch_on_next_pps(10)
    ctrl.on_pps(pps_present=True, mhz_ok=True)
    ev = ctrl.on_pps(pps_present=True, mhz_ok=False)
    assert ev["holdover"] is True
    assert ev["utc_valid"] is False
    assert ev["reference_loss"] is True


def test_channel_calibration_offset_in_timestamp():
    ctrl = UtcEpochController()
    ctrl.set_utc_epoch_on_next_pps(0)
    ev = ctrl.on_pps(
        pps_present=True,
        mhz_ok=True,
        coarse_phase_s=0.0,
        fine_phase_s=0.0,
        channel_cal_offset_s=5e-12,
    )
    assert abs(ev["timestamp_s"] - 5e-12) < 1e-18


def test_signed_interval_limits():
    ctrl = UtcEpochController()
    assert ctrl.signed_interval_s(0.0, 0.5) == 0.5
    assert ctrl.signed_interval_s(1.0, 0.0) == -1.0
    with pytest.raises(ValueError):
        ctrl.signed_interval_s(0.0, SIGNED_INTERVAL_LIMIT_S + 0.1)


def test_monotonic_sequence_increments():
    ctrl = UtcEpochController()
    ctrl.set_utc_epoch_on_next_pps(1)
    ctrl.on_pps(pps_present=True, mhz_ok=True)
    ctrl.on_pps(pps_present=True, mhz_ok=True)
    assert ctrl.sequence == 2
    assert ctrl.monotonic_ok is True
    assert ctrl.history[-1]["utc_second"] > ctrl.history[-2]["utc_second"]
