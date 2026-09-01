"""UTC / 10 MHz / 1 PPS reference behavioural model.

Classification: model-based simulation of flags and state, not UTC accuracy.
No time-error in seconds is claimed.
"""

from __future__ import annotations

from enum import IntEnum

import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure


class RefState(IntEnum):
    SEARCH = 0
    QUALIFYING = 1
    LOCKED = 2
    HOLDOVER = 3
    REACQUIRE = 4


# Quality bits (concept only).
Q_10MHZ_PRESENT = 1 << 0
Q_10MHZ_QUALIFIED = 1 << 1
Q_1PPS_PRESENT = 1 << 2
Q_1PPS_ALIGNED = 1 << 3
Q_UTC_VALID = 1 << 4
Q_HOLDOVER = 1 << 5


def step(
    state: RefState,
    mhz_ok: bool,
    pps_ok: bool,
    qualify_count: int,
    qualify_needed: int = 3,
) -> tuple[RefState, int, int]:
    """Advance one 1 PPS epoch. Returns (state, new_qualify_count, quality_bits)."""
    bits = 0
    if mhz_ok:
        bits |= Q_10MHZ_PRESENT
    if pps_ok:
        bits |= Q_1PPS_PRESENT

    if state == RefState.SEARCH:
        qualify_count = 0
        if mhz_ok:
            state = RefState.QUALIFYING
    elif state == RefState.QUALIFYING:
        if not mhz_ok:
            state = RefState.SEARCH
            qualify_count = 0
        elif pps_ok:
            qualify_count += 1
            bits |= Q_10MHZ_QUALIFIED
            if qualify_count >= qualify_needed:
                state = RefState.LOCKED
                bits |= Q_1PPS_ALIGNED | Q_UTC_VALID
        else:
            qualify_count = 0
            bits |= Q_10MHZ_QUALIFIED
    elif state == RefState.LOCKED:
        bits |= Q_10MHZ_QUALIFIED | Q_1PPS_ALIGNED | Q_UTC_VALID
        if not mhz_ok or not pps_ok:
            state = RefState.HOLDOVER
            bits = (bits & ~Q_UTC_VALID) | Q_HOLDOVER
            if mhz_ok:
                bits |= Q_10MHZ_PRESENT | Q_10MHZ_QUALIFIED
            if pps_ok:
                bits |= Q_1PPS_PRESENT
    elif state == RefState.HOLDOVER:
        bits |= Q_HOLDOVER
        if mhz_ok:
            bits |= Q_10MHZ_PRESENT
        if pps_ok:
            bits |= Q_1PPS_PRESENT
        if mhz_ok and pps_ok:
            state = RefState.REACQUIRE
            qualify_count = 0
    elif state == RefState.REACQUIRE:
        bits |= Q_HOLDOVER
        if not mhz_ok:
            state = RefState.HOLDOVER
            qualify_count = 0
        elif pps_ok:
            qualify_count += 1
            bits |= Q_10MHZ_PRESENT | Q_10MHZ_QUALIFIED | Q_1PPS_PRESENT
            if qualify_count >= qualify_needed:
                state = RefState.LOCKED
                bits = Q_10MHZ_PRESENT | Q_10MHZ_QUALIFIED | Q_1PPS_PRESENT | Q_1PPS_ALIGNED | Q_UTC_VALID
        else:
            bits |= Q_10MHZ_PRESENT | Q_10MHZ_QUALIFIED
    return state, qualify_count, bits


def run_script(events: list[tuple[bool, bool]], qualify_needed: int = 3) -> pd.DataFrame:
    state = RefState.SEARCH
    q = 0
    rows = []
    for epoch, (mhz_ok, pps_ok) in enumerate(events):
        state, q, bits = step(state, mhz_ok, pps_ok, q, qualify_needed)
        rows.append(
            {
                "epoch": epoch,
                "mhz_ok": mhz_ok,
                "pps_ok": pps_ok,
                "state": state.name,
                "state_id": int(state),
                "utc_valid": bool(bits & Q_UTC_VALID),
                "holdover": bool(bits & Q_HOLDOVER),
                "quality_bits": bits,
                "result_classification": "model-based simulation",
            }
        )
    return pd.DataFrame(rows)


def default_scenario() -> list[tuple[bool, bool]]:
    """Qualify, lock, lose PPS, holdover, restore, reacquire, lock."""
    events: list[tuple[bool, bool]] = []
    events += [(False, False)] * 2
    events += [(True, False)] * 2
    events += [(True, True)] * 6
    events += [(True, False)] * 4  # PPS loss
    events += [(False, False)] * 2  # both lost
    events += [(True, True)] * 8  # restore
    return events


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    del seed, fast
    out = outputs_dir("reference_clock")
    df = run_script(default_scenario())
    df.to_csv(out / "reference_state.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.step(df["epoch"], df["state_id"], where="post", color="0.1")
    ax.set_yticks(list(range(len(RefState))), [s.name for s in RefState])
    ax.set_xlabel("1 PPS epoch (conceptual)")
    ax.set_ylabel("Reference state")
    ax.set_title("10 MHz / 1 PPS state machine (flags only; no UTC accuracy claim)")
    save_figure(fig, out / "reference_state")

    locked = df[df["state"] == "LOCKED"]
    hold = df[df["state"] == "HOLDOVER"]
    params = {
        "qualify_needed_pps_epochs": 3,
        "scenario": "search, qualify, lock, PPS loss, both loss, restore, reacquire",
        "utc_accuracy_claimed": False,
        "parameter_provenance": "engineering assumption for qualify count; no oscillator model",
    }
    extra = {
        "n_locked_epochs": int(len(locked)),
        "n_holdover_epochs": int(len(hold)),
        "utc_valid_only_when_locked": bool((~df["utc_valid"] | (df["state"] == "LOCKED")).all()),
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.utc_reference",
        random_seed=DEFAULT_SEED,
        input_parameters=params,
        extra=extra,
    )
    write_json(out / "summary.json", extra)
    (out / "interpretation.md").write_text(
        f"""# UTC / 10 MHz / 1 PPS conceptual model

**Classification:** model-based simulation of state and quality flags.
No UTC time-error allocation has been validated. Holdover is a flag, not a
specified oscillator holdover specification.

Locked epochs = {extra["n_locked_epochs"]}
Holdover epochs = {extra["n_holdover_epochs"]}
utc_valid asserted only in LOCKED: {extra["utc_valid_only_when_locked"]}

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "table": df}
