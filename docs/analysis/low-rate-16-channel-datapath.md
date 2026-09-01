# Low-rate 16-channel data path (design hypothesis)

Status: TRL 2. This is a challenge-specific architecture note, not a sized
memory design and not implementation evidence.

Kwiatkowski et al. 2023 (DOI 10.1016/j.measurement.2023.112510) report
resource-saving and throughput-optimized pre-encoders at 140 MSa/s and
385 MSa/s for one 200-bit register. Those encoder rates are **literature
evidence** for a general high-rate instrument.

S5 and S7 of this challenge specify 16 measurement channels at 1 PPS, i.e.
**16 measurement events per second**. That is many orders of magnitude below
140 MSa/s. The paper's per-channel deep FIFOs and high-rate host path are not
required by the specified event rate.

Do not calculate a fake final BRAM usage from this note. Replacing paper FIFOs
with a smaller centralized buffer is a **design hypothesis** that needs Vivado
evidence.

## Proposed structure (hypothesis)

- per-channel timestamp capture (fine + coarse combiner)
- minimal elastic buffering per channel (not a deep per-channel FIFO sized for
  hundreds of MS/s)
- shared centralized event queue
- internal nonvolatile backup logger (S13)
- UDP export (S10)
- sequence numbers, calibration-state version, and UTC quality bits on every
  record

There is no need for hundreds-of-MS/s sustained host transfer in the specified
1 PPS use case.

## Explicitly not decided here

- No memory part is selected.
- No buffer depth or retention time is claimed until the record format and
  outage-retention requirement are fixed.

Related calculator: `python -m tidl_poc sim mswu-literature`.
Classification of that CLI: model-based simulation plus literature
transcription, not FPGA utilization.
