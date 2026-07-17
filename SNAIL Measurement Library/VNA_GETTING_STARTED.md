# Getting started with the Keysight N5222B PNA — a beginner's guide

You've never used a VNA before, so this is ordered as a **learning path**, not a
link dump. Do it roughly top to bottom. Your specific instrument is a
**Keysight PNA N5222B** (part of the PNA "N522x/N523x/N524xB" family — that
family name is what you search for when a page doesn't mention "N5222B" by name).

> **Heads-up on links:** Keysight's online *help* pages are versioned by
> firmware (`WebHelp9_42`, `csg/N52xxA`, …) and Keysight reshuffles them often,
> so a deep link may 404 in a few months. The **stable entry point that never
> moves** is <https://www.keysight.com/find/pna> — start there if any specific
> link below is dead, and use Keysight's doc search at
> <https://docs.keysight.com>. The *best* copy of the help is the one **built
> into the instrument** (see Step 1).

---

## Step 0 — What a VNA even is (30–60 min, concepts)

A VNA sends a tone into your device and measures what comes back, as a function
of frequency. "S21" = what gets *transmitted* through (port 1 → port 2). "S11" =
what gets *reflected* back at port 1. A resonator shows up as a dip (S21) or a
circle (S11) at its frequency. That's the whole game for your resonator scans.

- **Keysight, "Network Analysis Fundamentals" (Northwestern NUANCE handout, PDF)** —
  a clean, slide-style beginner intro to S-parameters and VNA basics, written for
  exactly your situation (a physics lab, new user):
  <https://nuance.northwestern.edu/documents/2024-04-22-keysight-network-analysis-fundamentals.pdf>
- **Video: "Introduction to PNA Help and Programming – Part 1"** (Keysight, YouTube) —
  short tour of the PNA and its built-in help/command finder:
  <https://www.youtube.com/watch?v=60vIj3wCe8o>

## Step 1 — The instrument's own help + Quick Start (do this at the lab PC)

The N5222B runs Windows and has the **entire help manual built in** — press
**Help** on screen, or on the desktop open the PNA Help. This is the copy that
matches *your* firmware exactly, including every SCPI command.

- **"New to the PNA/PNA-X? Start Here"** (Keysight knowledge center) — the
  official beginner on-ramp; a guided tour of the most important operations in
  priority order: <https://www.keysight.com/find/pna> → search *"New to the PNA
  Start Here"* (the direct docs.keysight.com link for this rotates).
- **PNA Series Installation & Quick Start Guide (PDF)** — front-panel/hardkey
  tour: Preset, **Meas** (pick S21/S11), Freq, Power, Sweep, Marker:
  <https://www.keysight.com/us/en/assets/9018-05093/quick-start-guides/9018-05093.pdf>

**Front-panel practice (no code), with port 1 cabled to port 2:**
1. Press **Preset** (green key) — known clean state.
2. **Meas** → select **S21**. You should see a flat trace near 0 dB (a cable
   passes everything through).
3. Set **Start/Stop** frequency and **Points**; watch the trace update.
4. Lower **IF Bandwidth** → trace gets less noisy but sweeps slower. Turn on
   **Averaging** → watch it settle. (These are the `if_bandwidth` and `averages`
   knobs in your notebook.)
5. Switch the display to **phase** and adjust **Electrical Delay** until the
   phase goes flat — *that* is the `delay_t = 6.5e-8` magic number in your code.

## Step 2 — Talk to it from Python with PyVISA (the "hello world")

Before any SCPI, get the instrument to *identify itself*. This is the whole
foundation of "communicating with the VNA directly."

- **PyVISA tutorial (official docs)** — install, `ResourceManager`, open a
  resource, `query('*IDN?')`, read/write terminations:
  <https://pyvisa.readthedocs.io/en/latest/introduction/communication.html>
- **PyVISA project home:** <https://pyvisa.readthedocs.io/>

Your first script on the lab PC (your VNA's address is already in
`qlab/config.py`):

```python
import pyvisa
rm = pyvisa.ResourceManager()
print(rm.list_resources())            # find/confirm the instrument
vna = rm.open_resource('USB0::0x2A8D::0x2A01::MY58421887::0::INSTR')
print(vna.query('*IDN?'))             # -> Keysight,N5222B,... : success!
```

If that prints the instrument's name, you can talk to it. Everything else is
just sending it the right text commands.

## Step 3 — SCPI: the command language (your main goal with Hao)

SCPI is the text protocol: you send strings like `SENS:FREQ:STAR 8e9` and read
back `CALC:DATA? SDATA`. The PNA help has a **Command Finder** and **example
programs** — this is the reference you'll live in when writing the direct driver.

- **SCPI Basics (Keysight help):** what SCPI is, syntax, how queries work:
  <https://helpfiles.keysight.com/csg/n5106a/scpi_basics.htm>
- **Triggering the PNA using SCPI (example):** how to trigger a sweep and wait
  for it to finish — the crux of getting clean single sweeps:
  <https://helpfiles.keysight.com/csg/pxivna/Programming/GPIB_Example_Programs/Triggering_the_PNA_using_SCPI.htm>
- **SCPI Example Programs index** (browse for a full measure→read example;
  find the current version via <https://www.keysight.com/find/pna> → *Help &
  Manuals* → *Programming* → *SCPI Example Programs*).
- **Programming Command Finder / SCPI Command Tree** — the searchable list of
  every command. Reach it from the instrument's built-in Help (most reliable),
  or online via the PNA help *Programming* section.

The ~15 commands you'll actually need (cross-reference each in the Command
Finder for exact syntax on your firmware):

| Purpose | SCPI (approx.) |
|---|---|
| Identify / reset | `*IDN?` , `SYST:FPR` / `*RST` |
| Define an S21 measurement | `CALC:PAR:DEF:EXT 'my_meas','S21'` |
| Start / stop frequency | `SENS:FREQ:STAR 8e9` , `SENS:FREQ:STOP 8.02e9` |
| Number of points | `SENS:SWE:POIN 2001` |
| IF bandwidth | `SENS:BWID 1000` |
| Source power | `SOUR:POW -30` |
| Averaging | `SENS:AVER:COUN 100` , `SENS:AVER ON` |
| Electrical delay | `CALC:CORR:EDEL:TIME 6.5e-8` |
| Trigger one sweep + wait | `INIT:IMM` then `*OPC?` |
| Read complex data | `CALC:DATA? SDATA` (real/imag pairs) |
| Fast binary transfer | `FORM:DATA REAL,64` |

## Step 4 — Your Rosetta Stone: the lab's own `KST_VNA.py` driver

You don't have to reverse-engineer SCPI from scratch. The lab's existing driver
already wraps every command you use. On the lab PC:

```python
from pycqed.instrument_drivers.physical_instruments import KST_VNA
print(KST_VNA.__file__)      # open this file
```

Every method your notebooks call (`bandwidth()`, `avg()`, `start_sweep_all()`,
`get_real_imaginary_data()`, …) is a thin wrapper around one or two SCPI
strings. **Read that file next to the Command Finder** and you'll have the exact
command list for a direct driver — it's the shortest path to Hao's goal.

---

## Quick reference — the durable links

| What | Link |
|---|---|
| PNA documentation portal (never moves) | <https://www.keysight.com/find/pna> |
| Keysight doc search | <https://docs.keysight.com> |
| N5222B product/support page | <https://www.keysight.com/us/en/support/N5222B/pna-microwave-network-analyzer-900-hz-10-mhz-26-5-ghz.html> |
| PNA Quick Start Guide (PDF) | <https://www.keysight.com/us/en/assets/9018-05093/quick-start-guides/9018-05093.pdf> |
| Network Analysis Fundamentals (beginner PDF) | <https://nuance.northwestern.edu/documents/2024-04-22-keysight-network-analysis-fundamentals.pdf> |
| PyVISA tutorial | <https://pyvisa.readthedocs.io/en/latest/introduction/communication.html> |
| SCPI Basics | <https://helpfiles.keysight.com/csg/n5106a/scpi_basics.htm> |
| Triggering the PNA using SCPI | <https://helpfiles.keysight.com/csg/pxivna/Programming/GPIB_Example_Programs/Triggering_the_PNA_using_SCPI.htm> |
| Intro to PNA Help & Programming (video) | <https://www.youtube.com/watch?v=60vIj3wCe8o> |

**Suggested order:** Step 0 reading tonight → Steps 1–2 next time you're at the
lab PC (front panel + `*IDN?`) → Steps 3–4 when you start the direct `pna.py`
driver. The `smoke_test.py` fake VNA lets you develop the *loop logic* on your
Mac in parallel, so at the lab you only debug the hardware I/O.
