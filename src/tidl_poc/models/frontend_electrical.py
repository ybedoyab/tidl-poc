"""ADCMP582 / Kintex-7 / DS15BR401 datasheet-level interface arithmetic.

Classification: external component evidence / datasheet arithmetic.
Not SPICE. Not laboratory measurement. High-speed DJ figures are not 1 PPS guarantees.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir

# ADCMP582 reduced-swing PECL output differential (Rev. B class facts).
ADCMP582_VOD_MV = {"min": 340.0, "typ": 395.0, "max": 450.0}
# Typical PECL common-mode anchors used for arithmetic (V).
# VCCO=3.3 V: manufacturer-typical CM ≈ 2.16 V.
# VCCO=2.5 V: VOH≈1.56, VOL≈1.17 → CM≈1.365 V.
ADCMP582_VCM_TYP_V = {2.5: 1.365, 3.3: 2.16}
# Propagation / jitter manufacturer anchors (not 1 PPS guarantees).
ADCMP582_TPD_TYP_PS = 180.0
ADCMP582_TPD_TC_PS_PER_C = 0.25
ADCMP582_RJ_RMS_PS = 0.2  # 200 fs under datasheet conditions
ADCMP582_DJ_PS = {
    "vod_500mv_5vns_prbs31_5gbps": 15.0,
    "vod_200mv_5vns_prbs31_10gbps": 25.0,
}

# Kintex-7 LVDS_25 (AMD DS182 class windows used in this repo).
KINTEX7_LVDS25_VIDIFF_V = (0.100, 0.600)
KINTEX7_LVDS25_VICM_V = (0.300, 1.500)

# TI DS15BR401 / DS15BR400 family input domain (product-page class facts).
DS15BR401_VID_V = (0.100, 2.400)
DS15BR401_VCM_V = (0.05, 3.55)
DS15BR401_RJ_TYP_PS = 0.5
DS15BR401_RJ_MAX_PS = 1.5


@dataclass(frozen=True)
class LevelCorner:
    vcco_v: float
    corner: str
    vod_v: float
    vcm_v: float
    voh_v: float
    vol_v: float
    kintex_vidiff_ok: bool
    kintex_vicm_ok: bool
    kintex_both_ok: bool
    ds15_vid_ok: bool
    ds15_vcm_ok: bool
    ds15_both_ok: bool
    note: str


def pecl_levels(vcco_v: float, corner: str) -> tuple[float, float, float, float]:
    """Return (vod_v, vcm_v, voh_v, vol_v) for ADCMP582 PECL arithmetic."""
    if vcco_v not in ADCMP582_VCM_TYP_V:
        raise ValueError(f"unsupported VCCO {vcco_v}")
    if corner not in ADCMP582_VOD_MV:
        raise ValueError(f"unsupported corner {corner}")
    vod_v = ADCMP582_VOD_MV[corner] / 1000.0
    # Hold CM at typ for all VOD corners unless a datasheet corner table is added.
    vcm_v = ADCMP582_VCM_TYP_V[vcco_v]
    voh_v = vcm_v + vod_v / 2.0
    vol_v = vcm_v - vod_v / 2.0
    return vod_v, vcm_v, voh_v, vol_v


def in_range(value: float, lo: float, hi: float, *, eps: float = 1e-9) -> bool:
    return (lo - eps) <= value <= (hi + eps)


def evaluate_corner(vcco_v: float, corner: str) -> LevelCorner:
    vod_v, vcm_v, voh_v, vol_v = pecl_levels(vcco_v, corner)
    k_vid = in_range(vod_v, *KINTEX7_LVDS25_VIDIFF_V)
    k_vicm = in_range(vcm_v, *KINTEX7_LVDS25_VICM_V)
    d_vid = in_range(vod_v, *DS15BR401_VID_V)
    d_vcm = in_range(vcm_v, *DS15BR401_VCM_V)
    note = "datasheet arithmetic; CM held at typ for VOD corners"
    if vcco_v == 2.5 and corner != "typ":
        note += "; worst-corner direct LVDS_25 margin not closed for baseline"
    if vcco_v == 3.3:
        note += "; VCCO=3.3 V PECL CM above Kintex LVDS_25 VICM max — translator path"
    return LevelCorner(
        vcco_v=vcco_v,
        corner=corner,
        vod_v=vod_v,
        vcm_v=vcm_v,
        voh_v=voh_v,
        vol_v=vol_v,
        kintex_vidiff_ok=k_vid,
        kintex_vicm_ok=k_vicm,
        kintex_both_ok=k_vid and k_vicm,
        ds15_vid_ok=d_vid,
        ds15_vcm_ok=d_vcm,
        ds15_both_ok=d_vid and d_vcm,
        note=note,
    )


def all_corners() -> list[LevelCorner]:
    rows: list[LevelCorner] = []
    for vcco in (2.5, 3.3):
        for corner in ("min", "typ", "max"):
            rows.append(evaluate_corner(vcco, corner))
    return rows


def baseline_decision(rows: list[LevelCorner] | None = None) -> dict:
    rows = rows or all_corners()
    typ_25 = next(r for r in rows if r.vcco_v == 2.5 and r.corner == "typ")
    typ_33 = next(r for r in rows if r.vcco_v == 3.3 and r.corner == "typ")
    all_25_ok = all(r.kintex_both_ok for r in rows if r.vcco_v == 2.5)
    translator_ok = all(r.ds15_both_ok for r in rows if r.vcco_v == 3.3)
    return {
        "poc_baseline": "ADCMP582 (VCCO=3.3 V) → PECL termination → DS15BR401 → Kintex-7 LVDS",
        "direct_adcmp582_to_kintex_status": "optional_optimization_not_baseline",
        "direct_typ_2p5_kintex_ok": typ_25.kintex_both_ok,
        "direct_all_corners_2p5_kintex_ok": all_25_ok,
        "translator_typ_3p3_ds15_ok": typ_33.ds15_both_ok,
        "translator_all_corners_3p3_ds15_ok": translator_ok,
        "why_ds15br401_not_400": (
            "ADCMP582 PECL wants 50 Ω from each output to VCCO−2 V; "
            "DS15BR401 lacks internal input termination so external PECL "
            "termination is not paralleled with DS15BR400's 100 Ω input."
        ),
        "dj_not_1pps_guarantee": True,
        "classification": "datasheet arithmetic / external component evidence",
    }


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    del seed, fast
    out = outputs_dir("frontend_electrical")
    rows = all_corners()
    df = pd.DataFrame([asdict(r) for r in rows])
    df.to_csv(out / "level_corners.csv", index=False)
    decision = baseline_decision(rows)
    write_json(out / "summary.json", {**decision, "corners": [asdict(r) for r in rows]})
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.frontend_electrical",
        random_seed=DEFAULT_SEED,
        input_parameters={
            "adcmp582_vod_mv": ADCMP582_VOD_MV,
            "adcmp582_vcm_typ_v": ADCMP582_VCM_TYP_V,
            "kintex7_lvds25_vidiff_v": KINTEX7_LVDS25_VIDIFF_V,
            "kintex7_lvds25_vicm_v": KINTEX7_LVDS25_VICM_V,
            "ds15br401_vid_v": DS15BR401_VID_V,
            "ds15br401_vcm_v": DS15BR401_VCM_V,
            "parameter_provenance": "manufacturer datasheet arithmetic; not SPICE/lab",
        },
        extra=decision,
    )
    (out / "interpretation.md").write_text(
        f"""# Front-end electrical datasheet arithmetic

**Classification:** datasheet arithmetic / external component evidence.
Not SPICE. Not laboratory measurement.

POC baseline: `{decision["poc_baseline"]}`

Direct ADCMP582 VCCO=2.5 V → Kintex-7 LVDS_25: typ OK={decision["direct_typ_2p5_kintex_ok"]},
all corners OK={decision["direct_all_corners_2p5_kintex_ok"]}
→ status: `{decision["direct_adcmp582_to_kintex_status"]}`.

Translator path VCCO=3.3 V → DS15BR401: typ OK={decision["translator_typ_3p3_ds15_ok"]},
all corners OK={decision["translator_all_corners_3p3_ds15_ok"]}.

High-speed DJ figures are pattern-specific and are **not** 1 PPS guarantees.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "table": df, "decision": decision}
