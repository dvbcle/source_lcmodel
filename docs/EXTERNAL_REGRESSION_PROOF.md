# External Regression Proof (`test_lcm`)

This document records a successful external regression run using the public
fixture from `schorschinho/LCModel` (`test_lcm`).

## Run metadata

- Date: `2026-03-08`
- Fixture source: `https://github.com/schorschinho/LCModel`
- Fixture files used: `control.file`, `data.raw`, `3t.basis`, `out_ref_build.ps`

## Command executed

```powershell
python -m lcmodel --control-file control.file
```

## Process

1. Clone upstream fixture repository and copy `test_lcm` inputs into a local
   working directory.
2. Run LCModel Python CLI with the provided control file.
3. Compare generated `out.ps` against upstream reference `out_ref_build.ps`:
   - Binary compare via `fc /b`.
   - SHA256 checksums for both files.
4. Record all outputs (`stdout/stderr`, compare output, checksums).

## Verification

- Process exit code: `0`
- Binary compare (`fc /b out.ps out_ref_build.ps`) exit code: `0`
- `fc` output: `FC: no differences encountered`
- SHA256 (`out.ps`): `ED84E9B18FC0968528939C1355E90A6220D96DA770AD4032094FD9D13DD5E2E5`
- SHA256 (`out_ref_build.ps`): `ED84E9B18FC0968528939C1355E90A6220D96DA770AD4032094FD9D13DD5E2E5`
- Hash match: `True`

## Evidence captured during run

- `fc /b` output: `FC: no differences encountered`
- CLI run completed with `run_exit_code=0`
- Binary compare completed with `fc_exit_code=0`
