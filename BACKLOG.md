# SN Consultant — Product Backlog

## How to use this file
- Add ideas here as they come up during development/ideation
- Each item has a priority (High / Medium / Low), rough effort (S/M/L/XL), and status
- Move to "In Progress" when work starts, "Done" when shipped

---

## V2 — Planned

### Agent Quality

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| A1 | ServiceNow practices directory | High | L | Backlog | Curated good/bad practices shared across all agents. Option B: dedicated `consult_practices` tool, flat files in `practices/` dir by module (itsm.md, cmdb_and_discovery.md, integrations.md, security.md, performance.md, flow_designer.md, upgrade_safety.md). DB-editable overrides on top. See design discussion 2026-03-09. |
| A2 | Integration tests for handoff paths | High | M | Backlog | Test covering consultant → implementation handoff with permission gate. Catches KeyError and orphaned tool_use bugs before production. |
| A3 | `inspect_record` tool | Medium | M | Backlog | Fetch actual script/code content from live instance (business rules, script includes, flows). Agents can audit existing code instead of guessing. Requires instance credentials. |
| A4 | `format_change_request` tool | Medium | M | Backlog | Generate a CAB-ready RFC document from conversation context. Strong differentiator for the change management use case. |

### Consultant Improvements

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| C1 | Admin console shows code-default prompt as read-only reference | Medium | S | Backlog | Currently admins can paste old prompts back without seeing what the default is. Show the code default alongside the override textarea. |
| C2 | Discovery progress tracker in state | Low | M | Backlog | Track which discovery phases are complete in MultiAgentState so consultant doesn't re-ask answered questions across sessions. |

### ServiceNow Practices Knowledge Base

**Design decision (2026-03-09):** Two-layer architecture. Layer 1 = curated system practices shipped with the app (repo markdown files, manually maintained by developer, rarely change between SN releases). Layer 2 = user/org additions via existing Knowledge Base section. Both layers searched together by agents. No admin UI needed — users manage their own additions via KB, developer maintains system layer via repo. No release versioning for now — manual update when practices change.

**Trusted sources:** ServiceNow Developer Docs, Product Docs (docs.servicenow.com), Now Learning / CIS exam guides, ServiceNow Community (definitive patterns only), ServiceNow Knowledge conference sessions. Only include things that are definitively correct or wrong — no debated opinions.

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| P1 | Practices directory — curated content | High | L | Backlog | Create `practices/` dir in repo. Files: `itsm.md`, `cmdb_and_discovery.md`, `integrations.md`, `security.md`, `performance.md`, `flow_designer.md`, `upgrade_safety.md`. Consistent format per entry: `## Topic`, `### Recommended`, `### Avoid`, `### Why it matters`, `### Source`. Content from trusted sources only. Manually maintained — no versioning for now. |
| P2 | `consult_practices` tool | High | M | Backlog | New tool for all agents. Searches practices directory by keyword/topic, returns relevant entries. Layer 1 (system practices from P1) + Layer 2 (user KB entries) searched together. Called before any recommendation (consultant) or before writing code (architect). Replaces P3 — no separate admin UI needed. |
| P3 | ~~Admin UI for practices management~~ | — | — | Removed | Replaced by existing Knowledge Base section for user additions. System practices managed via repo. |
| P4 | Practices backing for OOB/Risk badge (R1) | Medium | S | Backlog | Once P1+P2 live, upgrade R1 confidence badge from "model opinion" to "verified against practices directory". Badge gets a source citation. Depends on P2 and R1. |
| P5 | Ingest system practices into ChromaDB on startup | High | M | Backlog | On app startup, auto-ingest `practices/` markdown files into ChromaDB as a separate collection. Enables semantic search via `consult_practices` tool. Re-ingests when files change. Separate collection from user KB so layers stay distinguishable for attribution (TR3). |

### Tools & Integrations

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| T1 | `generate_script` tool | Medium | M | Backlog | Produce properly formatted ServiceNow code (try/catch, GlideRecord patterns, correct scope) as a structured output rather than freeform text. |
| T2 | `validate_servicenow_script` tool | Low | L | Backlog | Static analysis of scripts against ServiceNow best practices (no current.update(), no hardcoded sys_ids, etc.) |

---

## V2 — UX & Differentiation

### User Onboarding & Discoverability

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| U1 | Clickable use-case chips in empty state | High | S | Backlog | Show 4-6 clickable prompts in the chat empty state grouped by category (Process Design, Troubleshooting, Architecture, Best Practice Check). Clicking starts the conversation. Written in real-user language, not marketing copy. |
| U2 | Persistent "What can I ask?" link | Medium | S | Backlog | Subtle link/button in sidebar or chat footer that opens a panel showing use cases by category. Always accessible after the empty state is gone. |
| U3 | Module context on first use | Low | M | Backlog | Ask user which ServiceNow modules they primarily work with during first login or settings. Use this to personalise use-case chips and agent context. |

### Trust Signals & Grounding Transparency

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| TR1 | Empty state redesign — grounding statement | High | S | Backlog | Replace generic "Start a conversation" with a factual 3-line statement of what makes this different: curated SN best practices, live instance access, tells you when something is wrong. Sits above the use-case chips (U1). Specific and factual, not marketing copy. |
| TR2 | "Grounded in:" indicator below chat input | High | S | Backlog | Subtle row below the chat input showing active knowledge layers: `✓ ServiceNow Best Practices` `✓ Your Knowledge Base` `✓ Live Instance`. Third item greyed out with "Connect your instance" nudge if credentials not configured. Reflects actual state, not static decoration. |
| TR3 | Response attribution tags | Medium | M | Backlog | Subtle tag at end of agent responses indicating which knowledge layer was used: "Based on ServiceNow ITSM best practices" / "Referencing your organisation's knowledge base" / "Verified against your instance (Washington)". Tells user how confident to be in the answer. |
| TR4 | First-conversation proactive opening message | Medium | S | Backlog | On first login, agent sends a brief opening message before user types: "I'm your ServiceNow consultant — grounded in best practices across ITSM, ITOM, CMDB, HR, and more. I can connect to your live instance for diagnostics. What are you working on?" Sets context without modal or onboarding flow. |
| TR5 | Knowledge Base page — system practices as read-only entries | High | S | Backlog | Pre-populate the Knowledge Base page with system practice entries (ITSM, CMDB, Integrations etc.) clearly badged "ServiceNow Best Practices — System" and read-only. User entries sit alongside badged "Your Organisation". Visual proof the app came with knowledge built in. Depends on P1. |

### Recommendation Transparency

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| R1 | OOB / Custom / Risk badge on recommendations | High | M | Backlog | Visual badge on every consultant recommendation: `OOB ✅`, `OOB + Config ⚙️`, `Custom ⚠️` with confidence level. Extracted from what consultant already states. Phase 1: parse response. Phase 2 (after A1): backed by practices directory. |
| R2 | "Verified against your instance" tag | Medium | S | Backlog | When implementation agent checks live instance, tag the response to signal advice is grounded in actual instance data, not generic guidance. |
| R3 | Upgrade impact indicator on custom recommendations | Medium | M | Backlog | When consultant recommends a custom approach, show an upgrade risk indicator. Requires release-awareness (see R4). |
| R4 | Release-aware responses | High | M | Backlog | Detect client's ServiceNow version from instance connection or settings. Only recommend features available in that release. Flag when a better feature exists in a newer release they could upgrade to. |

### Deliverables & Outputs

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| V1 | Conversation export as consulting summary | High | M | Backlog | Export full conversation as a formatted PDF/Word document — decisions made, recommendations, next steps. Something you can take to a meeting or send to a client. |
| V2 | Auto-generated RFC from change conversation | High | L | Backlog | At end of a change management discussion, one-click generates a CAB-ready RFC with risk assessment, rollback plan, test criteria pre-filled from conversation. Depends on A4. |
| V3 | Requirements document from discovery phase | Medium | M | Backlog | After consultant completes discovery, offer to generate a formal BRD with acceptance criteria from the conversation. |
| V4 | Decision log per conversation | Medium | S | Backlog | Track key architectural/process decisions made during a conversation ("Chose Assignment Rules over custom routing — reason: upgrade safety"). Surfaced as a summary at conversation end. |

### Instance Intelligence

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| I1 | Upgrade readiness scan | High | L | Backlog | Connect to instance, identify customisations at risk for the next release. Output prioritised list: "14 customisations at risk for Yokohama — 3 critical." |
| I2 | CMDB health score | Medium | L | Backlog | Scan for duplicate CIs, orphaned relationships, classes outside hierarchy, missing required fields. Present as a score with prioritised fix list. |
| I3 | "What changed?" forensics | High | M | Backlog | Automatically correlate recent instance changes with reported symptoms. Not just "check your logs" — connect the dots. |
| I4 | License utilisation report | Low | M | Backlog | Which modules are licensed vs actually used. Common consulting deliverable that currently takes hours manually. |

### Agent Visibility

| # | Item | Priority | Effort | Status | Notes |
|---|---|---|---|---|---|
| AG1 | Agent handoff trail as conversation timeline | Medium | M | Backlog | Show the full agent path (Consultant → Architect → Implementation) as a visible timeline per conversation. Makes multi-agent system a feature, not invisible plumbing. |
| AG2 | Conversation typed by outcome in sidebar | Low | S | Backlog | Categorise conversations in sidebar as Discovery / Architecture / Troubleshooting / Review rather than just auto-generated titles. |

---

## V3 — Ideas / Future

| # | Item | Priority | Notes |
|---|---|---|---|
| F1 | Multi-tenant support | High | Each customer org gets isolated knowledge base and preferences |
| F2 | Scheduled instance health checks | Medium | Proactive ITOM/CMDB health reports on a schedule |
| F3 | Slack / Teams integration | Medium | Bring the consultant into existing team channels |
| F4 | Instance profile memory | Medium | After several conversations the app knows your release, customisation level, modules, coding standards. Every answer calibrated to your setup. |
| F5 | Known issues log | Low | Track recurring errors seen in a client's instance. "We've seen this error twice before — last time it was caused by X." |
| F6 | Fine-tuned model on ServiceNow data | Low | Long-term — fine-tune on ServiceNow docs + resolved tickets |

---

## Done (shipped in V1)

| # | Item | Shipped |
|---|---|---|
| D1 | Multi-agent system (Consultant / Architect / Implementation) | 2026-03-08 |
| D2 | Consultant prompt rewrite — one question/turn, discovery phases, OOB feature table | 2026-03-09 |
| D3 | Anti-pattern watchlist in consultant (13 patterns) | 2026-03-09 |
| D4 | Hard technical boundary — consultant never writes code | 2026-03-09 |
| D5 | Orchestrator conversation-aware routing (last 8 messages) | 2026-03-09 |
| D6 | Structured handoff format across all agents | 2026-03-09 |
| D7 | sanitize_messages() — fix orphaned tool_use on handoff (Anthropic 400) | 2026-03-09 |
| D8 | Fix KeyError 'implementation' — reset handoff state on early returns | 2026-03-09 |
| D9 | Credit system with admin management | 2026-03-08 |
| D10 | GitHub Actions CI pipeline (API tests + Playwright E2E) | 2026-03-08 |
| D11 | DigitalOcean deployment | 2026-03-08 |
