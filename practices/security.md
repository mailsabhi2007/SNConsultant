# ServiceNow Security Best Practices

---

## ACL Design — Table, Field, and Row-Level Security

### Recommended
Design ACLs in three layers in this order of evaluation:
1. **Table-level ACLs** (`<table_name>`, operation `*`) as the default permit/deny gate
2. **Field-level ACLs** (`<table_name>.<field_name>`) for restricting sensitive columns (salary, SSN, password hashes)
3. **Row-level ACLs** using the **Condition** field or **Script** field on the ACL record to restrict access based on record data (e.g., `current.caller_id == gs.getUserID()`)

Set the **Default ACL** (table ACL with no role requirement) only if public access is intended. Use the **Security Admin** role elevation (`security_admin`) to modify ACLs — never grant this role permanently except to a break-glass account. Assign ACLs to **roles**, not directly to users or groups. Test ACLs using the **ACL Simulator** at `sys_security.do`.

### Avoid
Do not use `gs.hasRole('admin')` checks inside Business Rules as a substitute for ACLs — this logic is invisible to the ACL framework and cannot be audited. Do not create permissive table-level ACLs and rely on UI-layer hiding to protect sensitive data — ACLs must enforce server-side access control. Avoid wildcarding the `name` field in ACL records with `*` unless absolutely necessary — overly broad ACLs create unintended access grants.

### Why it matters
Missing field-level ACLs on sensitive columns (e.g., `sys_user.password`) expose data via the REST Table API even if the UI hides the field. Row-level security bypassed by UI customisation means data is only one direct API call away from exposure for any authenticated user.

### Source
ServiceNow Developer Docs — Access Control Lists (ACLs); ServiceNow Security Administration Fundamentals course; ServiceNow Security Hardening Guide

---

## Scoped Application Security

### Recommended
Build all new custom applications as **scoped applications** using the **Application Development Studio**. Define explicit **Application Access** settings (`sys_scope_privilege`) to control which tables and script includes the scoped app can read/write/create/delete. Grant cross-scope access only via explicitly declared **Script Include access** from the caller app — the called Script Include must have `Accessible from` set to "All Application Scopes" or the specific calling scope. Use `gs.getCurrentScopeName()` to validate the execution scope in sensitive Script Includes.

### Avoid
Do not develop new functionality in the **Global scope** unless it genuinely requires global access (e.g., Business Rules on core platform tables not accessible from scoped apps). Do not set Script Include `Accessible from` to "All Application Scopes" by default — only expose what is needed. Avoid storing scoped application configuration in Global scope System Properties — use scoped app properties in the application's own scope.

### Why it matters
Global scope applications have unrestricted access to all tables and APIs — a bug or injection attack in a Global script can affect the entire instance. Scoped applications enforce a security boundary that limits blast radius and makes cross-scope access explicit and auditable.

### Source
ServiceNow Developer Docs — Scoped Applications; Application Scope Privileges; ServiceNow Developer Training: Application Development in a Scoped App

---

## Credential Storage — Never in Scripts or Variables

### Recommended
Store all secrets — passwords, API keys, OAuth client secrets, private keys — in **Credential records** (`discovery_credential`, `sys_credential`, or `oauth_entity`) accessed via **Connection & Credential Aliases** (`sys_alias`). Use **System Properties** only for non-secret configuration values (feature flags, URLs, timeouts). For secrets that must be referenced in scripts, use the `SecureCredential` API (scoped: `new sn_cfg_native.SecureCredential()`) to retrieve credentials without exposing the value in script logs or Update Sets.

### Avoid
Never store credentials in:
- Script Include class-level variables or constants
- Workflow/Flow Designer flow variables (they appear in execution logs)
- System Properties (`sys_properties`) — they are included in Update Set exports
- Hardcoded strings in any server-side or client-side script
- Global Variables in Business Rules

Do not log credential values using `gs.log()`, `gs.info()`, or `gs.debug()` even temporarily during development.

### Why it matters
System Properties are exported verbatim in Update Sets. A developer exporting an Update Set for deployment to a production instance unknowingly exports hardcoded credentials. Flow Designer variables with credential values appear in the Flow execution log, visible to any user with the `flow_designer` role. Multiple real-world credential leaks have originated from ServiceNow Update Set exports committed to Git repositories.

### Source
ServiceNow Developer Docs — Credential Storage Best Practices; ServiceNow Security Hardening Guide; OWASP Secrets Management (applied to ServiceNow)

---

## Role Design and Least Privilege

### Recommended
Define roles at the functional level (e.g., `itil`, `sn_incident_read`, `catalog_admin`) rather than at the individual user level. Use **Role contains Role** (`sys_user_role_contains`) to build a role hierarchy — avoid granting multiple flat roles when a composed role would suffice. For custom applications, create application-specific roles with the app prefix (e.g., `x_myco_myapp.user`). Grant roles to **Groups** — never assign roles directly to individual user records except for break-glass emergency accounts. Review role assignments quarterly using the **User Role** report and the **Who Can** report.

### Avoid
Do not grant `admin` role to integration service accounts — use a minimum-privilege custom role. Do not grant `security_admin` to anyone who does not need to modify ACLs in their regular work — it must be elevated on demand. Avoid creating roles that mirror department structure rather than function — "Finance Department" is not a valid role; "finance_budget_approver" is.

### Why it matters
Over-privileged service accounts are a top-ranked attack vector in ServiceNow security incidents. A service account with `admin` rights that is used in an integration gives the external system the ability to read and modify any data in the instance — including HR records, security configurations, and credential storage.

### Source
ServiceNow Security Administration course (Now Learning); ServiceNow Security Hardening Guide; CIS Security Controls v8 (Principle of Least Privilege applied to ServiceNow)

---

## Security Admin Role Elevation

### Recommended
Require users to **elevate to security_admin** only for the specific session in which ACL modifications are needed. Configure the system property `glide.security.require_elevated_privileges = true` to enforce elevation before ACL edits can be made. Log all `security_admin` elevation events — they are captured in `sys_audit` by default. Create a process requiring a second approver review before any ACL change is committed to the Update Set. Revoke permanent `security_admin` from all users — the role should be granted via elevation only.

### Avoid
Do not grant `security_admin` as a permanently assigned role to any user's role list, including administrators. Do not perform ACL changes in production without first testing in a sub-production instance. Avoid making ACL changes inside the same session used for regular development work — use a separate elevated session to maintain audit clarity.

### Why it matters
Permanent `security_admin` means an attacker who compromises any admin account gains immediate ability to remove all ACLs, exposing the entire instance. Elevation-on-demand creates a friction point that prevents accidental ACL modifications and creates an audit trail of who changed what and when.

### Source
ServiceNow Security Administration course; ServiceNow Product Documentation — Security Admin Role Elevation; ServiceNow Security Hardening Guide

---

## Encrypted Fields and Data Classification

### Recommended
Use **Edge Encryption** for data that must remain encrypted at rest and in transit, stored encrypted even in the database. Use **Column-Level Encryption** (`sys_encryption_context`) for specific fields on tables that store PII, financial data, or regulated information. Mark fields as **Encrypted** in the Dictionary (`sys_dictionary`, field `encrypt_field = true`) when using the built-in encryption. Define a **Data Classification** taxonomy (Public, Internal, Confidential, Restricted) and tag tables and fields accordingly using the **Data Classification** plugin. Use the **Privacy & Data Management** module to map PII fields to GDPR, HIPAA, or other regulatory frameworks.

### Avoid
Do not rely on field-level hiding via UI Policies or Dictionary flags as a substitute for actual encryption — the data is still stored in plaintext and accessible via API. Do not encrypt fields that are used in frequent WHERE clause queries without considering the performance impact — encrypted fields cannot be indexed by the database. Avoid applying Column-Level Encryption retroactively to high-volume tables (millions of rows) without a maintenance window — the encryption migration job is resource-intensive.

### Why it matters
A UI Policy that hides a salary field provides zero protection to an API caller that bypasses the UI entirely. Column-Level Encryption without a corresponding ACL means the value is encrypted in the database but returned as plaintext by the Table API to any authenticated user with table read access.

### Source
ServiceNow Product Documentation — Column-Level Encryption; Edge Encryption; Privacy & Data Management module; GDPR compliance guidance on servicenow.com

---

## Audit Logging and Change Tracking

### Recommended
Enable **Audit** on all tables that store sensitive, regulated, or compliance-critical data — set `sys_audit_delete` and `sys_audit_field` appropriately in Table Dictionary. Use **Field-Level Auditing** selectively — auditing every field on `incident` generates extreme audit log volume; restrict to key state, assignment, and approval fields. Enable **Login Audit Trail** (`glide.sys.login_audit_trail = true`) to capture all user logins including failed attempts. Forward audit events to a SIEM using the **Export to JSON** audit scheduled export or by integrating with ServiceNow's **Event Management** (if available). Retain audit records for a minimum of 1 year per most compliance frameworks.

### Avoid
Do not disable audit on tables like `sys_user`, `sys_user_role`, `sys_user_has_role`, `sysapproval_approver`, and `sys_choice` — changes to these tables are high-risk and must always be tracked. Do not truncate the `sys_audit` table to reclaim space — archive old records to a cold store instead. Avoid auditing high-volume transactional fields (e.g., `work_notes` updates on incident) unless specifically required — audit volume on `incident` can exceed 1 billion rows annually in large enterprises.

### Why it matters
Disabled audit on `sys_user_has_role` means a privilege escalation attack (adding a role to a user account) goes completely undetected. Without a login audit trail, breach investigations cannot determine when an unauthorised user first accessed the system or what data they viewed.

### Source
ServiceNow Product Documentation — Field-Level Auditing; sys_audit table; ServiceNow Security Hardening Guide; SOC 2 Type II controls applicable to ServiceNow audit trail

---

## Input Validation and Script Injection Prevention

### Recommended
Use **Glide's built-in input sanitisation** — never trust client-supplied values in server-side scripts without validation. When constructing GlideRecord queries from user input, use parameterised `addQuery()` calls — never concatenate user input into encoded query strings. In Scripted REST API handlers, validate all input fields against an expected schema before processing. Use `GlideStringUtil.escapeHTML()` when rendering user-supplied text in HTML contexts. In client scripts, validate and sanitise field values using the catalog variable validator framework before submission.

### Avoid
Do not use `eval()` on any data that originates from user input, request parameters, or external system payloads — this enables arbitrary code execution. Do not build GlideRecord queries by string concatenation: `gr.addEncodedQuery('name=' + userInput)` — use `gr.addQuery('name', userInput)` instead. Avoid using `gs.include()` with a dynamically constructed path — this can be exploited to include unintended scripts.

### Why it matters
A script injection through an unvalidated `addEncodedQuery` call can bypass ACLs entirely by injecting operators like `NQ` (new query) to extend the query beyond its intended scope. `eval()` on external payload data has been exploited in real ServiceNow deployments to achieve remote code execution within the Rhino JavaScript engine, escalating to full instance compromise.

### Source
ServiceNow Developer Docs — GlideRecord Security; OWASP Injection Prevention applied to ServiceNow; ServiceNow Security Advisory bulletins (HI portal); ServiceNow Scripting Security Guide

---

## HTTPS Enforcement and Session Management

### Recommended
Enforce HTTPS for all instance access by setting `glide.security.use_secure_cookies = true` and configuring the instance's load balancer/CDN to redirect HTTP to HTTPS. Set session timeout via `glide.ui.session_timeout` (recommended: 30 minutes of inactivity for standard users, 15 minutes for privileged users). Enable **Multi-Factor Authentication (MFA)** for all privileged roles (`admin`, `security_admin`, `itil_admin`) via the **ServiceNow Identity Provider** or a federated IdP (Okta, Azure AD, Ping). Configure **IP Allow Lists** for admin and API access where operationally feasible.

### Avoid
Do not allow HTTP access to any ServiceNow instance — even internal/dev instances — without HTTPS. Do not set session timeouts longer than 60 minutes for any role. Do not disable the `X-Frame-Options` header (set via `glide.security.x_frame_options`) — this prevents clickjacking attacks. Avoid single-factor authentication for any account that can access or modify HR, financial, or security data.

### Why it matters
An HTTP session on an internal network is vulnerable to session token theft via passive network sniffing — the same attack vector used in Firesheep-style attacks. Sessions without MFA are vulnerable to credential stuffing attacks — a breached password from any other system gives an attacker direct ServiceNow access.

### Source
ServiceNow Security Hardening Guide; ServiceNow Product Documentation — System Security Properties; OWASP Session Management Cheat Sheet applied to ServiceNow
