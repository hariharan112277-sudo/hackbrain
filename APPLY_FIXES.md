# Hackbrain Stale Test Cleanup — Only Fixes

This archive contains ONLY the cleanup for the stale test file.

## What was done
- Removed `tests/test_industrial.py` (stale, tests removed routes and old login schema)
- Removed `DELETED_FILES.txt` and `README_FIXES.txt` (scratch notes, no longer needed)

## How to apply (if not already applied)
```bash
cd /path/to/hackbrain
git am < hackbrain_cleanup.patch
# or manually:
git rm tests/test_industrial.py DELETED_FILES.txt README_FIXES.txt
git commit -m "Remove stale test_industrial.py (superseded by test_assets.py)"
```

## Final verification (run at repo root)
```bash
pytest tests/ -q --ignore=tests/test_stage2_realtime.py
```

## Expected result
```
====================== 226 passed, 21 warnings in 17.xx s =======================
```
0 failures, 0 errors.
