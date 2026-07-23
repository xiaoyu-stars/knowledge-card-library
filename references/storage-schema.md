# Storage schema

Prepare one UTF-8 JSON object per topic for `knowledge_store.py upsert`.

## Required fields

```json
{
  "id": "gene-prdm15",
  "title": "PRDM15",
  "content_type": "gene_transcription_regulator",
  "status": "new",
  "tags": ["PRDM15", "transcription_regulation"],
  "source": {
    "kind": "user_provided_text",
    "externally_verified": false,
    "text": "Complete original text"
  },
  "items": [
    {
      "id": "prdm15-01",
      "kind": "identity",
      "front": "Question",
      "back": "Answer"
    }
  ]
}
```

Required top-level fields are `id`, `title`, `content_type`, `source`, and non-empty `items`. Each item requires `id`, `kind`, `front`, and `back`.

## Optional fields

- `status`: default `new`; use `learning`, `mastered`, or `needs_revision` when appropriate.
- `tags`: array of search terms.
- `markdown_filename`: stable filename such as `PRDM15.md`. If omitted, the helper derives one from `title`.
- `source.urls`: sources used for external verification.
- Additional topic or item fields may be preserved when useful.

The helper owns `created_at`, `updated_at`, `version`, and `markdown_file`. Do not depend on caller-supplied values for these fields.

## Identity and updates

- Use a lowercase, durable semantic topic ID such as `gene-prdm15` or `concept-operant-conditioning`.
- Reuse the ID to revise an existing topic.
- Keep item IDs stable when the tested fact remains the same.
- Preserve the full original input in `source.text`; do not replace it with a summary.
- Set `externally_verified` to `true` only after checking cited sources.

