# Files to Delete Before Giving to Candidate

## Delete this entire directory: `to_delete_before_test/`

This directory contains:
- `answer_key.json` - Expected behaviors for each query
- `evaluate_responses.py` - Pre-built evaluation script  
- `CHALLENGE_NOTES.md` - Hints about what to fix
- `CURRENT_PERFORMANCE.md` - Current scores and issues
- Test outputs with evaluation scores
- `test_datasets_cleaned/` - Cleaned datasets with hints removed

## Also delete:
- `.env` file (candidate should create their own)
- `venv/` directory (candidate should create their own)
- `.git/` directory (if you want them to start fresh)

## Keep everything else!

The remaining files create a realistic codebase with subtle issues for the candidate to identify and fix.

## Quick cleanup command:
```bash
rm -rf to_delete_before_test/ .env venv/ .git/
```
