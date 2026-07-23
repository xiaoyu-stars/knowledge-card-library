---
name: knowledge-card-library
description: Delegate supplied knowledge to one sub-agent that converts it into structured active-recall cards and persists readable Markdown plus structured source data in a knowledge library. Use when the user asks to generate 知识卡片, build or add to a 知识库, organize genes/proteins/terms/words/concepts/mechanisms for learning, or explicitly invokes $knowledge-card-library. Also use to retrieve, revise, or extend cards previously stored by this skill; every generation, revision, or persistence operation must be performed by a sub-agent rather than the main agent.
---

# Knowledge Card Library

Keep the main agent's context focused on the user's knowledge and final deliverable. Delegate the mechanical creation and storage workflow.

## Mandatory delegation rule

For every request that **creates, revises, imports, or persists** knowledge cards:

1. Spawn exactly one sub-agent and assign it ownership of the complete operation.
2. Do not classify the content, draft cards, prepare payloads, edit library files, or run persistence commands in the main agent.
3. Pass the sub-agent only:
   - the user's original content without summarizing it;
   - the user's explicit card or formatting constraints;
   - the selected library root;
   - the absolute path of this Skill directory.
4. Instruct the sub-agent to read this `SKILL.md`, then read and follow [references/worker-workflow.md](references/worker-workflow.md) and [references/storage-schema.md](references/storage-schema.md). These operational references are for the executing sub-agent; the main agent does not need to load them.
5. Wait for the sub-agent's compact handoff containing the saved Markdown path, topic ID, card count and types, verification status, and persistence checks.
6. In the main agent, perform at most lightweight existence/status checks if needed. Do not reload drafts, payloads, command logs, or the full backend store unless the sub-agent reports a failure or the user explicitly asks for an audit.
7. Return the final Markdown link and the compact result to the user.

If sub-agent delegation is unavailable, stop and state that this Skill requires a sub-agent. Do not silently perform card creation or persistence in the main agent.

## Resolve the library root

- Use a path explicitly supplied by the user.
- Otherwise use the `KNOWLEDGE_BASE_ROOT` environment variable when set.
- If neither is provided, use `~/KnowledgeBase`.
- Do not create another library merely because the current working directory changed.

## Read-only operations

Simple listing, retrieval, or opening of existing cards may remain in the main agent because they do not create or persist content. Delegate whenever an operation changes Markdown cards, the index, structured data, status, tags, or versions.

## Sub-agent handoff contract

Require the sub-agent's final message to contain only:

- outcome and topic title;
- absolute Markdown card path;
- topic ID, total card count, and card-kind summary;
- whether content was externally verified;
- confirmation that the Markdown file, `data/store.json`, and `index.md` were validated;
- concise warning or blocker, if any.

Do not ask the sub-agent to paste generated Markdown or backend JSON into its handoff; those remain in the knowledge library.

