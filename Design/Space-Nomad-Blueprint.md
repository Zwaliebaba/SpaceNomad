# Space Nomad — Design Blueprint

Status: collaborative design draft v0.2. Game implementation remains outside this document's scope; a visual style guide and Blender art study have since been requested.

## 1. Intent and confirmed direction

Space Nomad is a browser-based space RPG about growing from the owner of a small ship into an influential power in a huge galaxy. Players collect resources, accept work from agents, develop relationships, and gradually establish an empire.

The player has confirmed:

- “Baldur’s Gate in space” primarily means meaningful story choices and recurring characters.
- The first MVP is solo PvE with a persistent server save.
- Most play time should involve choosing contracts, exploring, and managing ship resources.
- The server is authoritative; the frontend runs in a web browser.
- Current work is design and a Blender art study, with no game implementation.
- Station locations use actual 3D geometry with freely rotating, zoomable cameras, following the supplied depot image's visual direction.

Everything below that narrows these requirements is a recommendation, not an approved product commitment. The repository currently has no game code or Cargo manifest. Its Rust-oriented ignore file and installed tooling do not settle the implementation stack.

## 2. Player promise

> Start with a ship that barely holds together. Decide whom to help, what to bring home, and what kind of power to become.

The signature decision combines three pressures: an immediate material need, a relationship, and a future opportunity. For example: sell recovered components to improve the ship now, or deliver them to an agent who can help secure your first depot.

The initial emotional arc is vulnerability → competence → belonging → ownership. Wealth supports that arc; watching a number increase is insufficient on its own.

### Design pillars

| Pillar | Player-facing evidence | Scope guardrail |
| --- | --- | --- |
| Choices leave traces | An agent remembers a decision and changes a later offer or price | Reuse authored situations with a small number of persistent flags |
| A small ship creates useful constraints | Cargo capacity forces a choice about what to recover or carry | One ship, a few clearly explained resources |
| Discovery changes a plan | A location reveals a lead, resource opportunity, or competing claim | A compact authored sector before procedural generation |
| Power grows through relationships and assets | Work opens access to a first owned foothold | Prove one asset before simulating an empire |

## 3. Challenge the concept constructively

These are design heuristics and hypotheses to test, not claims that one formula works for every game.

| Concept risk | Why it matters | Better first approach |
| --- | --- | --- |
| A huge galaxy is the first deliverable | Empty travel and repetitive content dilute meaningful decisions | Build one dense sector; make undiscovered space visible as future possibility |
| “Like Baldur’s Gate” implies every feature | Cinematics, companions, combat, and branching narrative compete for the same content budget | Borrow consequential dialogue and recurring characters first |
| Collection becomes repeated clicking | Busywork delays the interesting contract and relationship decisions | Resolve salvage through a small set of collection and resource-allocation choices |
| Agents become interchangeable job boards | Rewards alone fail to establish recurring characters | Give two agents conflicting needs, recognizable voices, and remembered outcomes |
| Empire growth is a separate management game immediately | Production chains and fleet automation obscure the opening RPG loop | End the first arc with a depot that provides one practical benefit |
| Server authority is treated as an MMO requirement | Shared economies and concurrency multiply design and operations costs | Persist isolated solo campaigns on an authoritative server |
| Every choice creates a new storyline | Branches expand faster than the team can author and validate them | Branch briefly, reconverge, and carry consequences through flags and later variants |
| Routine fuel or repair costs create a soft lock | A new player can become unable to reach the next decision | Use free local travel initially and guarantee a recovery action |

No real-time piloting, tactical combat, or multiplayer is necessary to test the selected promise. If playtests show an absence of tension, first improve competing objectives, visible opportunity costs, and agent consequences. Add combat only if it solves a demonstrated problem.

## 4. Long-term vision versus first proof

The eventual galaxy can contain distinct regions, competing powers, specialized ships, recurring crews, and owned infrastructure. An empire could grow through trade access, alliances, information, and industry as well as military force. The exact form remains open.

The first proof is narrower:

> Can a short sequence of contracts make players care about a resource decision, remember an agent, and want to establish their own foothold?

A small sector does not validate galaxy scale, a player economy, or empire simulation. It validates whether the foundation deserves expansion.

## 5. Recommended MVP boundary

### Intended experience

Provisional target: a complete first playthrough in 20–30 minutes on a desktop or laptop browser, with no enforced waiting. The player can leave and resume from the last committed action. Session length is a playtest target, not a scheduling or delivery estimate.

Presentation: a readable sector navigation map and a 3D station-location view with freely rotating, zoomable camera, ship/cargo panel, and dialogue/contract view. The station art follows the user's supplied low-poly industrial depot reference. See [Visual-Style-Guide.md](Visual-Style-Guide.md). This replaces the earlier static/2.5D recommendation. Limit the first 3D study to one depot; voice acting and elaborate animation remain deferred. Camera exploration does not imply direct ship piloting or character locomotion.

### Content budget

| Element | Hard initial cap | Purpose |
| --- | --- | --- |
| Sector | 1, containing 4 locations | Hub, salvage field, remote contact, abandoned depot |
| Player ship | 1 | Stable identity and understandable constraints |
| Recurring agents | 2 | Opposing priorities without a faction simulation |
| Authored contracts | 3, in one reconverging arc | Introduction, consequential choice, first foothold |
| Recovery activity | 1 repeatable salvage action | Prevent progression dead ends |
| Recoverable material | 1: components | Links collection, contracts, upgrades, and depot |
| Currency | 1: credits | Explicit alternate reward and purchase route |
| Upgrade types | 2 mutually exclusive early options | Cargo capacity or a depot restoration discount |
| Persistent owned asset | 1 depot | Concrete ending and first empire step |
| Meaningful story branch | 1 conflict with 2 outcomes | Later agent response and a changed final cost |

Locations, character names, numeric balances, and exact contract prose are not yet finalized. Resist adding more content until this loop works.

### Essential player capabilities

1. Start or resume a persistent solo campaign with a recognizable small ship.
2. See reachable locations, cargo space, components, credits, and current objectives.
3. Meet both agents and inspect a contract’s requirements and reward before accepting.
4. Travel between unlocked locations without a real-time flight simulation.
5. Recover components with a visible cargo constraint; choose what to keep or sell.
6. Make one mutually exclusive decision about an agent’s disputed salvage claim.
7. See that decision acknowledged and reflected in a later offer or depot price.
8. Choose one affordable ship upgrade with a clear gameplay effect.
9. Restore and claim a depot, then use its storage to verify ownership has practical value.
10. Reload or reconnect without lost progress, duplicated rewards, or repeated consequences.

### Explicit exclusions

Multiplayer, PvP, player trading, global markets, procedural galaxies, planetary walking, real-time piloting, tactical combat, ship destruction, fuel simulation, crafting trees, multiple ships, crew simulation, passive income, offline production, monetization, and mobile-specific UI are deferred. Minimal keyboard access and readable layouts remain part of the browser experience.

## 6. Core loop and sample first arc

**Talk to an agent → choose a contract → prepare cargo space → travel → explore or recover → make a tradeoff → deliver or sell → observe the response → invest → pursue the next opportunity.**

An action should advance a goal, reveal information, or create a decision. Travel provides context and access; it should not become an idle timer.

### Example arc: A Place to Call Ours

All story details in this example are provisional.

1. **A Small Favor.** A hub broker needs components for a stranded maintenance crew. The player visits the salvage field, learns cargo capacity, and delivers a small load. The reward guarantees access to an initial upgrade. Introduce the second agent’s competing interest during this contract.
2. **Competing Claims.** A remote surveyor claims ownership of recovered survey equipment. The broker wants it sold to finance urgent repairs. Both explain credible stakes before commitment. Returning it improves the surveyor’s disposition and earns a depot restoration discount; selling it improves the broker’s disposition and earns additional credits. The choice changes the next conversation and cost, then both paths converge on the depot lead.
3. **A Place to Call Ours.** The player gathers the remaining materials and restores an abandoned depot. Either agent path can succeed. The final exchange references the prior choice. Claiming the depot unlocks a fixed storage allowance and ends the authored arc after the player transfers cargo into it.

The disputed object is a contract flag, not a second general-purpose commodity. Do not make either branch require content that only exists on the other branch. A choice’s intended material effect should be legible before commitment; not every line of dialogue needs an exposed numeric forecast.

## 7. Resources, progression, and recovery

Components occupy cargo slots; credits do not. Cargo capacity and storage limits are visible. Purchasing an upgrade or restoring the depot consumes the stated cost exactly once. Material collection, delivery, sale, and storage have distinct actions and understandable feedback.

Use handcrafted, stable transaction prices for the first proof. Dynamic pricing is unnecessary. Set exact values during a later balance pass, then verify that both story routes can reach the upgrade and depot without repeated grinding.

The two recommended upgrades create a visible early preference: carry more per trip, or reserve resources for cheaper depot restoration. Permit one choice in the first arc and explain the exclusivity before purchase. If that choice does not produce an observable benefit in playtests, simplify to one upgrade.

Recovery rules:

- Local travel and the basic recovery action have no mandatory entry cost.
- The player cannot purchase an upgrade before required story delivery resources are protected or recoverable.
- A full hold offers a return/sell/discard route; never require collecting an item before allowing the player to free space.
- The salvage activity can replenish components for either final route. No finite resource is silently required after it can be sold permanently.
- The client previews affordability, while the server validates actual balances and capacity.
- Failure is a setback or changed opportunity, not a permanently stranded campaign. No permadeath in this MVP.

Repeatable salvage should be a safety valve. If typical completion requires several identical salvage trips, reduce costs or increase contextual rewards before adding new systems.

## 8. Agent and narrative design

Each agent needs a practical need, a worldview, a reason to keep hiring the player, and a recognizable response to the disputed claim. Neither should be obviously foolish merely to make the other path attractive.

Track only the story flags needed for the arc and one disposition per agent, such as neutral, helped, or disappointed. Avoid a general-purpose relationship score or faction diplomacy simulation initially.

Author each consequential exchange with:

- Context and stakes, in short browser-readable text.
- Available choices, their requirements, and any intentional irreversible commitment.
- Immediate resource effects and persistent flags.
- A later acknowledgement and a concrete altered offer.
- A defined reconvergence point and both-route completion check.

Do not generate plot-critical dialogue dynamically for the MVP. Authored content provides a controllable test of continuity and consequence.

## 9. Browser experience

Recommended views are a sector map, an agent/contract panel, and a ship/cargo panel; depot storage can reuse the cargo interaction. Keep the current goal and the last action’s result visible.

Every consequential action should communicate what will happen, what it costs, and whether it can be reversed. Disable accidental repeat submission while pending, show errors with a useful next step, and distinguish pending local feedback from confirmed server state. Use a confirmation for the single major story commitment, not every routine click.

Required usability cases: keyboard navigation, readable contrast and text, no hover-only essential information, full-cargo handling, insufficient resources, lost connection, stale browser tab, and reload after a committed choice. Do not show internal implementation details in the player UI.

## 10. Server-authoritative boundary

This is a design constraint, not a framework selection or implementation specification.

| Server owns | Browser owns |
| --- | --- |
| Campaign ownership and persisted state | Rendering, navigation, and input |
| Credits, cargo, capacity, upgrades, and depot ownership | Display of the last confirmed state |
| Location access and travel eligibility | Previews based on that state |
| Contract transitions, story flags, and agent disposition | Readable dialogue and action feedback |
| Reward calculation and validation | Pending state and reconnect experience |

The browser submits player intent, such as accepting a contract or choosing a salvage outcome; it never supplies a trusted reward or resulting balance. The server checks identity, campaign ownership, preconditions, costs, and legal transitions before committing effects.

One logical action must update its costs, rewards, flags, and contract progress atomically. Retried requests must not apply twice. Stale actions from another tab must be rejected or reconciled clearly. Save after each accepted state change; reconnect reloads authoritative state. Separate campaigns must remain isolated.

The MVP needs a durable player/session association so refresh and later browser sessions resume the right campaign. A secure opaque browser session is a possible minimum; email login, account recovery, and cross-device access remain open requirements. Never trust a player-selected campaign identifier as authorization.

Recommendation: begin with request/response interactions and durable storage; no continuous simulation or real-time socket transport is required for discrete solo actions. Do not select a backend language, database, hosting platform, or scaling architecture yet. A basic health check and action-error logging will support the eventual playable test without becoming a full operations project.

## 11. Proof of completion and playtest questions

These are future acceptance criteria, not completed tests or a request to implement tests now.

| Area | Observable acceptance criterion |
| --- | --- |
| Complete loop | A fresh campaign can finish all three contracts, choose an upgrade, claim the depot, and transfer cargo into it |
| Both branches | Both disputed-claim outcomes reach the ending and produce their specified later agent response and material difference |
| Resource decisions | At least one allocation decision offers competing uses for the same components, such as selling now or reserving them for restoration; the player can explain the opportunity cost |
| Persistence | Reload after collection, delivery, upgrade purchase, branch choice, and depot claim preserves the committed result |
| Server authority | Altered client balances, unauthorized campaigns, impossible choices, and excess cargo are rejected |
| Retry safety | Duplicate delivery/purchase/claim requests apply costs and rewards once, including after a lost response |
| Recovery | Empty credits, sold components, and full cargo still permit a route to completion |
| Usability | A first-time player can identify the next objective, affordances, cargo constraint, and choice consequences |

For an initial moderated playtest, recruit a small group of target players (for example five) and record observed behavior plus short interviews. This is qualitative evidence, not statistically reliable retention data.

Provisional success signals: most can finish without designer intervention; they can name an agent and explain the tradeoff; they notice a later consequence; and they describe a reason to continue after obtaining the depot. Ask what they would do next rather than whether they “liked it.” Record time to first meaningful choice, stuck points, repeated salvage trips, and branch comprehension.

If they finish but remember no agent, revise characterization and consequences. If they care about agents but struggle with resources, simplify cargo presentation and costs. If they understand everything but feel no tension, strengthen competing goals before adding galaxy size. Do not expand merely because the feature checklist passes.

## 12. Design sequence and decisions still open

Next design steps, before any implementation:

1. Review this scope and resolve the few decisions below that change the first session.
2. Write a short playable-on-paper version of the three contracts, including exact balances and both branches.
3. Walk through fresh, low-resource, full-cargo, and reconnect scenarios on paper.
4. Revise based on whether choices express the player promise.
5. Only after a separate explicit request, plan the smallest implementation and its validation.

Open decisions, with provisional defaults:

| Question | Why it matters | Recommended working default |
| --- | --- | --- |
| What tone should the galaxy have? | Changes dialogue, agent motives, and consequences | Grounded frontier adventure with moments of warmth |
| How morally difficult should choices be? | Sets expectations for losses and irreversible outcomes | Conflicting legitimate needs; no hidden catastrophic punishment in the tutorial |
| What does “empire” ultimately mean? | Determines what the depot should foreshadow | A network of infrastructure and alliances; military power remains a later option |
| Must MVP saves work across devices? | Changes identity and account requirements | Same-browser return sessions initially; validate before implementation |
| Is a first foothold a satisfying MVP ending? | Determines the smallest complete player arc | Depot with usable storage, followed by a future lead rather than additional systems |

The confirmed choices in section 1 should not be asked again unless the user changes direction. These open decisions do not block this design draft. Team size, budget, and delivery date are unknown; no time estimate is implied by the content caps.

## 13. Handoff

Use [MVP-Design-Prompt.md](MVP-Design-Prompt.md) to continue collaboratively from this blueprint. The prompt keeps the confirmed direction, requires constructive scope challenges, and authorizes design work only. Review and amend assumptions as answers arrive.
