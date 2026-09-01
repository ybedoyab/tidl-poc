# CML to Kintex-7 interface options (pre-study)

Status: TRL 2. Research note only. **No path is selected.** No hardware and no
interface SPICE exist. If an external conversion stage is required, it must
become a **separate error-budget term**; it is not hidden inside the 5 ps
front-end allocation.

## What the datasheets actually state

### ADCMP580 CML (Analog Devices Rev. B / product page)

- CML output intended to drive about 400 mV into 50 ohm transmission lines
  **terminated to ground**
- This is not an FPGA SelectIO standard

### Kintex-7 SelectIO (AMD/Xilinx DS182; UG471 / AR 43989)

DS182 LVDS (HP banks) and LVDS_25 (HR banks):

- Differential input VIDIFF typical window on the order of 100–600 mV
  (350 mV typical in the LVDS table with VICM = 1.25 V)
- Input common-mode VICM about **0.300 V to 1.425 V** (LVDS table at
  VIDIFF = ±350 mV). The LVDS_25 table lists VICM max 1.500 V in later DS182
  revisions.
- Absolute VIN windows are separate (HR about −0.40 V to VCCO+0.55 V;
  HP about −0.55 V to VCCO+0.55 V). Being inside VIN does not prove LVDS VICM
  compatibility.
- AR 43989: LVDS *inputs* may sit in a bank whose VCCO is not the LVDS output
  voltage, but DIFF_TERM must then be FALSE and the driver must still meet
  VIDIFF and VICM.

These numbers are **manufacturer literature**, not a board measurement.

## Conceptual options (none chosen)

1. **Direct differential FPGA input**
   Only if a named Kintex-7 I/O standard is shown to accept the ADCMP580 CML
   swing **and** common mode. CML terminated to ground typically sits near 0 V
   common mode, which is **below** the 0.300 V VICM minimum in the DS182 LVDS
   tables above. Direct LVDS is therefore **not shown to be compatible** from
   these documents. Do not assume it works.

2. **External level conversion / CML or PECL-to-LVDS receiver**
   A documented bridging part could move common mode into the FPGA window.
   That part adds delay, dispersion, and jitter and would need its own budget
   line. No device is selected here.

3. **AC coupling plus bias into an LVDS VICM window**
   Sometimes used for high-rate data. The challenge input is 1 PPS (second-scale
   pulses), so AC coupling is generally the wrong tool: the waveform droops and
   the threshold walks. Do not treat AC coupling as the default 1 PPS path.

## What must be verified before a choice

- Measured or simulated ADCMP580 Q/QB voltages into the intended termination
- The exact Kintex-7 bank type (HR vs HP) and VCCO
- VIN, VICM, VIDIFF for the I/O standard actually used
- Whether internal DIFF_TERM is legal at that VCCO
- Added timing uncertainty of any translator

Until that evidence exists, CML-to-FPGA remains an open interface risk, not a
solved block.
