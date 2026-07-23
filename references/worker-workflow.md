# Knowledge-card worker workflow

Use this workflow only as the sub-agent that owns card generation, revision, import, or persistence.

## Resolve and initialize the library

Use the library root supplied by the parent agent. If it does not exist, run:

```powershell
py "<skill-directory>\scripts\knowledge_store.py" init --root "<library-root>"
```

Use this layout:

```text
<library-root>/
├── index.md
├── cards/
│   └── <topic>.md
└── data/
    └── store.json
```

## Classify and design cards

Select the structure automatically:

- Gene/protein: full name, location, molecular type, action, pathway-context-outcome mappings, development or disease roles.
- Term/concept: concise definition, essential attributes, boundaries, mechanism, example/counterexample, confusing neighbors.
- Word: meaning, pronunciation only when known or supplied, usage, collocations, roots, contrast, mnemonic.
- Process/mechanism: trigger, ordered steps, outcome, regulation, failure modes.
- Comparison: shared basis, exact differences, discriminating cues, scenario questions.
- Mixed or long material: split into atomic cards across the relevant structures.

Apply these rules:

- Ask one core retrieval question per atomic card.
- Put the shortest sufficient answer first; add details underneath.
- Preserve the user's certainty level. Do not strengthen tentative claims into absolute ones.
- Do not invent facts absent from the source. Mark user-provided material as externally unverified unless sources were checked.
- Add a memory hook only when it faithfully reflects the source.
- Include a one-page overview, atomic cards, compact self-test, tags, and status.
- Avoid cards that test the same fact in slightly different words.

## Persist the result

1. Read `references/storage-schema.md` in full.
2. Create the human-facing Markdown draft in a temporary workspace location with a stable filename.
3. Create a UTF-8 JSON payload containing the complete original source and every front/back pair.
4. Run:

   ```powershell
   py "<skill-directory>\scripts\knowledge_store.py" upsert `
     --root "<library-root>" `
     --payload "<payload.json>" `
     --markdown "<draft.md>"
   ```

5. Parse `data/store.json` and verify the topic ID, card count, Markdown path, and index link.
6. Remove temporary drafts and payloads when safe; never delete library history or unrelated files.

For an existing topic, inspect the current record and reuse its stable topic ID. Preserve stable item IDs for unchanged facts. Create a new topic instead of overwriting unrelated knowledge.

## Return a compact handoff

Return only:

- outcome and title;
- absolute Markdown path;
- topic ID;
- number and kinds of cards;
- external-verification status;
- Markdown/store/index validation status;
- any warning or blocker.

Do not paste the card body, payload, backend JSON, or command transcript into the handoff.

