# Front-end electrical baseline (POC candidate)

Status: **TRL 2**. Classification: **external component evidence** +
**datasheet arithmetic**. Not SPICE (except retained ADCMP580-family core
macromodel evidence elsewhere). Not laboratory measurement.

Fine TDC architecture is **not** selected from Vivado alone. This note freezes
the **POC electrical front-end candidate** for the measurement channels.

## Frozen FPGA structural context (local implementation evidence only)

| Branch | 16ch resources | 4 ns WNS | Route | Placement |
| --- | --- | --- | --- | --- |
| Multichain Round 7 | 8192 CARRY4, 32800 FF, 21547 LUT, 13669 slices (53.92%) | +3.045 ns | fully_routed | — |
| MSWU validated Round 9 | 800 CARRY4, 13112 FF, 1038 LUT, 2935 slices (11.58%) | +0.162 ns | fully_routed | 16/16 vertical, 0 scattered |

Validated 1ch sequential MSWU preencoder surrogate: 50 CARRY4, 1274 FF, 434 LUT,
396 slices (1.56%), WNS +0.221 ns.

**No architecture winner selected from Vivado alone.** Multichain: lower
pulse-launch/algorithmic risk, heavier resources. MSWU-inspired: lower structural
resource use + stronger literature metrology precedent; physical Wave Union
launcher / calibration / manual P&R risk remains.

## Primary comparator candidate: Analog Devices ADCMP582

Manufacturer facts (ADCMP580/581/582 family datasheet / product literature;
**external component evidence**):

| Item | Value |
| --- | --- |
| Status | PRODUCTION |
| Output | Reduced-swing PECL |
| Propagation delay | 180 ps typical |
| Propagation-delay TC | 0.25 ps/°C |
| Random jitter | 200 fs RMS under datasheet conditions |
| Deterministic jitter | 15 ps (VOD=500 mV, 5 V/ns, PRBS31, 5 Gbps); 25 ps (VOD=200 mV, 5 V/ns, PRBS31, 10 Gbps) |
| Output differential | 340 / 395 / 450 mV min/typ/max |
| VCCO | 2.5 V to 5.0 V |
| On-chip input termination | 47–53 Ω |
| Input supplies | ±5 V |
| Input range | −2 V to +3 V |

**Do not** treat high-speed DJ figures as 1 PPS guarantees.

ADCMP580 SPICE macromodel results already in this repository remain valid as
**family-core** SPICE evidence; they do not close the PECL→FPGA I/O path.

## Preferred translator: TI DS15BR401 (not DS15BR400)

| Reason | Detail |
| --- | --- |
| PECL termination | ADCMP582 PECL wants 50 Ω from each output to **VCCO − 2 V** |
| DS15BR401 | Lacks internal input termination → external PECL termination is not paralleled with DS15BR400’s 100 Ω input |
| Family I/O | Accepts LVPECL / CML / LVDS; outputs LVDS |
| Input differential | About 100 mV to 2.4 V |
| Input common-mode | About 0.05 V to 3.55 V |
| Family RJ | Typ 0.5 ps RMS, max 1.5 ps under datasheet 750 MHz test |
| High-speed DJ/TJ | Pattern-specific; not 1 PPS guarantees |

## POC baseline channel

```text
SMA female 50 Ω
  → protection / controlled impedance
  → ADCMP582
  → PECL termination (50 Ω to VCCO−2 V)
  → DS15BR401
  → Kintex-7 LVDS
  → TDC capture
```

**Initial translator-interface candidate:** ADCMP582 **VCCO = 3.3 V**.
Typical PECL CM ≈ 2.16 V and differential ≈ 395 mV sit inside the DS15BR401
characterized input domain (datasheet arithmetic:
`python -m tidl_poc sim frontend-electrical`).

## Optional optimization (not baseline)

ADCMP582 **VCCO = 2.5 V** direct to Kintex-7 **LVDS_25**.

Nominal typ arithmetic:

| Quantity | Value |
| --- | --- |
| VOH | ~1.56 V |
| VOL | ~1.17 V |
| VCM | ~1.365 V |
| VDIFF | ~0.395 V |

Kintex-7 LVDS_25 windows used here: VIDIFF 0.100–0.600 V; VICM 0.300–1.500 V.
Typ is nominally compatible; **worst-corner margin is not closed**, so this path
is **not** the POC baseline.

## Datasheet arithmetic outputs

```text
python -m tidl_poc sim frontend-electrical
```

Writes `outputs/frontend_electrical/` (CSV/JSON). Label: datasheet arithmetic,
not SPICE/lab.

## Open risks (explicit)

- 1 PPS slew/amplitude not specified by the challenge → walk/dispersion remain
  calibration-sensitive.
- Translator adds delay, skew, and RJ; must appear as separate error-budget terms.
- Direct 2.5 V PECL→LVDS_25 is an optimization study only.
- No board has been built; no physical validation exists at TRL 2.
