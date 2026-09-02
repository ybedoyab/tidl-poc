"""UTC epoch arming and timestamp composition model.

Classification: model-based simulation of control/state behaviour.
No UTC accuracy, NTP/PTP phase alignment, or physical 1 PPS claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir

SIGNED_INTERVAL_LIMIT_S = 1.0


@dataclass
class UtcEpochController:
    """SET_UTC_EPOCH_ON_NEXT_PPS behavioural model."""

    armed_label: int | None = None
    utc_second: int | None = None
    utc_valid: bool = False
    holdover: bool = False
    reference_loss: bool = False
    sequence: int = 0
    last_pps_seen: bool = False
    monotonic_ok: bool = True
    history: list[dict] = field(default_factory=list)

    def set_utc_epoch_on_next_pps(self, utc_second_label: int) -> None:
        """Arm integer UTC-second label for the next captured physical 1PPS."""
        if not isinstance(utc_second_label, int):
            raise TypeError("utc_second_label must be int")
        self.armed_label = utc_second_label

    def on_pps(
        self,
        *,
        pps_present: bool,
        mhz_ok: bool,
        coarse_phase_s: float = 0.0,
        fine_phase_s: float = 0.0,
        channel_cal_offset_s: float = 0.0,
    ) -> dict:
        """Advance one PPS epoch. Missing PPS clears utc_valid; no silent relabel."""
        event = {
            "pps_present": pps_present,
            "mhz_ok": mhz_ok,
            "armed_before": self.armed_label,
            "utc_second_before": self.utc_second,
        }
        if not mhz_ok:
            self.reference_loss = True
            self.holdover = True
            self.utc_valid = False
        if not pps_present:
            self.utc_valid = False
            self.reference_loss = True if not mhz_ok else self.reference_loss
            event.update(self._snapshot(None, coarse_phase_s, fine_phase_s, channel_cal_offset_s))
            self.history.append(event)
            self.last_pps_seen = False
            return event

        # Duplicate PPS while already processed this edge: ignore silent relabel.
        if self.last_pps_seen and self.armed_label is None and self.utc_second is not None:
            # Treat as a second consecutive PPS in the same conceptual slot only if
            # caller re-enters without clearing; increment normally below.
            pass

        if self.armed_label is not None:
            self.utc_second = self.armed_label
            self.armed_label = None
            self.utc_valid = mhz_ok
            self.holdover = not mhz_ok
            self.reference_loss = not mhz_ok
        elif self.utc_second is not None:
            prev = self.utc_second
            self.utc_second = prev + 1
            if self.utc_second <= prev:
                self.monotonic_ok = False
            self.utc_valid = mhz_ok and not self.reference_loss
            if not mhz_ok:
                self.holdover = True
                self.utc_valid = False
            else:
                # Successful PPS with frequency OK clears holdover after arm history.
                if self.holdover and mhz_ok:
                    self.holdover = False
                    self.reference_loss = False
                    self.utc_valid = True
        else:
            # PPS seen but epoch never armed → invalid UTC.
            self.utc_valid = False

        self.sequence += 1
        self.last_pps_seen = True
        ts = self.compose_timestamp(coarse_phase_s, fine_phase_s, channel_cal_offset_s)
        event.update(self._snapshot(ts, coarse_phase_s, fine_phase_s, channel_cal_offset_s))
        self.history.append(event)
        return event

    def compose_timestamp(
        self,
        coarse_phase_s: float,
        fine_phase_s: float,
        channel_cal_offset_s: float = 0.0,
    ) -> float | None:
        if self.utc_second is None or not self.utc_valid:
            return None
        return (
            float(self.utc_second)
            + float(coarse_phase_s)
            + float(fine_phase_s)
            + float(channel_cal_offset_s)
        )

    def signed_interval_s(self, t_a: float, t_b: float) -> float:
        delta = float(t_b) - float(t_a)
        if abs(delta) > SIGNED_INTERVAL_LIMIT_S + 1e-15:
            raise ValueError(f"interval {delta} s exceeds ±{SIGNED_INTERVAL_LIMIT_S} s")
        return delta

    def _snapshot(
        self,
        timestamp: float | None,
        coarse_phase_s: float,
        fine_phase_s: float,
        channel_cal_offset_s: float,
    ) -> dict:
        return {
            "utc_second": self.utc_second,
            "armed_after": self.armed_label,
            "utc_valid": self.utc_valid,
            "holdover": self.holdover,
            "reference_loss": self.reference_loss,
            "sequence": self.sequence,
            "timestamp_s": timestamp,
            "coarse_phase_s": coarse_phase_s,
            "fine_phase_s": fine_phase_s,
            "channel_cal_offset_s": channel_cal_offset_s,
            "monotonic_ok": self.monotonic_ok,
            "result_classification": "model-based simulation",
        }


def default_scenario() -> pd.DataFrame:
    ctrl = UtcEpochController()
    rows = []
    # Missing PPS before arm.
    rows.append(ctrl.on_pps(pps_present=False, mhz_ok=True))
    # Arm and apply on next PPS.
    ctrl.set_utc_epoch_on_next_pps(1_700_000_000)
    rows.append(ctrl.on_pps(pps_present=True, mhz_ok=True, coarse_phase_s=0.1, fine_phase_s=1e-12))
    # Normal increment.
    rows.append(ctrl.on_pps(pps_present=True, mhz_ok=True, coarse_phase_s=0.2, fine_phase_s=2e-12))
    # Missing PPS → invalid UTC.
    rows.append(ctrl.on_pps(pps_present=False, mhz_ok=True))
    # Restore PPS without re-arm: continue from last second + 1 only if we had a second;
    # model increments when PPS returns after a gap (one missed tick already lost).
    rows.append(ctrl.on_pps(pps_present=True, mhz_ok=True, coarse_phase_s=0.0, fine_phase_s=0.0))
    # Frequency loss → holdover / invalid.
    rows.append(ctrl.on_pps(pps_present=True, mhz_ok=False, coarse_phase_s=0.0, fine_phase_s=0.0))
    # Reacquire.
    rows.append(ctrl.on_pps(pps_present=True, mhz_ok=True, coarse_phase_s=0.0, fine_phase_s=0.0))
    return pd.DataFrame(rows)


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    del seed, fast
    out = outputs_dir("utc_timestamp")
    df = default_scenario()
    df.to_csv(out / "utc_epoch_script.csv", index=False)
    extra = {
        "n_rows": int(len(df)),
        "utc_valid_epochs": int(df["utc_valid"].sum()),
        "holdover_epochs": int(df["holdover"].sum()),
        "signed_interval_limit_s": SIGNED_INTERVAL_LIMIT_S,
        "ntp_ptp_for_picosecond_phase": False,
        "mechanism": "SET_UTC_EPOCH_ON_NEXT_PPS",
    }
    write_json(out / "summary.json", extra)
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.utc_timestamp",
        random_seed=DEFAULT_SEED,
        input_parameters={
            "mechanism": "SET_UTC_EPOCH_ON_NEXT_PPS",
            "timestamp": "UTC_second + coarse_phase + calibrated_fine_phase",
            "utc_accuracy_claimed": False,
            "parameter_provenance": "engineering architecture model",
        },
        extra=extra,
    )
    (out / "interpretation.md").write_text(
        f"""# UTC epoch arming model

**Classification:** model-based simulation.
No UTC accuracy claim. NTP/PTP must not be used for picosecond phase alignment.

Mechanism: `{extra["mechanism"]}`
UTC-valid epochs in script: {extra["utc_valid_epochs"]}
Holdover epochs: {extra["holdover_epochs"]}

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "table": df}
