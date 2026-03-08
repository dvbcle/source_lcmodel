# Performance Measurements

Last updated: 2026-03-08 11:54 (America/New_York)

This document captures measured runtime changes after:

- FFT backend configurability (`auto`, `numpy`, `pure_python`)
- Batch time-domain basis spectral caching

## Environment and workload

- Host: Windows (local development machine)
- Python: 3.13
- NumPy: 2.4.2 (installed for this measurement pass)
- Workload fixture: `test_lcm` from `https://github.com/schorschinho/LCModel`
- Control run command template:
  - `python -m lcmodel --control-file control.file --fft-backend <backend>`

## 1) FFT backend performance (single-run)

Method:

1. Warm up once per backend.
2. Run 5 timed runs per backend on the same fixture.
3. Validate `out.ps` against `out_ref_build.ps` after each backend set.

Measured results:

| Backend | Avg (s) | Min (s) | Max (s) | Regression check |
|---|---:|---:|---:|---|
| `pure_python` | 11.8151 | 9.3514 | 13.6535 | `FC_EXIT=0` |
| `numpy` | 0.4336 | 0.3977 | 0.4711 | `FC_EXIT=0` |
| `auto` (NumPy installed) | 0.4213 | 0.4055 | 0.4481 | `FC_EXIT=0` |

Derived speedup:

- `pure_python` -> `numpy`: **27.25x faster** (11.8151 / 0.4336)
- `pure_python` -> `auto` (with NumPy available): **28.05x faster** (11.8151 / 0.4213)

## 2) NumPy regression confirmation

Explicit standalone check:

- Command:
  - `python -m lcmodel --control-file control.file --fft-backend numpy`
  - `fc /b out.ps out_ref_build.ps`
- Result:
  - `FC: no differences encountered`
  - `FC_EXIT=0`
  - `OUT_PS_SHA256=ED84E9B18FC0968528939C1355E90A6220D96DA770AD4032094FD9D13DD5E2E5`
  - `REF_PS_SHA256=ED84E9B18FC0968528939C1355E90A6220D96DA770AD4032094FD9D13DD5E2E5`

## 3) Batch cache impact (time-domain batch)

Method:

1. Created 4 raw files (duplicates of fixture `data.raw`) with one shared basis file.
2. Timed:
   - `run_batch()` (includes basis spectral cache)
   - manual no-cache loop (`run()` per raw file without shared cache)
3. 5 timed runs each.

Measured results:

| Mode | Avg (s) | Notes |
|---|---:|---|
| Batch with cache | 0.6925 | Current `run_batch()` behavior |
| Manual no-cache loop | 1.5048 | Recomputes basis spectral conversion per raw |

Derived speedup:

- Batch cache vs no-cache baseline: **2.17x faster**

## Notes

- Timing variation is expected on a development workstation.
- The FFT improvement dominates single-run gains; batch caching adds additional
  throughput gain for multi-file time-domain batches sharing the same basis.
