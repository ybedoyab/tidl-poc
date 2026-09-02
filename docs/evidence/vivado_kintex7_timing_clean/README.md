# Kintex-7 timing-clean structural benchmark

**Classification:** RTL/synthesis/implementation evidence.
**Vivado:** 2026.1. **Part:** `xc7k160tffg676-2`.
**Clock:** 4.000 ns on `clk` (synchronous capture/benchmark-control only).
**Asynchronous hit** inputs are narrowly false-pathed; `rst_n` into FDRE.R only.

This snapshot reran synthesis and place/route for channels {1,4,8,16} at
**64 CARRY4 per chain** after removing the Round-6 **benchmark-only wide XOR
parity tree**. Capture FFs are retained via `KEEP` / `DONT_TOUCH`; the top
exposes one registered bit per channel (chain-0 tap 0) as `bench_status`.

No physical timing measurement. No claim of 1 ps resolution, DNL, SSP,
accuracy, or temperature performance.

## Comparison to Round 6

| | Round 6 (`docs/evidence/vivado_kintex7/`) | This snapshot |
| --- | --- | --- |
| Observability | Wide `^captured_k` parity per chain, hierarchical XOR to `tap_parity` | KEEP on capture bank; one tap per channel registered |
| Matrix | 12 synth; 6 impl (32/48/64 sweep) | 4 impl @ 64 CARRY4/chain only |
| 8/16-ch P&R | `place_design -no_timing_driven` on some cases | Timing-driven place/route |
| WNS | Negative from 1ch/64 upward (likely parity tree) | See `implementation_summary.csv` |

Round-6 numbers are **not** overwritten. Resource deltas vs Round-6 @64 are
mostly LUT/FF reduction from removing parity XOR trees; CARRY4 and capture FF
counts should match structural expectations.

## Figures

- `resource_scaling.png` — slices / LUT / FF / CARRY4 vs channels @ 64 CARRY4/chain.
- `timing_scaling.png` — 4 ns WNS vs channels (not TDC-bin timing).
- `placement_16ch_64.png` — 16×64 LOC plot from Vivado text.

## Reproduce

```text
python -m tidl_poc vivado-timing-clean
python -m tidl_poc vivado-timing-clean --export-only
```

Raw Vivado trees stay gitignored under `outputs/vivado_kintex7_timing_clean/`.
