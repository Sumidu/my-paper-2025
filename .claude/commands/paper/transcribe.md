Run the transcription pipeline:

```bash
bash _harness/setup.sh 2>/dev/null || true
_harness/.venv/bin/python _harness/scripts/transcribe.py
```

After the script finishes:
- Report which files were transcribed (or that no new recordings were found)
- If any translation files were created, mention them too
- If there were errors, explain them clearly
