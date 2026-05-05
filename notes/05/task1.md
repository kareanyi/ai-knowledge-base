millerlin@192 v2 % python hooks/validate_json.py knowledge/articles/test-good.json
[PASS] knowledge/articles/test-good.json

==================================================
Total: 1 files, 0 errors
millerlin@192 v2 % python hooks/validate_json.py knowledge/articles/test-bad.json

[FAIL] knowledge/articles/test-bad.json
- Missing required field: source_url
- Missing required field: summary
- Missing required field: tags
- ID 'bad' must match format {source}-{YYYYMMDD}-{NNN}
- status must be one of ['archived', 'draft', 'published', 'review'], got 'unknown_status'

==================================================
Total: 1 files, 5 errors
millerlin@192 v2 % python hooks/validate_json.py knowledge/articles/*.json

[FAIL] knowledge/articles/test-bad.json
- Missing required field: source_url
- Missing required field: summary
- Missing required field: tags
- ID 'bad' must match format {source}-{YYYYMMDD}-{NNN}
- status must be one of ['archived', 'draft', 'published', 'review'], got 'unknown_status'
  [PASS] knowledge/articles/test-good.json

==================================================
Total: 2 files, 5 errors