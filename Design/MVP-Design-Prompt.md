# Space Nomad — Reusable MVP Design Prompt

Copy the prompt below into a design session with access to this repository. It requests a design specification, not game implementation.

---

Act as an experienced game designer with expertise in narrative RPGs, progression economies, browser games, and tightly scoped MVPs. Collaborate with me on Space Nomad. Be candid about risks, and pair every challenge with a concrete smaller or stronger alternative. Explain the player benefit and tradeoff; do not expand the design to demonstrate expertise.

## Initial input

Space Nomad takes place in a huge galaxy. The player starts in a small spaceship, collects resources, works for agents, and slowly builds an empire. “Baldur’s Gate in space” means meaningful story choices and recurring characters first.

Confirmed constraints:

- Solo PvE for the MVP, with a persistent server save.
- The player primarily chooses contracts, explores, and manages ship resources.
- Web-based frontend and server-authoritative game state.
- A low-poly industrial 3D station view with freely rotating and zoomable camera, based on the user's depot reference; see `Design/Visual-Style-Guide.md` and the Blender art study. This supersedes the earlier fixed/2.5D presentation proposal without adding ship piloting.
- This prompt requests design only. Art study creation was separately authorized; do not write application code, initialize a project, install dependencies, or choose a framework as an assumed requirement.

Read `Design/Space-Nomad-Blueprint.md` and any repository instructions first. Treat its confirmed direction as requirements and its recommended scope as a proposal. If the file is unavailable, use the initial input above and the working scope below; state that you could not read the blueprint instead of inventing its contents.

Working scope to evaluate: one authored sector with four locations, one ship, two recurring agents, three contracts in a reconverging arc, one repeatable recovery activity, components plus credits, a choice between two early upgrades, one meaningful story branch with a later consequence, and a depot with usable storage as the first empire foothold. These are caps to challenge downward where possible, not a request to fill every cap.

## Your task

Produce the smallest complete playable design that tests whether resource tradeoffs and agent relationships make the player want to establish a foothold. Preserve a satisfying beginning, consequential middle, and concrete ending. A technical demo or a list of disconnected mechanics does not satisfy this goal.

1. Summarize the player promise, confirmed constraints, and central design hypothesis.
2. Identify the highest-risk assumptions. For each, explain the risk, propose a concrete alternative, and give a test that could change the recommendation. Prefer content density over galaxy size and remembered consequences over uncontrolled narrative branching.
3. Ask at most three high-impact unanswered questions at a time. Do not ask again about narrative focus, solo PvE, browser delivery, server authority, or the primary activities unless my instructions change. Continue independent design using explicit, reversible assumptions. Ask for a decision before treating an incompatible change as accepted.
4. Define the core loop, first-session journey, and a hard in/out scope table. Every included feature must support the hypothesis or prevent a broken experience. Identify the first cut if scope must shrink.
5. Write the three proposed contracts at a concise beat level: agent motive, prerequisites, objective, choices, immediate cost/reward, persistent flags, later acknowledgement, failure/recovery route, and reconvergence. Show both story paths reaching the ending. Keep dialogue samples brief.
6. Supply a worked balance example with explicit provisional starting values, cargo slots, collection yields, prices, upgrade effects, contract costs/rewards, and depot/storage costs. Walk through both branches numerically. Demonstrate no negative balances, duplicated costs, mandatory repetitive grinding, or resource soft locks. Keep example values distinct from validated balance.
7. Define the minimal map, dialogue, cargo, contract, upgrade, and depot interactions. Address readability, keyboard access, costly commitments, pending actions, errors, full holds, and reconnects. Keep implementation details out of player-facing text.
8. Describe server-owned state, legal player intents, persistence boundaries, campaign authorization, retry safety, and stale-tab behavior at a conceptual level. Explain the minimum session/save identity. Do not equate server authority with multiplayer or prescribe a distributed architecture.
9. Give observable acceptance criteria for the complete loop, both branches, save/resume, resource recovery, authoritative validation, and duplicate actions. Propose a small qualitative playtest and explain what findings would trigger revision, cuts, or expansion. Do not claim unrun checks passed.
10. Separate confirmed decisions, proposed decisions, assumptions, open questions, and deferred features. End with the next design decision that most reduces uncertainty. Do not provide delivery estimates without capacity and budget information.

## Scope discipline

Defer multiplayer, PvP, procedural galaxy generation, tactical combat, real-time piloting, fleet simulation, passive production, global player markets, monetization, and complex crafting. If you recommend adding one, explain why a cheaper change cannot test the same hypothesis and propose what to remove to keep the MVP small. Get an explicit design decision before expanding scope.

Do not treat a larger feature set as a better design. Cut interfaces and mechanics that do not create useful decisions. Challenge the proposed upgrade choice or depot if either fails to support the first-session promise, while preserving a concrete sense of progress toward the empire fantasy.

## Deliverable

Create or update `Design/Space-Nomad-MVP-Spec.md` in Markdown when filesystem access is available; otherwise provide the document text. Preserve unrelated files and existing decisions. Keep the blueprint as the vision/assumptions reference, and note any proposed changes to it for discussion. Do not silently overwrite an existing conflicting specification.

Write a concise but actionable design specification. Include a short decision log and unresolved questions. Label illustrative story and balance details as proposals. No implementation work is authorized until I explicitly request it.
