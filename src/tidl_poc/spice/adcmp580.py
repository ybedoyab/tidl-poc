"""ADCMP580 LTspice characterization (SPICE/front-end simulation).

Not laboratory evidence. Not S14 compliance. The Analog Devices macromodel
stays in the local LTspice library and is not copied into Git.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from tidl_poc import DEFAULT_SEED, SPICE_DISCLAIMER, SPICE_RESULT_CLASSIFICATION
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir, repo_root
from tidl_poc.common.plotting import plt, save_figure
from tidl_poc.spice.ltspice import (
    find_adcmp580_library,
    find_ltspice,
    log_has_model_error,
    ltspice_version,
    parse_meas_log,
    read_log,
    run_batch,
    switched_clean,
)

SCHEMATIC_REL = Path("spice") / "adcmp580" / "tidl_adcmp580_characterization.asc"

OVERDRIVES_V = (0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500)
SLEWS_V_PER_NS = (1.0, 2.0, 5.0, 10.0)
POLARITIES = ("rise", "fall")
RISE_TIMES_S = (100e-12, 250e-12, 500e-12, 1e-9, 2e-9, 5e-9)

# Engineering testbench parameters — not a challenge 1 PPS specification.
CHAR_THRESHOLD_V = 0.0
CHAR_AMPLITUDE_V = 0.4

DATASHEET_TPD_TYP_PS = 180.0
DATASHEET_DISP_DETAILED_LT_PS = 25.0
DATASHEET_DISP_OVERVIEW_TYP_LT_PS = 15.0

DISPERSION_CSV_COLUMNS = (
    "overdrive_v",
    "slew_v_per_ns",
    "polarity",
    "t_in_s",
    "t_out_s",
    "tpd_s",
    "tpd_ps",
    "vout_max_v",
    "vout_min_v",
    "t_r_out_s",
    "switched_clean",
    "meas_ok",
)
RISE_CSV_COLUMNS = (
    "rise_time_s",
    "amplitude_v",
    "threshold_v",
    "polarity",
    "t_in_s",
    "t_out_s",
    "tpd_s",
    "tpd_ps",
    "vout_max_v",
    "vout_min_v",
    "t_r_out_s",
    "switched_clean",
    "meas_ok",
)


def schematic_path() -> Path:
    return repo_root() / SCHEMATIC_REL


def schematic_hash(path: Path | None = None) -> str:
    data = (path or schematic_path()).read_bytes()
    return hashlib.sha256(data).hexdigest()


def generate_dispersion_cases(*, fast: bool = False) -> list[dict[str, Any]]:
    vods = (0.050, 0.500) if fast else OVERDRIVES_V
    slews = (1.0, 10.0) if fast else SLEWS_V_PER_NS
    pols = ("rise",) if fast else POLARITIES
    cases: list[dict[str, Any]] = []
    for vod in vods:
        for slew in slews:
            for pol in pols:
                cases.append(
                    {
                        "mode": "dispersion",
                        "overdrive_v": float(vod),
                        "slew_v_per_ns": float(slew),
                        "polarity": pol,
                    }
                )
    return cases


def generate_rise_cases(*, fast: bool = False) -> list[dict[str, Any]]:
    times = (100e-12, 5e-9) if fast else RISE_TIMES_S
    pols = ("rise",) if fast else POLARITIES
    cases: list[dict[str, Any]] = []
    for tr in times:
        for pol in pols:
            cases.append(
                {
                    "mode": "rise_time",
                    "rise_time_s": float(tr),
                    "amplitude_v": CHAR_AMPLITUDE_V,
                    "threshold_v": CHAR_THRESHOLD_V,
                    "polarity": pol,
                }
            )
    return cases


def generate_sweep_cases(*, fast: bool = False) -> list[dict[str, Any]]:
    return generate_dispersion_cases(fast=fast) + generate_rise_cases(fast=fast)


def polarity_sign(polarity: str) -> int:
    if polarity == "rise":
        return 1
    if polarity == "fall":
        return -1
    raise ValueError(f"unknown polarity {polarity!r}")


def polarity_from_sign(value: float) -> str:
    return "rise" if float(value) >= 0 else "fall"


def propagation_dispersion_ps(tpd_s: list[float]) -> float:
    if not tpd_s:
        raise ValueError("tpd_s must be non-empty")
    return (max(tpd_s) - min(tpd_s)) * 1e12


def _spice_list(values: list[float], scale: str = "") -> str:
    parts = []
    for v in values:
        if scale == "p":
            parts.append(f"{v * 1e12:g}p")
        else:
            parts.append(f"{v:g}")
    return " ".join(parts)


def _step_or_param(name: str, values: list[float], *, scale: str = "") -> str:
    if len(values) == 1:
        if scale == "p":
            return f".param {name}={values[0] * 1e12:g}p"
        return f".param {name}={values[0]:g}"
    return f".step param {name} list {_spice_list(values, scale=scale)}"


def characterization_netlist(*, mode: str, fast: bool) -> str:
    """Original project netlist. Topology matches the committed .asc; not a vendor copy."""
    if mode == "dispersion":
        cases = generate_dispersion_cases(fast=fast)
        vods = []
        slews = []
        pols = []
        for case in cases:
            if case["overdrive_v"] not in vods:
                vods.append(case["overdrive_v"])
            s = case["slew_v_per_ns"] * 1e9
            if s not in slews:
                slews.append(s)
            p = float(polarity_sign(case["polarity"]))
            if p not in pols:
                pols.append(p)
        param_block = f"""\
.param Vth={CHAR_THRESHOLD_V} Td=200p Amp={CHAR_AMPLITUDE_V}
.param Tr={{2*Vod/Slew}}
.param Vstart={{Vth-Pol*Vod}} Vstop={{Vth+Pol*Vod}}
{_step_or_param("Vod", vods)}
{_step_or_param("Slew", slews)}
{_step_or_param("Pol", pols)}
"""
    elif mode == "rise_time":
        cases = generate_rise_cases(fast=fast)
        times = []
        pols = []
        for case in cases:
            if case["rise_time_s"] not in times:
                times.append(case["rise_time_s"])
            p = float(polarity_sign(case["polarity"]))
            if p not in pols:
                pols.append(p)
        param_block = f"""\
.param Vth={CHAR_THRESHOLD_V} Vod={CHAR_AMPLITUDE_V/2} Td=200p Amp={CHAR_AMPLITUDE_V}
.param Slew=1
.param Vstart={{Vth-Pol*Amp/2}} Vstop={{Vth+Pol*Amp/2}}
{_step_or_param("Tr", times, scale="p")}
{_step_or_param("Pol", pols)}
"""
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return f"""* TIDL original ADCMP580 characterization netlist (not a vendor example copy).
* Latch compare-mode: LE=0.4, _LE=0, VTT=0. HYS left open. VTP/VTN=0.
Vin VP 0 PWL(0 {{Vstart}} {{Td}} {{Vstart}} {{Td+Tr}} {{Vstop}})
Vth VN 0 {{Vth}}
Vvcc VCCI 0 5
Vvee VEE 0 -5
Vle LE 0 0.4
RQ Q 0 50
RQB QB 0 50
XU1 0 VP VN 0 VCCI 0 LE 0 0 QB Q VEE HYSOPEN ADCMP580
{param_block}.param Tstop={{Td+Tr+2n}}
.tran 0 {{Tstop}}
.options plotwinsize=0 numdgt=10
.meas TRAN t_in WHEN V(VP)-V(VN)=0 CROSS=1
.meas TRAN t_out WHEN V(Q)-V(QB)=0 CROSS=1
.meas TRAN tpd PARAM t_out-t_in
.meas TRAN vout_max MAX V(Q)-V(QB)
.meas TRAN vout_min MIN V(Q)-V(QB)
.meas TRAN t_q_lo WHEN V(Q)-V(QB)=-0.24 CROSS=1
.meas TRAN t_q_hi WHEN V(Q)-V(QB)=0.24 CROSS=1
.meas TRAN t_r_out PARAM abs(t_q_hi-t_q_lo)
.lib ADCMP580.sub
.end
"""


def _as_list(value: Any, n: int) -> list[Any]:
    if isinstance(value, list):
        if len(value) == n:
            return value
        if len(value) == 1:
            return value * n
        raise ValueError(f"expected {n} stepped values, got {len(value)}")
    return [value] * n


def _zip_meas(meas: dict[str, Any], n: int) -> list[dict[str, Any]]:
    keys = ("t_in", "t_out", "tpd", "vout_max", "vout_min", "t_r_out")
    columns = {k: _as_list(meas.get(k), n) for k in keys}
    failed = set(meas.get("_failed") or [])
    rows = []
    for i in range(n):
        one = {k: columns[k][i] for k in keys}
        one["_failed"] = sorted(failed)
        rows.append(_row_from_meas(one))
    return rows


def _row_from_meas(meas: dict[str, Any]) -> dict[str, Any]:
    def f(key: str) -> float | None:
        val = meas.get(key)
        if val is None or key in set(meas.get("_failed") or []):
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    t_in = f("t_in")
    t_out = f("t_out")
    tpd = f("tpd")
    if tpd is None and t_in is not None and t_out is not None:
        tpd = t_out - t_in
    vmax = f("vout_max")
    vmin = f("vout_min")
    tr_out = f("t_r_out")
    ok = tpd is not None and vmax is not None and vmin is not None
    clean = bool(ok and switched_clean(float(vmax), float(vmin)))
    return {
        "t_in_s": t_in,
        "t_out_s": t_out,
        "tpd_s": tpd,
        "tpd_ps": None if tpd is None else tpd * 1e12,
        "vout_max_v": vmax,
        "vout_min_v": vmin,
        "t_r_out_s": tr_out,
        "switched_clean": clean,
        "meas_ok": bool(ok and tpd is not None and tpd > 0),
    }


def _run_stepped(
    ltspice_exe: Path,
    lib_sub: Path,
    work: Path,
    stem: str,
    mode: str,
    fast: bool,
) -> list[dict[str, Any]]:
    cir = work / f"{stem}.cir"
    cir.write_text(characterization_netlist(mode=mode, fast=fast), encoding="utf-8")
    proc = run_batch(ltspice_exe, cir, include_path=lib_sub)
    log_path = work / f"{stem}.log"
    if not log_path.is_file():
        err = (proc.stderr or b"").decode("utf-8", errors="replace")
        raise RuntimeError(f"LTspice produced no log for {stem}: {err[:800]}")
    text = read_log(log_path)
    if log_has_model_error(text):
        raise RuntimeError(f"LTspice model/library resolution failed for {stem}")
    meas = parse_meas_log(text)
    if mode == "dispersion":
        cases = generate_dispersion_cases(fast=fast)
    else:
        cases = generate_rise_cases(fast=fast)
    rows_meas = _zip_meas(meas, len(cases))
    merged = [{**case, **row} for case, row in zip(cases, rows_meas, strict=True)]
    for leftover in work.glob(f"{stem}.raw"):
        leftover.unlink(missing_ok=True)
    return merged


def _write_plots(disp, rise, out: Path) -> None:
    if not disp.empty and disp["meas_ok"].any():
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        for slew, grp in disp[disp["meas_ok"]].groupby("slew_v_per_ns"):
            for pol, sub in grp.groupby("polarity"):
                ax.plot(
                    sub["overdrive_v"] * 1e3,
                    sub["tpd_ps"],
                    marker="o",
                    label=f"{slew:g} V/ns {pol}",
                )
        ax.set_xlabel("Overdrive (mV)")
        ax.set_ylabel("Propagation delay (ps)")
        ax.set_title("ADCMP580 SPICE tpd vs overdrive (not lab data)")
        ax.legend(fontsize=8)
        save_figure(fig, out / "tpd_vs_overdrive")

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        for vod, grp in disp[disp["meas_ok"]].groupby("overdrive_v"):
            for pol, sub in grp.groupby("polarity"):
                ax.plot(
                    sub["slew_v_per_ns"],
                    sub["tpd_ps"],
                    marker="o",
                    label=f"{vod*1e3:.0f} mV {pol}",
                )
        ax.set_xlabel("Slew rate (V/ns)")
        ax.set_ylabel("Propagation delay (ps)")
        ax.set_title("ADCMP580 SPICE tpd vs slew (not lab data)")
        ax.legend(fontsize=8)
        save_figure(fig, out / "tpd_vs_slew")

        if set(disp["polarity"]) >= {"rise", "fall"}:
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)
            piv = (
                disp[disp["meas_ok"]]
                .pivot_table(
                    index=["overdrive_v", "slew_v_per_ns"],
                    columns="polarity",
                    values="tpd_ps",
                )
                .reset_index()
            )
            if "rise" in piv.columns and "fall" in piv.columns:
                ax.scatter(piv["rise"], piv["fall"])
                lo = min(piv["rise"].min(), piv["fall"].min())
                hi = max(piv["rise"].max(), piv["fall"].max())
                ax.plot([lo, hi], [lo, hi], linestyle="--", color="0.4")
                ax.set_xlabel("Rise tpd (ps)")
                ax.set_ylabel("Fall tpd (ps)")
                ax.set_title("ADCMP580 SPICE rise vs fall delay (not lab data)")
                save_figure(fig, out / "tpd_rise_vs_fall")
            else:
                plt.close(fig)

    if not rise.empty and rise["meas_ok"].any():
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        for pol, sub in rise[rise["meas_ok"]].groupby("polarity"):
            ax.semilogx(sub["rise_time_s"] * 1e12, sub["tpd_ps"], marker="o", label=pol)
        ax.set_xlabel("Input edge rise time (ps, SPICE Tr 0-100%)")
        ax.set_ylabel("Propagation delay (ps)")
        ax.set_title("ADCMP580 SPICE tpd vs edge rise time (not lab data)")
        ax.legend()
        save_figure(fig, out / "tpd_vs_rise_time")


def run(
    *,
    fast: bool = True,
    ltspice: Path | None = None,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    del seed
    import pandas as pd

    out = outputs_dir("spice_adcmp580")
    work = out / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    exe = find_ltspice(ltspice)
    libs = find_adcmp580_library(exe)
    write_json(
        out / "local_paths.json",
        {
            "ltspice_exe": str(exe) if exe else None,
            "library": libs,
            "note": "Machine-local paths. Gitignored. Do not copy into tracked docs.",
        },
    )
    if exe is None:
        raise RuntimeError("LTspice.exe not found. Pass --ltspice or set TIDL_LTSPICE.")
    if "model" not in libs or "symbol" not in libs:
        raise RuntimeError(
            "Installed ADCMP580 symbol/model not found under %LOCALAPPDATA%\\LTspice. "
            "Open LTspice, F2, confirm ADCMP580, then re-run."
        )
    lib_sub = Path(libs["model"]).parent
    version = ltspice_version(exe)

    disp_rows = _run_stepped(exe, lib_sub, work, "dispersion", "dispersion", fast)
    rise_rows = _run_stepped(exe, lib_sub, work, "rise_time", "rise_time", fast)

    disp = pd.DataFrame(disp_rows)
    rise = pd.DataFrame(rise_rows)
    disp.to_csv(out / "dispersion.csv", index=False)
    rise.to_csv(out / "rise_time_sensitivity.csv", index=False)
    _write_plots(disp, rise, out)

    ok_tpd = [float(x) for x in disp.loc[disp["meas_ok"], "tpd_s"].tolist()] if not disp.empty else []
    extra = {
        "ltspice_version": version,
        "schematic_hash_sha256": schematic_hash(),
        "fast": fast,
        "n_dispersion_cases": int(len(disp_rows)),
        "n_rise_cases": int(len(rise_rows)),
        "n_dispersion_ok": int(disp["meas_ok"].sum()) if not disp.empty else 0,
        "mean_tpd_ps": None if not ok_tpd else (sum(ok_tpd) / len(ok_tpd)) * 1e12,
        "min_tpd_ps": None if not ok_tpd else min(ok_tpd) * 1e12,
        "max_tpd_ps": None if not ok_tpd else max(ok_tpd) * 1e12,
        "dispersion_ps": None if len(ok_tpd) < 2 else propagation_dispersion_ps(ok_tpd),
        "datasheet_tpd_typ_ps": DATASHEET_TPD_TYP_PS,
        "datasheet_disp_detailed_lt_ps": DATASHEET_DISP_DETAILED_LT_PS,
        "datasheet_disp_overview_typ_lt_ps": DATASHEET_DISP_OVERVIEW_TYP_LT_PS,
        "tpd_sim_minus_datasheet_typ_ps": None
        if not ok_tpd
        else (sum(ok_tpd) / len(ok_tpd)) * 1e12 - DATASHEET_TPD_TYP_PS,
        "char_amplitude_v": CHAR_AMPLITUDE_V,
        "char_threshold_v": CHAR_THRESHOLD_V,
        "char_amplitude_is_challenge_spec": False,
        "random_jitter_inferred": False,
        "hardware_measured": False,
    }
    params = {
        "schematic": str(SCHEMATIC_REL).replace("\\", "/"),
        "overdrives_v": list(OVERDRIVES_V if not fast else (0.050, 0.500)),
        "slews_v_per_ns": list(SLEWS_V_PER_NS if not fast else (1.0, 10.0)),
        "rise_times_s": list(RISE_TIMES_S if not fast else (100e-12, 5e-9)),
        "polarities": list(POLARITIES if not fast else ("rise",)),
        "latch": "compare-mode LE=0.4V, _LE=GND, VTT=GND (official example)",
        "hysteresis": "HYS open (datasheet zero hysteresis)",
        "termination": "VTP and VTN to GND; no extra VP shunt 50ohm",
        "cml_load": "50ohm to GND on Q and QB",
        "parameter_provenance": {
            "datasheet_tpd": "literature ADCMP580 Rev. B typical 180 ps",
            "sweeps": "engineering characterization grid",
            "amplitude": "engineering testbench, not challenge 1 PPS",
        },
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.spice.adcmp580",
        random_seed=DEFAULT_SEED,
        input_parameters=params,
        extra=extra,
        result_classification=SPICE_RESULT_CLASSIFICATION,
        disclaimer=SPICE_DISCLAIMER,
    )
    write_json(out / "summary.json", extra)
    (out / "interpretation.md").write_text(_interpretation(extra), encoding="utf-8")
    extra["output_dir"] = str(out)
    extra["ltspice_ran"] = True
    return {"output_dir": str(out), "extra": extra}


def _interpretation(extra: dict[str, Any]) -> str:
    disp = extra.get("dispersion_ps")
    mean = extra.get("mean_tpd_ps")
    delta = extra.get("tpd_sim_minus_datasheet_typ_ps")
    return f"""# ADCMP580 SPICE interpretation

**Classification:** SPICE/front-end simulation. Not laboratory measurement.

Mean tpd: {mean} ps. Datasheet typical: {DATASHEET_TPD_TYP_PS} ps.
Difference (sim − datasheet typ): {delta} ps. Do not retune the bench to force agreement.

Sweep dispersion max(tpd)-min(tpd): {disp} ps.
Datasheet detailed discussion: <{DATASHEET_DISP_DETAILED_LT_PS} ps over 5 mV–500 mV and 1–10 V/ns.
Overview text typical <{DATASHEET_DISP_OVERVIEW_TYP_LT_PS} ps. Keep both contexts.

Random jitter was not inferred. The 200 fs RMS figure remains manufacturer literature.

Macromodel limitations: no package/PCB/connector parasitics; CML-to-Kintex-7 not in this bench.
Challenge 1 PPS amplitude/edge remains unspecified.

{SPICE_DISCLAIMER}
"""
