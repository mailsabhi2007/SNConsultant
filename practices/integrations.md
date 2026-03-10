# ServiceNow Integration Best Practices

---

## IntegrationHub vs Custom REST Messages

### Recommended
Use **IntegrationHub spokes** (from the ServiceNow Store or built with **Action Designer**) as the default choice for any new integration with a supported third party. IntegrationHub spokes use the **Connection & Credential Alias** framework, are flow-compatible, and appear in the Flow Designer action picker without custom code. For unsupported targets, build a custom **IntegrationHub Action** using the REST step — this keeps the integration within Flow Designer's audit and retry infrastructure. Use custom **REST Message** records (`sys_rest_message`) only for scripted integrations that cannot be expressed as flows (e.g., complex dynamic URL generation or multi-step handshake protocols).

### Avoid
Do not write raw `RESTMessageV2` calls in Business Rules or Script Includes for integrations that could be modelled as IntegrationHub Actions — they are harder to audit, lack built-in retry, and are invisible to the Integration Health dashboard. Do not use the legacy `RESTMessage` (non-V2) API in new development — it is deprecated and lacks Connection Alias support. Avoid building custom integrations in Global scope when a scoped application would provide better isolation and upgrade protection.

### Why it matters
IntegrationHub provides integration-level monitoring, run history, and error replay from a single dashboard. Custom `RESTMessageV2` code scattered across Business Rules creates undocumented integration inventory that cannot be managed at scale and is invisible to ServiceNow's integration monitoring tools.

### Source
ServiceNow Developer Docs — IntegrationHub Overview; ServiceNow IntegrationHub Action Designer; REST Message v2 API Reference

---

## Import Sets vs Direct Table API for Inbound Data

### Recommended
Use **Import Sets** (`sys_import_set`) as the staging layer for all bulk inbound data from external systems — do not write directly to operational tables via the Table API. Design the Import Set data source to match the external system's native schema, then use **Transform Maps** to normalise and write to the target table. For real-time, record-at-a-time inbound data (e.g., from webhooks), use the **Table API** (`/api/now/table/{tableName}`) only if the payload is already clean and validated. For CMDB data, always route through Import Sets + IRE regardless of volume.

### Avoid
Do not use the Table API to load thousands of records in a loop from an external system — each call is a separate HTTP transaction with full authentication overhead, ACL evaluation, and Business Rule execution. Do not bypass Import Sets for CMDB population — direct Table API inserts skip IRE and create duplicate CIs. Avoid storing raw inbound payloads in operational fields (e.g., storing a JSON blob in a string field on `incident`).

### Why it matters
Bulk Table API inserts in a loop are a primary cause of integration-induced instance performance degradation. Each API call triggers all Business Rules, notifications, and workflow evaluations — what appears to be a simple 10,000-record load can generate 50,000+ Business Rule executions in a single import operation.

### Source
ServiceNow Developer Docs — Import Sets and the Ingest API; Table API Reference; ServiceNow Integration Best Practices (KB article KB0534752)

---

## Connection and Credential Aliases

### Recommended
Store all external system credentials (usernames, passwords, OAuth tokens, API keys) in **Credential records** (`discovery_credential` or `sys_credential`) accessed via a **Connection & Credential Alias** (`sys_alias`). Reference aliases by name in REST Message records and IntegrationHub Action configurations — never embed credential values inline. Use the **Connection Alias** (`sys_connection_alias`) to define the base URL and default headers for each integration endpoint, so the URL is configurable without code changes. In scoped apps, ensure the Credential record is accessible to the application scope via an explicit **Access Control** grant.

### Avoid
Never store passwords, API keys, or OAuth client secrets in: Script Include class variables, Workflow variables, Flow Designer flow variables, System Properties (`sys_properties`), or hardcoded strings in any script. Do not use the `admin` account's credentials for integration service accounts — create a dedicated, least-privilege service account. Avoid reusing a single Credential record across multiple integrations — if one integration is compromised, all are exposed.

### Why it matters
Credentials stored in System Properties or scripts are visible to any administrator who can read properties or scripts — and are exported in Update Sets, potentially leaking to non-production environments. Dedicated per-integration service accounts limit blast radius and enable credential rotation without disrupting other integrations.

### Source
ServiceNow Developer Docs — Connection and Credential Aliases; ServiceNow Security Best Practices — Credential Management; ServiceNow Developer Certification Study Guide

---

## Error Handling in Integrations

### Recommended
In all `RESTMessageV2` and IntegrationHub REST Action calls, always check the HTTP response status code explicitly:
- 2xx: process the response
- 4xx: log a permanent error (do not retry — the request is malformed)
- 5xx: trigger a retry with exponential backoff
- Network timeout: retry up to a configurable maximum

Use **IntegrationHub Error Handling** steps (Try/Catch in Flow Designer) to catch action failures and route to a compensation flow. Log all integration errors to a dedicated **Integration Error Log** table (custom `u_integration_error_log`) with fields for: source system, endpoint URL, HTTP status code, request payload (sanitised), response body, and retry count. Send alerts when error rate exceeds a defined threshold using a scheduled report or Metric query.

### Avoid
Do not silently swallow HTTP errors with empty catch blocks — this produces integrations that appear healthy while silently losing data. Do not log full request payloads including credentials or PII to `syslog` — use the dedicated integration error log with field-level masking. Avoid infinite retry loops on 4xx errors — a 400 Bad Request will never succeed on retry.

### Why it matters
Silent integration failures are the most common cause of data consistency issues between ServiceNow and external systems. An integration that logs nothing on failure provides no observable signal — incidents caused by missing data take hours to diagnose without error logs.

### Source
ServiceNow Developer Docs — REST Message Error Handling; ServiceNow IntegrationHub Try/Catch Actions; ServiceNow Integration Design Patterns

---

## Async vs Synchronous Integration Processing

### Recommended
Run all integrations that do not require an immediate response in the same transaction as **asynchronous** operations. Use **async Business Rules** to trigger outbound calls after the transaction commits, so integration latency never affects the user-facing save response time. Use **Flow Designer** with a "Record Created/Updated" trigger (which runs asynchronously after the transaction) for most outbound integrations. For truly time-critical integrations (e.g., authentication callbacks, payment confirmations), use synchronous REST within an Action that the user is explicitly waiting on — but limit this to under 2 seconds or timeout.

### Avoid
Do not make outbound HTTP calls from **before Business Rules** or **synchronous Flows** unless the external response data is required to complete the current transaction. A synchronous HTTP call adds the external system's response time directly to the user's save latency. Do not rely on `GlideSysAjax` to make server-side outbound calls from client scripts — the client waits on the full round-trip.

### Why it matters
A synchronous outbound integration call from a before Business Rule means every user who saves an incident must wait for the external system to respond. If that system is slow (500ms response instead of 50ms), all saves on that table degrade by 500ms — and if the system goes down, all saves fail.

### Source
ServiceNow Developer Docs — Business Rule Types (Async); Flow Designer Trigger Types; ServiceNow Performance Best Practices

---

## ECC Queue Usage

### Recommended
Use the **ECC Queue** (`ecc_queue`) for MID Server-based integrations requiring the MID Server to execute probes or commands on behalf of the instance. Route custom probe results back through the ECC Queue output queue. Use **ECC Queue** for SNMP, WMI, SSH, and PowerShell-based discovery and integration probes. Monitor ECC Queue depth via the **ECC Queue** list view — a consistently growing queue indicates MID Server capacity issues. Set **ECC Queue** record TTL (time-to-live) using the `glide.ecc.agent.queue.record.expiry.time` property to prevent unbounded queue growth.

### Avoid
Do not use the ECC Queue for REST/SOAP integrations that can be executed from the instance directly — ECC Queue adds latency and a MID Server dependency. Do not process ECC Queue output records with Business Rules that perform additional GlideRecord queries without a `setLimit` — this causes runaway queries when the queue is backed up. Avoid leaving unprocessed ECC Queue records indefinitely — they grow to millions of rows and degrade list view performance.

### Why it matters
An unconfigured ECC Queue TTL has caused production instances to accumulate 50M+ ECC Queue records, requiring emergency DBA intervention to truncate. ECC Queue saturation blocks all Discovery and MID-Server-based integrations simultaneously.

### Source
ServiceNow Product Documentation — ECC Queue; MID Server Administration; KB article on ECC Queue maintenance (KB0529706)

---

## OAuth Configuration

### Recommended
Use **OAuth 2.0 Provider** profiles (`oauth_entity`) for all OAuth-based integrations — configure the client ID, client secret, token URL, and scope fields. Use **Token Management** (`oauth_credential`) to store access and refresh tokens separately from the OAuth Provider configuration. Enable **automatic token refresh** by setting the token expiry buffer property, so the integration refreshes the token before it expires rather than on the first 401 response. For inbound OAuth (ServiceNow as OAuth server), configure an **OAuth Application** (`oauth_entity` with type "OAuth API endpoint for external clients") and restrict allowed scopes to the minimum required.

### Avoid
Do not store OAuth access tokens in System Properties or script variables — they are short-lived secrets that must be stored in the `oauth_credential` table with proper ACL protection. Do not use the same OAuth client application for multiple integration purposes — create separate OAuth apps per integration to enable independent revocation. Avoid using password-grant OAuth flows unless the target system requires it — use client credentials or authorization code flows instead.

### Why it matters
OAuth tokens stored in System Properties are included in Update Set exports and can be committed to version control repositories, leaking live access credentials. Per-integration OAuth apps allow security teams to revoke a compromised integration without affecting all other integrations.

### Source
ServiceNow Developer Docs — OAuth 2.0 Configuration; ServiceNow Connection and Credential Aliases for OAuth; ServiceNow Security Hardening Guide

---

## Rate Limiting and Retry Logic

### Recommended
Implement **exponential backoff** for all integration retries: first retry after 2 seconds, second after 4 seconds, third after 8 seconds, capped at 5 retries. Use **Flow Designer's Wait for Condition** step combined with a retry counter flow variable to implement backoff without blocking a worker thread. Respect the external system's rate limit headers (`Retry-After`, `X-RateLimit-Remaining`) and pause integration processing when limits are hit. For high-volume outbound integrations, use a **scheduled batch processor** (Scheduled Script Execution) to send data in batches during off-peak hours.

### Avoid
Do not implement a simple `while (retry < max) { send(); }` loop in a synchronous script — this blocks a worker thread for the entire retry duration. Do not ignore `429 Too Many Requests` responses — treat them as a signal to back off, not to retry immediately. Avoid sending real-time notifications to external systems on every field change — debounce by using a "last synced" timestamp and only propagate records that have changed since the last sync.

### Why it matters
A retry loop that blocks a worker thread for 30 seconds (5 retries × 6 seconds each) holds a Rhino JavaScript engine worker for the full duration — under concurrent load, this exhausts the worker pool and causes all form saves to queue. Rate-limit-unaware integrations can trigger IP blocks on external SaaS platforms, taking the integration offline entirely.

### Source
ServiceNow Developer Docs — Scripted REST APIs and IntegrationHub; ServiceNow Integration Design Patterns; REST API design standards (RFC 7231)

---

## Webhook Patterns for Inbound Events

### Recommended
Expose inbound webhooks via **Scripted REST APIs** (`sys_ws_definition`) in a dedicated scoped application. Validate the webhook signature (HMAC, shared secret) in the API's `beforeQuery` Script using a System Property for the secret key. Immediately enqueue the raw payload to an **Import Set** or a custom staging table and return HTTP 200 — do not process the payload synchronously in the webhook handler. Process the staged payload asynchronously via a **Business Rule** or **Scheduled Script** to decouple inbound acceptance latency from processing logic.

### Avoid
Do not perform CMDB updates, incident creation, or workflow triggers synchronously inside a Scripted REST API handler — if processing takes more than 5 seconds, the calling system will retry, producing duplicate records. Do not expose webhook endpoints without authentication — at minimum require a shared secret header. Avoid logging raw webhook payloads to `syslog` — payloads often contain PII or security-sensitive data.

### Why it matters
A synchronous webhook handler that takes 8 seconds to complete will trigger the sending system to retry after its 5-second timeout — causing the same event to be processed twice, creating duplicate incidents or duplicate CI updates. Unauthenticated webhook endpoints have been exploited to inject fabricated incident records into production instances.

### Source
ServiceNow Developer Docs — Scripted REST APIs; ServiceNow Integration Design Patterns — Webhook handling; OWASP API Security Top 10 (applied to ServiceNow)
