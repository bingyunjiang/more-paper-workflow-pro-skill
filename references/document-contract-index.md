# Document Contract Index

This index keeps entry docs and runtime contracts from drifting apart.

## Generated Inventory

Run:

```bash
python3 scripts/check_doc_contracts.py --json
```

The generated inventory reports current repository facts:

- top-level Python script count from `scripts/*.py`
- Step document count from `agents/step_*.md`
- publisher configuration count from `config/publishers.toml`
- Step 5 route phases from `agents/step_5_download.md`
- line budgets for large entry/runtime files

README should refer to this generated inventory instead of hard-coding
marketing numbers such as publisher counts, script counts, success rates, or
trigger phrase counts.

## Step File Skeleton

Each main Step file should keep the same high-level skeleton:

1. trigger / applicable tasks
2. input requirements
3. checkpoint boundary
4. execution flow
5. standard outputs
6. quality gate
7. closing checks
8. failure routing / troubleshooting

Large domain rules, templates, examples, and style packs should live in
`references/` and be linked from the relevant Step file.

## Size Policy

Current line budgets are intentionally conservative no-growth guards, not the
final target size. Tighten them only after moving a chunk of domain material
from a Step file into `references/`.
