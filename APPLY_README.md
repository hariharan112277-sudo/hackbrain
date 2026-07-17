# Apply Phase 2 fixes

1. Extract this ZIP into the existing repository root and allow files to be overwritten.
2. Delete every path listed in `DELETE_FILES.txt`.
3. Install project dependencies if needed.
4. Run:

```bash
pytest -q tests/test_assets.py --no-cov
```

Expected targeted verification: `12 passed`.
