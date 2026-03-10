# ServiceNow Flow Designer Best Practices

---

## Flow Designer vs Legacy Workflow — When to Use Each

### Recommended
Use **Flow Designer** for all new automation development. Flow Designer is the strategic platform — it receives all new features, integrates natively with IntegrationHub, and supports the full Now Automation framework including Playbooks and Decision Tables. Use **Legacy Workflow** only to maintain or extend existing workflows that have not yet been migrated, or for processes that require features not yet available in Flow Designer (e.g., complex activity-based parallel branching with dynamic join logic). When migrating, use the **Workflow Migration Utility** (available from Washington DC release onwards) to convert legacy Workflow activities to Flow Designer equivalents.

### Avoid
Do not start new development in Legacy Workflow — it is in maintenance mode and will eventually be deprecated. Do not run parallel implementations where some processes use Legacy Workflow and others use Flow Designer for the same business process — consolidate on Flow Designer. Avoid mixing Legacy Workflow triggers with Flow Designer triggers on the same table/condition — they can both fire and produce duplicate side effects.

### Why it matters
Legacy Workflow has not received significant new features since Paris (2020). New platform capabilities — GenAI Playbooks, IntegrationHub spokes, Decision Builder, AI-assisted automation — are Flow Designer-only. Organisations that remain on Legacy Workflow are progressively locked out of the Now Automation roadmap.

### Source
ServiceNow Product Documentation — Flow Designer vs Workflow; ServiceNow Knowledge (Knowledge23) session "Migrating from Legacy Workflow to Flow Designer"; ServiceNow Roadmap announcement — Workflow deprecation timeline

---

## Subflow Design Patterns

### Recommended
Extract any logic that is reused across multiple flows into a **Subflow**. Subflows are reusable, independently testable, and version-controlled separately from parent flows. Design subflows with a clear input/output contract: define explicit **Input Variables** and **Output Variables** on the subflow. Name subflows by capability (e.g., "Assign Incident to Group," "Send Approval Notification") not by the parent process that first used them. Keep each subflow focused on a single responsibility — if a subflow takes more than 15 steps, consider whether it should be decomposed further. Store subflows in a **scoped application** matching the domain they belong to.

### Avoid
Do not duplicate logic across flows instead of creating a subflow — this creates maintenance debt where a business rule change requires updating 10 flows individually. Do not create subflows that read data and write data in the same flow — separate data retrieval subflows from mutation subflows for testability. Avoid passing entire record objects as subflow inputs when only specific field values are needed — pass the `sys_id` and let the subflow look up what it needs.

### Why it matters
Duplicated logic across 10 flows means a single logic change requires 10 separate deployments — each a manual Update Set operation. A subflow that passes entire record objects creates tight coupling between the calling flow and the subflow's internal structure, breaking when the record's schema changes.

### Source
ServiceNow Developer Docs — Subflows in Flow Designer; ServiceNow Flow Designer Best Practices (developer.servicenow.com); ServiceNow Knowledge (Knowledge22) session "Reusable Flow Patterns with Subflows"

---

## Error Handling in Flows

### Recommended
Wrap any step that can fail (IntegrationHub actions, Script steps, approval waits) in a **Try/Catch block** using the Flow Designer error handling capability. In the Catch branch, define explicit remediation actions: log the error to a custom error table, send an alert to an on-call group, and set a meaningful state on the triggering record. Use **Flow Designer's built-in Fault Handler** at the flow level as a safety net for unhandled exceptions. Store error context (step name, error message, record sys_id, timestamp) in a dedicated `u_flow_error_log` table for operational visibility.

### Avoid
Do not build flows with no error handling on steps that call external systems — unhandled exceptions cause the flow to terminate silently, leaving the triggering record in an indeterminate state. Do not use a single generic catch block that only logs "an error occurred" without capturing context. Avoid using System Logs (`gs.error()`) as the only error notification mechanism — they are high-volume and easy to miss; use targeted event-based alerts.

### Why it matters
A flow that terminates without a Fault Handler leaves the triggering record (e.g., a change request) in "In Progress" state permanently — it cannot complete or be rolled back automatically. Operations teams running 200 flows per day with no error handling have discovered failed flows weeks later only when a customer complaint surfaced a missing provisioning action.

### Source
ServiceNow Developer Docs — Flow Designer Error Handling; Try/Catch in Flow Designer; ServiceNow Flow Designer Fault Handler documentation

---

## Flow Variables Best Practices

### Recommended
Define **Flow Variables** explicitly for every value that is passed between steps. Use descriptive names with a consistent naming convention (e.g., `incident_sys_id`, `approval_result`, `assignee_email`). Set a **data type** on every flow variable — do not use string for everything; use Reference, Boolean, Integer, or Date/Time where appropriate. Keep the number of flow variables per flow to a minimum — if a flow has more than 20 variables, evaluate whether logic should be split into subflows. Use **Flow Data Pills** (the green data pill pill-picker) to pass values between steps rather than storing values in string variables and parsing them.

### Avoid
Do not store sensitive values (passwords, tokens, PII) in flow variables — they appear in the Flow Execution Log visible to anyone with the `flow_designer` role. Do not use flow variables to store large data structures (JSON blobs, arrays of thousands of items) — Flow Designer is not designed for in-memory data processing at scale. Avoid using the same flow variable for different purposes at different points in the flow — rename or create a new variable.

### Why it matters
A flow variable containing a credential or personal data appears verbatim in the execution log, which is accessible to all Flow Designer admins and anyone with the `sn_fd.admin` role. Flow variables containing multi-megabyte JSON payloads are serialised and stored in the execution context database table, causing rapid database storage growth.

### Source
ServiceNow Developer Docs — Flow Variables and Data Pills; ServiceNow Flow Designer Security Considerations; ServiceNow Knowledge (Knowledge21) session "Flow Designer Data Management"

---

## Calling Script Includes from Flows

### Recommended
For complex business logic that cannot be expressed with native Flow Designer actions, create a **Script Include** and call it from a **Script step** within the flow. The Script Include should be in the same scoped application as the flow and have `Accessible from` set to match the calling scope. Pass specific field values as parameters to the Script Include function — do not pass the entire GlideRecord object. Return a simple typed result (string, boolean, number) that can be mapped to a Flow Variable. Write the Script Include using a class-based pattern with a `process()` method for easy unit testing outside the flow.

### Avoid
Do not embed multi-line complex business logic directly in a Flow's Script step — inline scripts cannot be unit tested, version-controlled separately, or reused. Do not call Script Includes from flows using `eval()` or dynamic class instantiation based on flow variable values — this creates security risks and makes the flow's behaviour opaque. Avoid Script Includes that perform GlideRecord queries inside Flow steps that are already inside a Loop — this creates N+1 query problems at flow execution time.

### Why it matters
Inline scripts in Flow steps are stored as a blob inside the flow record — they cannot be independently searched, compared, or tested. A team with 50 flows each containing 3 inline scripts has effectively created 150 untestable code units scattered across flow definitions with no way to find or refactor them systematically.

### Source
ServiceNow Developer Docs — Script Steps in Flow Designer; Script Include Best Practices; ServiceNow Developer Certification Study Guide — Flow Designer

---

## Trigger Types — Record-Based, Schedule, Inbound Email

### Recommended
Choose triggers based on what initiates the process:
- **Record Created** / **Record Created or Updated** / **Record Updated**: Use for automation that must respond to ITSM record changes. Always set specific field conditions to prevent the flow from firing on every save.
- **Scheduled**: Use for batch processing, report generation, or maintenance operations. Set a specific run time during off-peak hours.
- **Inbound Email Action**: Use to parse inbound emails and create/update records — configure the `sys_email_action` to route to a Flow via the "Run Flow" action type.
- **ServiceNow Events**: Use `Event` trigger type to fire flows from custom event names (`gs.eventQueue()`) — provides loose coupling between the event source and the flow.

### Avoid
Do not use "Record Created or Updated" when only "Record Created" is needed — the flow fires on every save, not just creation. Do not use a Scheduled trigger for processes that should respond in real time — use a Record trigger. Avoid creating multiple flows triggered by the same condition on the same table — they can execute in an undefined order and produce race conditions.

### Why it matters
A "Record Created or Updated" trigger with no field conditions on `incident` fires every time an agent updates any field — potentially hundreds of times per day per incident. A flow designed to run once (on creation) running on every save produces duplicate task creation, duplicate notifications, and duplicate integration calls.

### Source
ServiceNow Developer Docs — Flow Designer Triggers; Inbound Email Actions; ServiceNow Event-Driven Flow Triggers documentation

---

## Avoiding Inline Scripts — Use Script Includes Instead

### Recommended
Treat Flow Designer's Script step as a thin wrapper that calls a named Script Include. The Script step should be no more than 5–10 lines that instantiate a Script Include and call a method. Move all business logic — validation, data transformation, external lookups — into the Script Include. This ensures that all logic is: discoverable (searchable in Script Includes list), testable (via Automated Test Framework), versionable (included in Update Sets as a separate record), and reusable (callable from flows, business rules, and other scripts).

### Avoid
Do not write 100-line scripts directly in Flow step script editors. Do not copy-paste the same script block into multiple flow steps — extract it to a shared Script Include. Avoid using inline scripts as a way to avoid learning the Script Include API pattern — the short-term convenience creates long-term unmaintainability.

### Why it matters
An inline script in a Flow step is stored as a single text field in the `sys_hub_flow_logic` table. There is no diff view, no test coverage, and no way to search for it from the Script Includes list. When a bug is found in that logic, the developer must know which flow and which step contains it — there is no platform-level discoverability.

### Source
ServiceNow Developer Docs — Script Steps and Script Includes in Flow Designer; ServiceNow Technical Best Practices — Code Reuse; ServiceNow Knowledge (Knowledge23) session "Patterns for Maintainable Flow Automation"

---

## Testing Flows

### Recommended
Use the **Test** button in the Flow Designer editor to run a flow against a real record in a sub-production environment before activating. Capture test scenarios in the **Automated Test Framework (ATF)** by creating a Flow step test using the `ATF Flow Designer Test Step` record. Test both happy-path and error-path scenarios — especially verify that the Catch/Fault Handler behaves correctly. Use **Flow Execution Context** logs (`sn_fd_execution_context`) to review step-by-step variable state after each test run. Before promoting flows to production, run them in a **Full Clone** of production to validate against production data volumes and ACLs.

### Avoid
Do not activate flows directly in production without sub-production testing — there is no "undo" for a flow that has already processed 500 records incorrectly. Do not test flows using the production instance's real records, even in a developer workspace — use developer or test instances. Avoid treating a single successful manual test as sufficient validation — define minimum test coverage criteria (at least happy path + two error conditions).

### Why it matters
A flow activated without error-path testing has caused bulk record state changes (e.g., 10,000 incidents moved to "Closed") that cannot be automatically reversed. Flow errors in production are customer-visible — a flow managing request fulfillment that crashes mid-execution leaves the customer's request in a broken state.

### Source
ServiceNow Developer Docs — Testing Flows; ATF Flow Designer Integration; ServiceNow Development Lifecycle Best Practices

---

## Versioning Flows

### Recommended
Use **Flow Designer Versioning** (available from San Diego release onwards) to maintain numbered versions of each flow. Before making changes to a production-active flow, create a new version rather than editing the active version in place. Document the purpose and scope of each version change in the version description field. Store flows in a **scoped application Update Set** so version history is captured alongside other application changes. Use the **Comparison view** between flow versions to review diffs before activation.

### Avoid
Do not edit the active version of a flow that is currently being executed by live records — in-flight executions reference the version that was active when they started, but mid-execution saves are risky. Do not delete old flow versions that are still referenced by in-flight execution contexts — this breaks execution log display for those runs. Avoid having more than one developer editing the same flow version simultaneously — Flow Designer has no real-time collaborative conflict resolution.

### Why it matters
Editing an active flow version while 200 records are currently being processed by it can change the logic mid-execution for records that have not yet reached that step — producing inconsistent outcomes. Deleted flow versions leave dangling references in the execution log, making audit trails unreadable and potentially causing support-case delays.

### Source
ServiceNow Developer Docs — Flow Versioning; Flow Designer Administration Guide (Washington DC); ServiceNow DevOps and ALM Best Practices
