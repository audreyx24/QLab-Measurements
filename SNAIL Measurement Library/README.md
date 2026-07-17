# SNAIL Measurement Library

Everything from `QLab_tra_HH.ipynb` and `HH_qubit.ipynb` moved into an
importable package (`qlab/`) plus one thin driver notebook
(`run_measurements.ipynb`). One measurement = one function call.

```
qlab/
  config.py        addresses, data dirs, default params (edit here, not in code)
  instruments.py   connect() [real, lab PC] / connect_fake() [any laptop]
  measurements.py  all measurement routines
  fake_vna.py      FakeVNA + FakeSgen for offline testing
run_measurements.ipynb   thin driver notebook
smoke_test.py            offline end-to-end test:  python3 smoke_test.py
fake_data/               output of fake-mode runs (CSV + PNG)
```

## Old cell → new function

| Original | New call |
|---|---|
| QLab_tra cells 10 / 15 / 17, HH_qubit cell 11 | `resonator_scan(st, center, span, ...)` |
| QLab_tra cell 12 (punch-out) | `resonator_power_sweep(st, ...)` |
| QLab_tra cell 14 (2 h monitor) | `stability_monitor(st, ..., n_runs=None)` |
| HH_qubit cell 9 (Gen1 prebuilt) | `two_tone_pump(st, ...)` |
| HH_qubit cell 10 (Gen1 2D) | `two_tone_probe_sweep(st, ...)` |
| HH_qubit cell 13 (Gen2, 10 s/pt) | `pump_sweep_gen2(st, ...)` — kept as reference |
| HH_qubit cells 16–20, 30 (Gen3, 2 s/pt) | `pump_sweep_fast(st, ...)` |
| HH_qubit cell 28 (5a observe) | `pump_observe(st, ...)` |
| HH_qubit cell 32 (5c Kerr) | `kerr_shift_sweep(st, ...)` |
| HH_qubit cell 33 (power ramp) | `pump_power_ramp(st, ...)` |
| sgen off + rf off cleanup cells | `all_off(st)` |

## What is intentionally unchanged

On real hardware every function reproduces the notebook call sequence
verbatim — same PycQED/QLab_Neon calls, same VNA setup order, same
`MC.run()` dataset names (typos included, so new data sorts next to old
data). Refactor first, optimize second.

## Deliberate changes (all flagged in docstrings)

1. **`pump_observe` bug fix** — the original cell used an undefined `power`
   variable that silently reused whatever the notebook namespace had;
   it is now the explicit required argument `pump_power`.
2. **`pump_sweep_fast(settle_s=...)`** — optional wait after moving the pump
   before triggering the VNA (the missing settle flagged in the notebook as
   a plausible cause of SNR drift). Default `0.0` = original behavior.
3. **`stability_monitor(n_runs=...)`** — the infinite `while True` loop got
   an optional run limit. `None` = original behavior.
4. **Gen3 CSV path** — auto-named and auto-organized into the dated tree
   below (the hardcoded `C:/...`/`G:/...` paths are gone); override with
   `csv_path=`.

## Where data lands (folder organization)

Every measurement's output goes into a per-run folder, mirroring the layout
PycQED already uses for its own datasets:

```
<datadir>/
  20260717/                         <- one folder per day (YYYYMMDD)
    112656_resonator_scan_S21/      <- one folder per run (HHMMSS_name)
      resonator_scan_S21.csv
      resonator_scan_S21.png
    113010_pumpsweep_4.5000GHz_to_6.5000GHz_pump5dBm/
      pumpsweep_...csv
```

- **Fake mode:** `<datadir>` = `fake_data/` (in the library folder).
- **Real mode:** `<datadir>` = `config.DATADIR_LAB` (e.g. `C:/Data_HH/stub-s3`),
  set once in `connect(datadir=...)`. For a new sample, point that at a new
  base folder (e.g. `C:/Data_HH/sampleXYZ`) and the dated tree builds under it.

Because the date/time convention matches PycQED's, the direct-save paths
(fake scans and `pump_sweep_fast`, which bypass PycQED's saver) interleave
in the **same day folders** as the PycQED `MC.run()` datasets — a whole day
of data sits together regardless of which code path wrote it. The helper is
`config.make_run_dir(datadir, name)` if you need it elsewhere.

## Testing without hardware / without a sample

1. **Laptop:** `python3 smoke_test.py` — runs every offline-capable routine
   against a fake VNA with synthetic physics (Lorentzian resonator, cable
   delay, punch-out, dispersive two-tone response) and asserts the results.
2. **Lab PC, no sample:** cable port 1 → port 2 on the PNA and run the
   notebook cells in `real` mode — flat S21 near 0 dB means the plumbing
   works. Nothing here can harm a sample at these powers anyway.
3. **Equivalence check (when going direct-SCPI later):** run the same scan
   through this library and through the new path; traces must match.

## Requirements

- Fake mode: numpy, pandas, matplotlib (nothing else).
- Real mode (lab PC): PycQED (`pycqed_py3` with lab-local `KST_VNA`,
  `QLab_Neon`), QCoDeS + qcodes_contrib_drivers, pyvisa.
