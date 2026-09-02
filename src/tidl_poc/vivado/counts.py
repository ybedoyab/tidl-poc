"""Kintex-7 structural TDC resource formulas. Independent of Vivado."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructuralCounts:
    channels: int
    chains_per_channel: int
    carry4_per_chain: int
    carry4: int
    taps: int
    capture_ff_min: int

    def optimized_away(self, mapped_carry4: int | None, *, tolerance: float = 0.95) -> bool:
        if mapped_carry4 is None:
            return False
        return mapped_carry4 < self.carry4 * tolerance


def expected_counts(
    channels: int,
    chains_per_channel: int,
    carry4_per_chain: int,
) -> StructuralCounts:
    if channels < 1 or chains_per_channel < 1 or carry4_per_chain < 1:
        raise ValueError("channels, chains_per_channel, and carry4_per_chain must be >= 1")
    carry4 = channels * chains_per_channel * carry4_per_chain
    taps = carry4 * 4
    return StructuralCounts(
        channels=channels,
        chains_per_channel=chains_per_channel,
        carry4_per_chain=carry4_per_chain,
        carry4=carry4,
        taps=taps,
        capture_ff_min=taps,
    )
