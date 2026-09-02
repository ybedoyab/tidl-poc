"""MSWU-inspired structural resource formulas (independent of Vivado)."""

from __future__ import annotations

from dataclasses import dataclass

# Paper anchor: 200 logical carry taps. Kintex-7 CARRY4 exposes 4 CO taps each.
MSWU_LOGICAL_TAPS = 200
MSWU_CARRY4_PER_TDL = MSWU_LOGICAL_TAPS // 4  # 50
MSWU_CAPTURE_BANKS = 4
MSWU_MBD_SUB_BITS = 40
MSWU_MBD_PARTITIONS = 5
MSWU_PREENC_OUT_BITS = 11
# Minimum LUT delta vs core-only for a valid preencoder resource measurement.
MSWU_MIN_PREENC_LUT_DELTA = 40
# Sequential mode: 1 scanner + 1 encoder; parallel: 20 encoders.
MSWU_PREENC_SEQ_INSTANCES = 1
MSWU_PREENC_PARALLEL_INSTANCES = 20


@dataclass(frozen=True)
class MswuStructuralCounts:
    channels: int
    carry4_per_tdl: int
    capture_banks: int
    logical_taps: int
    carry4: int
    capture_ff_min: int

    def optimized_away(self, mapped_carry4: int | None, *, tolerance: float = 0.95) -> bool:
        if mapped_carry4 is None:
            return False
        return mapped_carry4 < self.carry4 * tolerance


def expected_mswu_counts(channels: int) -> MswuStructuralCounts:
    if channels < 1:
        raise ValueError("channels must be >= 1")
    carry4 = channels * MSWU_CARRY4_PER_TDL
    capture_ff = channels * MSWU_CAPTURE_BANKS * MSWU_LOGICAL_TAPS
    return MswuStructuralCounts(
        channels=channels,
        carry4_per_tdl=MSWU_CARRY4_PER_TDL,
        capture_banks=MSWU_CAPTURE_BANKS,
        logical_taps=MSWU_LOGICAL_TAPS,
        carry4=carry4,
        capture_ff_min=capture_ff,
    )


def mbd_partition_ranges(n_taps: int = MSWU_LOGICAL_TAPS, sub_bits: int = MSWU_MBD_SUB_BITS) -> list[tuple[int, int]]:
    """Inclusive start/end indices for MBD=5 partitions. No gaps or overlap."""
    n_sub = n_taps // sub_bits
    ranges: list[tuple[int, int]] = []
    for i in range(n_sub):
        start = i * sub_bits
        end = start + sub_bits - 1
        ranges.append((start, end))
    return ranges
