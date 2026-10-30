# Coding Agent Workflow

## Starting a session

1. Open the repository root.
2. Read `README.md` in the repository and `prompts/00_MASTER_PROMPT.md` (adjust path if this pack is stored elsewhere).
3. Read `STATUS.md` and the relevant phase prompt.
4. Inspect the current code and git status before editing.
5. Identify whether uncommitted user changes exist; do not overwrite them.
6. State the intended scope and acceptance criteria briefly.
7. Implement in small, reviewable steps.

## During implementation

- Preserve current conventions unless there is a concrete reason to change.
- Never reveal secrets in terminal output, diffs, logs or reports.
- Do not use broad destructive commands.
- Do not add fake production content to make screens look complete.
- Do not bypass failed integrations with hardcoded responses.
- Run the smallest relevant test after each change, then broader checks.
- Keep migrations reversible where practical.
- Keep test fixtures isolated and never seed production.
- If a provider or official site is unavailable, report the real error and continue with non-blocked work.
- Ask for user input only when a real credential, permission, product decision or destructive action is blocking progress.

## End of each phase

Report:
- Files changed.
- Commands and tests run and their actual outcomes.
- Data sources retrieved and verification status.
- Integrations configured and actually tested.
- Remaining risks/blockers.
- Cost implications.
- Exact next step.

Update `STATUS.md` and relevant registers. Do not change a status to complete without evidence.

## Git hygiene

- Check `git status` before and after work.
- Never commit `.env`, credentials, private documents or user data.
- Use focused commits if requested by the owner.
- Do not push, deploy, delete production data or enable billing without explicit authorization.
