# ServiceNow Performance Best Practices

---

## GlideRecord Query Optimisation — addQuery and addEncodedQuery

### Recommended
Use `addQuery(field, operator, value)` as the primary method for building queries — it is type-safe, parameterised, and prevents injection. For complex pre-built queries (e.g., from a filter builder), use `addEncodedQuery(encodedQueryString)` where the string is either hardcoded or built from trusted system data. Chain multiple `addQuery()` calls to AND conditions together. Use `addOrCondition()` only when OR logic within a condition is genuinely required — excessive OR conditions prevent index usage. Always call `query()` after building conditions and before calling `next()`.

Example of correct usage:
```javascript
var gr = new GlideRecord('incident');
gr.addQuery('active', true);
gr.addQuery('priority', '1');
gr.setLimit(100);
gr.query();
while (gr.next()) { /* process */ }
```

### Avoid
Do not concatenate user-supplied input into `addEncodedQuery()` strings — this enables query injection. Do not call `GlideRecord.get()` inside a while loop iterating another GlideRecord — this is an N+1 query pattern. Do not query without any conditions on large tables (`incident`, `task`, `sys_log`) — this performs a full table scan.

### Why it matters
A full table scan on `incident` in a large enterprise instance (50M+ records) can run for minutes and hold a database connection for the entire duration, blocking other operations. N+1 query patterns inside loops have caused individual Business Rule executions to generate 10,000+ database queries, causing node-level memory exhaustion.

### Source
ServiceNow Developer Docs — GlideRecord API; ServiceNow Technical Best Practices — Scripting; servicenowguru.com — GlideQuery Cheat Sheet

---

## setLimit and chooseWindow for Pagination

### Recommended
Always call `gr.setLimit(n)` before `gr.query()` when you need only a bounded set of results. For paginated processing of large datasets, use `gr.chooseWindow(startRow, endRow)` to fetch a specific window of results:
```javascript
var gr = new GlideRecord('incident');
gr.addQuery('active', true);
gr.orderBy('sys_created_on');
gr.chooseWindow(0, 1000);
gr.query();
```
For processing all records in a large table, use a scheduled script that advances the window in batches to avoid holding a transaction open.

### Avoid
Do not iterate all records on high-volume tables in a single `while (gr.next())` loop without a `setLimit` — the loop will hold the database cursor open for the entire result set. Do not use `gr.getRowCount()` before iteration to size an array — it executes an additional `COUNT(*)` query. Do not use `chooseWindow` on unsorted queries — the window is not stable without an `orderBy` and will return overlapping or skipped records across batches.

### Why it matters
A GlideRecord loop on an unsized query against a 20-million-row table holds a database connection for the entire result set duration. Under concurrent load, this exhausts the database connection pool and causes `503 Service Unavailable` responses for all users — not just the user who triggered the operation.

### Source
ServiceNow Developer Docs — GlideRecord.setLimit(); GlideRecord.chooseWindow(); ServiceNow Performance Best Practices (Hi portal KB article on scripting performance)

---

## Avoiding GlideRecord in Client Scripts

### Recommended
Never make synchronous GlideRecord calls from client scripts — they are not supported and will throw errors in newer releases. For server-side lookups triggered from client scripts, use **GlideAjax** with a server-side **Script Include** that has `isPublic = true` (for Service Portal) or is accessible to the calling scope. Call `GlideAjax.getXMLAnswer()` with a callback function to process the response asynchronously without blocking the UI thread. For simple field-value lookups on reference fields, use the **`g_form.getReference()`** function (asynchronous callback variant only).

### Avoid
Do not use `GlideRecord` in client scripts — it does not work in client-side JavaScript contexts and was silently tolerated in older releases only because of legacy compatibility layers that no longer exist. Do not use the synchronous `GlideAjax.getXML()` — use the async `getXMLAnswer(callback)` version. Do not use `g_form.getReference(field)` in its synchronous (no-callback) form — it is deprecated and blocks the browser's JavaScript thread.

### Why it matters
Client-side GlideRecord calls in modern ServiceNow releases throw a hard error that breaks form functionality for all users. Synchronous server calls from the browser freeze the UI until the server responds — on a loaded server, that can be several seconds of an unresponsive form.

### Source
ServiceNow Developer Docs — GlideAjax; Client Script Scripting Guidelines; ServiceNow Developer Training: Client-Side Scripting

---

## Business Rule Ordering and Execution Type Selection

### Recommended
Choose the Business Rule execution type based on what the rule needs:
- **Before**: Modifies field values on the current record *before* the database write. Use for data normalisation, validation, setting calculated fields.
- **After**: Reads the saved record's `sys_id` or triggers related record changes *after* the DB write. Use for related record creation (e.g., creating a task when an incident is created).
- **Async**: Runs in a separate transaction after the user's transaction commits. Use for anything that does not affect the user's current save: external notifications, integration triggers, CMDB updates, and expensive calculations.
- **Display**: Populates scratchpad variables (`g_scratchpad`) on form load. Use for passing server-side data to client scripts without a GlideAjax call.

Order Business Rules explicitly (set the `order` field) to avoid unpredictable execution sequencing when multiple rules run on the same table/operation.

### Avoid
Do not use a synchronous Before or After Business Rule for any operation that could be deferred — prefer Async to minimise save latency. Do not put outbound HTTP calls, email sends, or CMDB writes in Before Business Rules. Do not rely on the default Business Rule order field value of 100 across multiple rules — always set explicit order values.

### Why it matters
An After Business Rule that performs a slow external API call adds that latency to every save operation on the table — directly impacting all users. Undefined rule ordering means that the order of execution changes when a new rule is added or an existing rule is renamed, causing hard-to-reproduce bugs.

### Source
ServiceNow Developer Docs — Business Rules; ServiceNow Technical Best Practices — When to Use Business Rules; ServiceNow CIS-Application Development Exam Guide

---

## UI Policy vs Client Script Performance

### Recommended
Use **UI Policies** for all visibility, mandatory, and read-only field toggling that can be expressed as a condition without code — they are declarative, execute faster than client scripts, and are easier for non-developers to maintain. Use **Client Scripts** only when logic cannot be expressed in a UI Policy: conditional visibility based on multiple fields, GlideAjax server calls, `g_form.showFieldMsg()`, or complex validation with error messages. Set UI Policy `Reverse if false` checkbox to automatically undo the policy when the condition is no longer true, rather than writing a paired client script.

### Avoid
Do not write a `onChange` Client Script that simply sets a field mandatory based on another field's value — a UI Policy with a condition does this declaratively with no script overhead. Do not write Client Scripts that call `g_form.setVisible()` in `onLoad` for every field that should be hidden — use UI Policies instead. Avoid more than 20 active Client Scripts on a single form — measure actual load time using the **JavaScript Log and Field Watcher** tool before adding more.

### Why it matters
Each client script loaded on a form adds browser-side JavaScript parsing and execution overhead. A form with 40 client scripts will noticeably load slower than the same form with 15 client scripts and 20 equivalent UI Policies. UI Policies are rendered and applied server-side before the form HTML is sent, eliminating the client-side flicker that occurs when client scripts modify field visibility after load.

### Source
ServiceNow Developer Docs — UI Policies; Client Scripts; ServiceNow Performance Best Practices Guide — Client-Side Performance

---

## Avoiding Synchronous Operations in Flows

### Recommended
Design Flow Designer flows to be **trigger-and-forget** from the user's perspective — flows triggered by "Record Created/Updated" run asynchronously after the transaction commits and should not block user interaction. Use **Wait for Condition** steps instead of polling loops when the flow must pause for an external event. For scheduled processing, use the **Scheduled** trigger type in Flow Designer rather than Scheduled Script Execution when visual auditability is important. Break large flows into **subflows** to keep each individual flow execution under the 30-minute timeout limit.

### Avoid
Do not call **Flow Designer flows synchronously** from a Business Rule using `FlowAPI.startFlow()` with the `current` record unless the flow result is required in the same transaction — use `FlowAPI.startFlowAsync()` instead. Do not embed long-running loops (hundreds of iterations) inside flows — they hit the 30-minute transaction limit and terminate without completing. Avoid creating flows with more than 30 steps without evaluating whether a subflow decomposition would improve maintainability and performance.

### Why it matters
A synchronous flow invocation from a Before Business Rule blocks the user's save transaction until the entire flow completes — including all wait steps. A flow that exceeds the 30-minute transaction timeout is killed mid-execution with partial side effects (some records updated, others not), creating data integrity issues.

### Source
ServiceNow Developer Docs — Flow Designer Performance; FlowAPI.startFlowAsync(); ServiceNow Knowledge (Knowledge22) session "Flow Designer Performance and Scale"

---

## Database Index Strategy

### Recommended
Ensure that fields used in frequent `addQuery()` conditions on high-volume tables are indexed. Check existing indexes in **System Definition > Tables** → the table's **Indices** related list. Create indexes via **sys_index_label** — always get ServiceNow support approval before creating indexes on core platform tables (`task`, `incident`, `sys_user`). Use the **Stats.do** diagnostic page to identify slow queries and their execution plans. For queries that combine multiple fields, consider a **composite index** but only with ServiceNow's guidance — poorly chosen composite indexes increase write overhead.

### Avoid
Do not add indexes to every frequently queried field without considering write overhead — each index slows INSERT and UPDATE operations on that table. Do not index fields with very low cardinality (e.g., a boolean field) — the query planner will ignore such indexes. Avoid requesting index creation without first checking Stats.do and confirming the query is causing measurable performance issues.

### Why it matters
An un-indexed `assignment_group` field on the `task` table in an instance with 100M task records means every assignment-group-based query performs a full table scan. Conversely, adding 20 indexes to a high-write table like `sys_log` would degrade log insert throughput by over 50%.

### Source
ServiceNow Technical Best Practices — Database Indexing; Stats.do usage guide; ServiceNow KB article on index management (KB0727413)

---

## Scheduled Job Best Practices

### Recommended
Design Scheduled Script Executions (`sysauto_script`) to run during **off-peak hours** (typically 02:00–06:00 local instance time). Limit each scheduled job to processing a bounded batch of records per run using `setLimit()` and a "last processed" watermark stored in a System Property or custom table. Always check `gs.getCurrentScopeName()` at the start of a scheduled script to prevent accidental execution in the wrong scope. Log job start time, records processed, and completion time to a custom log table for operational monitoring. Set a **Run As** user on the scheduled job with the minimum required role — not `admin`.

### Avoid
Do not create a scheduled job that loops over all records in a large table without `setLimit` — it will hold a database connection for the entire run. Do not schedule multiple jobs to run at the same time on the same table — stagger start times by at least 5 minutes. Avoid scheduled jobs that invoke complex Workflows or Flows for each record — use bulk processing patterns instead.

### Why it matters
A scheduled job without `setLimit` that runs at 00:00 on a 10M-row table can run for 4+ hours, overlapping with the next scheduled run at 01:00 and creating a cascading backlog. Multiple simultaneous scheduled jobs on the same table create database lock contention that affects all real-time operations.

### Source
ServiceNow Developer Docs — Scheduled Script Execution; ServiceNow Performance Best Practices — Scheduled Jobs; ServiceNow Technical Best Practices Guide

---

## List Rendering Performance

### Recommended
Limit list views to a maximum of 20 columns per list — each additional column adds a database column to every query. Set the **default list page size** to 20 rows (configurable in `glide.ui.list_count`). Avoid dot-walking more than 2 levels deep in list view columns (e.g., `assignment_group.manager.department.name`) — each dot-walk level adds a JOIN to the query. Use **List Collectors** sparingly on high-volume tables. Apply default filters on all list views for high-volume tables (`incident`, `task`) to prevent users from accidentally loading an unfiltered list.

### Avoid
Do not create list views without a default filter on tables with more than 100,000 records — an unfiltered list performs a full table scan plus column lookups for every displayed row. Do not use 4+ level dot-walk references in list columns — `caller_id.department.head.manager.name` executes 4 additional JOINs per query. Avoid enabling **Full Text Search** columns on the list for fields that are not in the full-text index.

### Why it matters
A list view on `incident` with 30 columns, 5 dot-walk references, and no default filter executes a query with 5 JOINs against a 50M-row table with no WHERE clause — this can take 60+ seconds and consume enough database CPU to degrade response times for all concurrent users.

### Source
ServiceNow Performance Best Practices — List Performance; ServiceNow Technical Best Practices Guide; ServiceNow Knowledge (Knowledge19) session "Diagnosing and Fixing Slow Lists"
