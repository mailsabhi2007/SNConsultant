# ServiceNow Upgrade Safety Best Practices

---

## Never Modify Out-of-Box Records — Always Clone First

### Recommended
When customising any out-of-box (OOB) record — Business Rules, Script Includes, UI Actions, Notifications, ACLs, Workflows — first **copy the record** by opening it and using "Insert and Stay" (or "Copy") to create a custom version. Name the copy with a clear prefix (e.g., `Custom - [OOB Name]` or using your company prefix `x_myco_`). Disable the original OOB record if the custom version fully replaces it. For OOB Script Includes, extend or wrap the original class rather than modifying it directly. Maintain a registry of all customised OOB records in a Change Management knowledge article or a custom tracking table.

### Avoid
Do not edit OOB records directly — even for what appears to be a trivial text change. Do not deactivate OOB records without first confirming there is no dependency from another OOB component. Never modify OOB ACLs in place — create a new ACL that extends or overrides the specific case you need to handle.

### Why it matters
Modified OOB records are flagged as "customised" in the Upgrade Center. During an upgrade, ServiceNow skips updating customised OOB records — meaning bug fixes, security patches, and feature improvements shipped in the new release are silently not applied to your instance. Over time, a heavily customised instance diverges further from the OOB baseline with every upgrade, increasing technical debt exponentially.

### Source
ServiceNow Upgrade Center documentation; ServiceNow Technical Best Practices — Customisation Guidance; ServiceNow CIS-Application Development Study Guide

---

## Scoped Applications vs Global Scope

### Recommended
All new custom development must live in a **scoped application** (created via Studio or the Application menu). Assign a unique application scope prefix (e.g., `x_myco_`) that identifies your organisation's custom code. Global scope should only be used for: Business Rules on core platform tables where scoped app restrictions prevent proper operation, or legacy customisations that predate scoped app availability. Document every Global-scope customisation with a justification comment and a migration plan to scoped app.

### Avoid
Do not create new Business Rules, Script Includes, or Client Scripts in Global scope for new development. Do not mix customisation code (your logic) with configuration data (system properties, choice lists) in the same scoped app — create separate apps for separate domains. Avoid creating scoped applications with a scope prefix that conflicts with ServiceNow's reserved prefixes (`sn_`, `com_`, `sys_`).

### Why it matters
Global scope customisations are the #1 contributor to upgrade conflicts and skipped upgrade records. Every new Global script added is another record that ServiceNow's upgrade engine must flag as "customised" and skip — reducing the organisation's effective patch level. Scoped apps isolate customisations from platform code, allowing ServiceNow to upgrade OOB records independently.

### Source
ServiceNow Developer Docs — Application Scopes; ServiceNow Technical Best Practices — Scoped vs Global Development; ServiceNow Upgrade Center: Customisation Impact

---

## Tracking Customisations with Update Sets

### Recommended
Capture all configuration and code changes in **Update Sets** (`sys_update_set`). Create one Update Set per logical change (feature, bugfix, or configuration item) rather than one per developer per day. Name Update Sets with a consistent naming convention: `[JIRA/Change number] - [Brief description] - [YYYY-MM-DD]`. Mark the Update Set as "In Progress" when actively making changes and "Complete" when ready to promote. Use **Update Set Hierarchies** to group related Update Sets for a release. Export Update Sets as XML before deleting from sub-production instances to maintain a local archive. Enable **Automatic Update Set selection** (`glide.update_set.auto.select`) only in developer instances — never in production.

### Avoid
Do not work in the Default Update Set — it collects all changes indiscriminately and cannot be easily scoped for promotion. Do not commit Update Sets directly to production without a review and approval process. Avoid circular Update Set dependencies — if Update Set B requires Update Set A, document and enforce this ordering in the promotion process.

### Why it matters
Undocumented changes made without an Update Set are invisible to the Change Management process — they cannot be rolled back, cannot be promoted consistently, and will be lost when the instance is refreshed from a production clone. "Mystery changes" in production discovered during incident investigations are almost always un-tracked configuration changes made outside an Update Set.

### Source
ServiceNow Developer Docs — Update Sets; ServiceNow Application Lifecycle Management Guide; ServiceNow Technical Best Practices — Change Tracking

---

## Handling Upgrade Conflicts — Skipping vs Reverting

### Recommended
After every upgrade, review all **Upgrade Conflicts** in the Upgrade Monitor (`upgrade_history_log` list, navigated at **System Update Sets > Upgrade Monitor**). For each conflict, make a conscious decision:
- **Accept Current (Skip)**: Keep your customisation, accepting that the OOB improvement will not be applied. Document the decision with a justification. Schedule a review task to evaluate whether the OOB change should be manually merged.
- **Accept Upgrade (Revert)**: Accept the ServiceNow upgrade version, losing your customisation. Only do this if the OOB version now covers the business need.
- **Merge**: Manually review both versions side-by-side and create a merged version that incorporates both the OOB improvement and your custom logic.

Treat every "Skip" decision as technical debt — create a backlog item to resolve it.

### Avoid
Do not bulk-skip all upgrade conflicts without reviewing them individually — some skipped records may be critical security patches. Do not accept an upgrade version (revert) without first checking whether your customisation is still functionally required. Avoid leaving upgrade conflicts unresolved for more than one upgrade cycle — they accumulate and become exponentially harder to merge.

### Why it matters
Bulk-skipping upgrade conflicts has caused production instances to miss critical security patches for years. A single skipped ACL security fix left a financial services instance vulnerable to privilege escalation — discovered only during a security audit two years later. ServiceNow releases an average of 50+ security advisories per year, many of which are delivered as OOB record changes.

### Source
ServiceNow Upgrade Center; ServiceNow Product Documentation — Managing Upgrade Conflicts; ServiceNow Security Advisories (Hi portal)

---

## Instance Scan Before Upgrading

### Recommended
Run **Instance Scan** (navigated at **System Diagnostics > Instance Scan**) at least 4 weeks before every major upgrade. Run the **Upgrade Center Checks** suite, which includes: Deprecated API Usage, Customisation Density, Performance Anti-Patterns, and Security Configuration issues. Review all **Critical** and **High** severity findings and remediate them before proceeding with the upgrade. Schedule Instance Scan as a quarterly recurring task even outside of upgrade cycles to maintain ongoing hygiene. Use the **Upgrade Center** (navigated at **System Update Sets > Upgrade Center**) to preview which OOB records will conflict with your customisations before the upgrade runs.

### Avoid
Do not upgrade without running Instance Scan — it is the only automated way to identify deprecated API usage that will break after the upgrade. Do not dismiss Instance Scan findings as "informational" without triage — each finding represents a known issue that ServiceNow engineers identified as upgrade-impacting. Avoid running Instance Scan only on the production instance — run it on a cloned sub-production instance first so remediation can be tested.

### Why it matters
Instance Scan has a check specifically for deprecated APIs (e.g., `GlideRecord.getLastErrorMessage()` deprecated in Tokyo, `workflow.scratchpad` usage deprecated in Utah). Without Instance Scan, developers discover breaking changes only when automated tests fail or users report errors after the upgrade — by which time the instance is already on the new version.

### Source
ServiceNow Product Documentation — Instance Scan; Upgrade Center Preview; ServiceNow Upgrade Readiness Checklist (Hi portal KB0011227)

---

## Deprecated API Tracking

### Recommended
Subscribe to the **ServiceNow Release Notes** and **What's New** documentation for every release (available at docs.servicenow.com under the release bundle). Maintain a **Deprecated API Registry** in your CMDB or a custom table listing every deprecated API in use in your instance, the deprecation release, the removal release, and the remediation ticket. Use **Instance Scan** checks for deprecated APIs to populate this registry automatically. When a deprecated API is identified, create a Defect record and prioritise it ahead of the feature work in the upcoming release sprint.

### Avoid
Do not assume that deprecated APIs will continue to work indefinitely — ServiceNow removes deprecated APIs, typically 2–4 major releases after deprecation. Do not use APIs marked `@deprecated` in JSDoc comments in the ServiceNow developer documentation for new code. Avoid waiting until a breaking change causes a production incident to address deprecation warnings from Instance Scan.

### Why it matters
The `GlideSysAttachment.copy()` method was deprecated in Orlando and removed in Quebec — instances that ignored this deprecation had production script failures immediately after upgrading to Quebec. The `$sp.getRecord()` Service Portal API was deprecated and its removal broke dozens of custom widgets in instances that had not tracked the deprecation.

### Source
ServiceNow Release Notes — Deprecated Features (each release); Instance Scan Deprecated API checks; ServiceNow Technical Best Practices — API Lifecycle

---

## Testing Strategy Before Upgrades

### Recommended
Execute the following test phases before every major upgrade:
1. **Automated Test Framework (ATF)**: Run the full ATF test suite on the cloned/upgraded sub-production instance. Aim for a minimum of 80% coverage of critical business processes.
2. **Smoke Tests**: Manual verification of the top 20 most-used transactions (create incident, approve change, submit catalog item, etc.)
3. **Integration Tests**: Verify all inbound and outbound integrations are functioning on the upgraded instance using a dedicated integration test environment.
4. **Performance Baseline**: Run a load test on the upgraded instance and compare against the pre-upgrade baseline using the **Transaction Log** analysis.
5. **UAT**: Business stakeholder sign-off on critical process workflows before promoting the upgrade to production.

### Avoid
Do not upgrade production before completing UAT on an identically-upgraded sub-production instance. Do not use a non-cloned sub-production instance for upgrade testing — the data and configuration must match production. Avoid a testing strategy that relies entirely on manual testing — ATF automation is required for consistent regression coverage.

### Why it matters
An upgrade applied directly to production without prior testing on a clone has caused 4-hour production outages when previously-working integrations broke due to deprecated APIs. A single untested upgrade that breaks the incident creation form affects every IT support agent simultaneously until the issue is diagnosed and resolved.

### Source
ServiceNow Product Documentation — Upgrade Testing Strategy; ATF documentation; ServiceNow Upgrade Readiness Checklist; ServiceNow Success Playbook: Platform Upgrades

---

## Avoiding Core Table Modifications

### Recommended
Never add custom fields directly to core platform tables: `sys_user`, `task`, `cmdb_ci`, `sys_db_object`, `sys_dictionary`. Instead, extend the table to a child table if you need additional fields specific to your use case, or create a separate related table with a reference field back to the core table. If a custom field is genuinely required on `task` (e.g., a global custom field visible across all task types), submit a ServiceNow Support request to confirm the field addition will survive upgrades and is not already addressed by an OOB mechanism.

### Avoid
Do not add more than 5 custom fields to `task` — the table inheritance means every custom field on `task` is replicated as a column across all child tables (`incident`, `change_request`, `problem`, `sc_req_item`, etc.), inflating the database schema for every task-type query. Do not modify dictionary entries for OOB fields on core tables — this changes the field's data type, max length, or reference qualifier in ways that may break OOB validation and reporting. Avoid adding custom tables that extend `task` without a clear business justification — ServiceNow's task family already covers most ITSM use cases.

### Why it matters
Adding 10 custom fields to the `task` table adds 10 columns to every task-inheriting table. In an instance with 30 task child tables, that is 300 additional database columns that must be carried through every upgrade, every clone, and every schema migration. Core table modifications have caused upgrade failures where ServiceNow's schema migration script conflicted with a custom column that used the same name as a new OOB field introduced in the upgrade.

### Source
ServiceNow Developer Docs — Table Extension and Inheritance; ServiceNow Technical Best Practices — Core Table Modification; ServiceNow Upgrade Center: Schema Change Guidance

---

## Plugin Dependency Management

### Recommended
Before activating any ServiceNow Store application or platform plugin, check its **dependency list** in the Plugin Manager (navigated at **System Definition > Plugins**). Document all active plugins in a **Plugin Inventory** table (custom or in CMDB) with the activation date, activating admin, and business justification. When decommissioning a process, review plugin dependencies before deactivating — some plugins cannot be deactivated once active. Test all plugin activations in a sub-production instance first — plugin activation is irreversible in most cases and can change table structures.

### Avoid
Do not activate plugins in production without first testing in a clone — plugin activation can run schema migrations that alter core tables and cannot be rolled back. Do not activate a plugin to "try it out" in production — use a developer instance. Avoid activating community-developed Store apps without reviewing the publisher's ServiceNow Partner tier and checking the app's release history for compatibility with your current release.

### Why it matters
Plugin activation has caused production incidents when a newly activated plugin ran a schema migration that took 4+ hours on a large instance, locking tables and causing timeouts for all concurrent users. A deactivated plugin that other plugins depended on caused cascading script failures across 15 dependent business rules in a large-enterprise instance.

### Source
ServiceNow Product Documentation — Plugin Manager; ServiceNow Store application guidelines; ServiceNow Upgrade Center: Plugin Compatibility Matrix
