# Preserving Chat History

This project does not automatically write the full assistant dialogue into the repository.

## Recommended workflow

1. At the start of a coding session, capture terminal I/O:

```powershell
Start-Transcript -Path .\docs\chat_transcript_$(Get-Date -Format yyyyMMdd_HHmmss).txt
```

2. At the end of the session, stop capture:

```powershell
Stop-Transcript
```

3. Save the IDE chat panel content:
- Use your IDE's `Copy` or `Export` action from the chat UI.
- Paste/export into `docs/` (for example, `docs/chat_export_YYYYMMDD.md`).

4. Keep checkpoints auditable with git:

```powershell
git log --oneline --decorate -n 30 > .\docs\checkpoint_log_latest.txt
```

## Notes

- `Start-Transcript` only captures terminal text after it is started.
- For earlier chat messages, use the IDE chat panel's export/copy.
- If desired, commit the transcript and checkpoint log after each major stage.

## Session Snapshot (2026-03-08)

This section summarizes the latest working session checkpoints so the
history is easy to review from the repository.

- `1a0edef` Modularize CLI mapping/output logic into reusable helper module.
- `501e895` Introduce typed RuntimeState and wire legacy scaffold defaults.
- `07337aa` Extract PostScript semantic overrides into domain module.
- `ece699d` Add conversion statistics snapshot for Fortran-to-Python port.
- `561d9f7` Document reproducible chat/session preservation workflow.
- `4d1d984` Refactor placeholder override registration into legacy bridge module.

For full details, run:

```powershell
git log --oneline --decorate -n 30
```
