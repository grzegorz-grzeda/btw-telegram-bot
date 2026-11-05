# Issue tracker: Local Markdown

Issues and specs for this repo live as markdown files under `docs/`, committed with the code.

## Conventions

- Each feature's spec is `docs/specs/<feature-slug>.md`
- Implementation issues are one file per ticket at `docs/issues/<NN>-<slug>.md`, never a single combined tickets file. All features share one running number: a new ticket takes the next number after the highest in `docs/issues/` (counting `done-` files)
- Each ticket links its spec, for example `[Spec](../specs/<feature-slug>.md) user stories 3–5`
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a ticket is finished

Set `Status: resolved`, tick its checklist, and append the commit SHA under `## Comments`. Do this in the same commit as the work.

Then rename the file with a `done-` prefix (`git mv 03-foo.md done-03-foo.md`), so finished tickets stand out in a directory listing. Keep the number: tickets are still referred to by it (`03`, `Blocked by: 03`), so look a ticket up by `*NN-*.md` and expect either name.

Then review the other open tickets in `docs/issues/` for a `**Blocked by:**` line that names the finished ticket, and update each one in the same commit:

- Append `— done` to that blocker's entry, e.g. `**Blocked by:** 02 (Item types…) — done`. A ticket whose blockers are all marked done is unblocked.
- If the finished work changed something the blocked ticket relies on (a store operation, a convention, a decision recorded in the ticket's `## Comments`), add a short note under the blocked ticket's `## Comments` saying what and where.

## Before starting a ticket

Check its `**Blocked by:**` line. Every listed ticket must be a `done-` file with `Status: resolved`. If one isn't, stop and tell the user which blocker is still open, rather than starting the work.

## When a skill says "publish to the issue tracker"

Create a spec at `docs/specs/<feature-slug>.md`, and tickets as `docs/issues/<NN>-<slug>.md` with the next free numbers.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly. Then read only the sections of the linked spec that the ticket names, by heading.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket.

- **Map**: `docs/issues/<effort>/map.md` (the Notes / Decisions-so-far / Fog body).
- **Child ticket**: `docs/issues/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:` line records `claimed`/`resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `docs/issues/<effort>/issues/` for files that are open, unblocked, and unclaimed; first by number wins. Files starting with `done-` are resolved.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, rename the file with a `done-` prefix, then append a context pointer (gist + link) to the map's Decisions-so-far in `map.md`.
