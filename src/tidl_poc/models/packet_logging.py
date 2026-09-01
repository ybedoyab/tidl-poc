"""UDP delivery plus internal backup-log reconciliation.

Classification: model-based simulation of a software/data-path. Not a network test.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure
from tidl_poc.common.rng import rng as make_rng

RECORD_FIELDS = (
    "utc_epoch",
    "coarse_count",
    "channel",
    "fine_timestamp_ps",
    "sequence",
    "quality_bits",
    "calibration_version",
    "crc32",
)


def crc32_concept(payload: bytes) -> int:
    """IEEE CRC-32 (0xEDB88320). Conceptual integrity field, not a protocol claim."""
    crc = 0xFFFFFFFF
    for byte in payload:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xEDB88320 if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def make_records(n: int, n_channels: int = 16) -> pd.DataFrame:
    rows = []
    for seq in range(n):
        ch = seq % n_channels
        utc_epoch = seq // n_channels
        coarse = utc_epoch * 100_000_000
        fine = (seq * 17) % 4000
        quality = 0x11
        cal = 1
        payload = f"{utc_epoch},{coarse},{ch},{fine},{seq},{quality},{cal}".encode()
        rows.append(
            {
                "utc_epoch": utc_epoch,
                "coarse_count": coarse,
                "channel": ch,
                "fine_timestamp_ps": fine,
                "sequence": seq,
                "quality_bits": quality,
                "calibration_version": cal,
                "crc32": crc32_concept(payload),
                "result_classification": "model-based simulation",
            }
        )
    return pd.DataFrame(rows)


def udp_impair(records: pd.DataFrame, rng: np.random.Generator, drop_p: float, dup_p: float, reorder_frac: float) -> pd.DataFrame:
    kept = []
    for _, row in records.iterrows():
        if rng.random() < drop_p:
            continue
        kept.append(row.to_dict())
        if rng.random() < dup_p:
            kept.append(row.to_dict())
    frame = pd.DataFrame(kept)
    if len(frame) == 0:
        return frame
    n_swap = int(len(frame) * reorder_frac)
    for _ in range(n_swap):
        i, j = rng.integers(0, len(frame), size=2)
        a, b = frame.iloc[i].copy(), frame.iloc[j].copy()
        frame.iloc[i], frame.iloc[j] = b, a
    return frame.reset_index(drop=True)


def reconcile(internal: pd.DataFrame, udp: pd.DataFrame) -> dict:
    truth = set(internal["sequence"].tolist())
    received = set(udp["sequence"].tolist()) if len(udp) else set()
    recovered = truth  # internal log intact
    return {
        "n_truth": len(truth),
        "n_udp_unique": len(received),
        "n_udp_rows": int(len(udp)),
        "udp_loss_unique": len(truth - received),
        "n_duplicates_in_udp": int(len(udp) - len(received)) if len(udp) else 0,
        "reconciled_unique": len(recovered),
        "measurement_loss_if_log_intact": 0,
        "external_loss_implies_measurement_loss": False,
    }


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    out = outputs_dir("packet_logging")
    gen = make_rng(seed)
    n = 256 if fast else 4096
    internal = make_records(n)
    udp = udp_impair(internal, gen, drop_p=0.08, dup_p=0.03, reorder_frac=0.05)
    stats = reconcile(internal, udp)
    internal.to_csv(out / "internal_log.csv", index=False)
    udp.to_csv(out / "udp_received.csv", index=False)
    pd.DataFrame([stats]).to_csv(out / "reconciliation.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(
        ["truth", "UDP unique", "reconciled via internal log"],
        [stats["n_truth"], stats["n_udp_unique"], stats["reconciled_unique"]],
        color="0.5",
    )
    ax.set_ylabel("Unique sequence numbers")
    ax.set_title("UDP impairment vs internal-log replay (software model)")
    save_figure(fig, out / "reconciliation")

    params = {
        "n_records": n,
        "n_channels": 16,
        "drop_p": 0.08,
        "dup_p": 0.03,
        "reorder_frac": 0.05,
        "record_fields": list(RECORD_FIELDS),
        "parameter_provenance": "impairment rates are engineering assumptions",
        "fast": fast,
        "evidence_scope": "software/data-path feasibility only",
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.packet_logging",
        random_seed=seed,
        input_parameters=params,
        extra=stats,
    )
    write_json(out / "summary.json", stats)
    (out / "interpretation.md").write_text(
        f"""# UDP + internal backup logging

**Classification:** model-based simulation of a data path. Not a network or storage test.

Record fields: {", ".join(RECORD_FIELDS)}

Truth records = {stats["n_truth"]}
UDP unique received = {stats["n_udp_unique"]}
UDP unique loss = {stats["udp_loss_unique"]}
Reconciled unique if internal log intact = {stats["reconciled_unique"]}
Measurement loss if log intact = {stats["measurement_loss_if_log_intact"]}

External packet loss does not imply measurement loss while the internal log remains intact.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "stats": stats}
