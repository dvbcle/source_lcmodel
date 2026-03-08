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
