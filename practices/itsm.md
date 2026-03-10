# ServiceNow ITSM Best Practices

---

## Incident Priority Matrix and Auto-Assignment

### Recommended
Define a fixed Priority matrix driven exclusively by **Impact** and **Urgency** fields on the `incident` table. Use Assignment Rules (`sys_assignment_source`) to auto-route based on Category, Subcategory, and Configuration Item's support group. Set `assignment_group` via a before-insert Business Rule rather than relying on manual agent selection. Use the **Predictive Intelligence** plugin (com.glide.platform_ml) for ML-based category/assignment suggestions on high-volume queues.

### Avoid
Do not allow agents to set Priority directly — it must be derived. Do not build assignment logic as inline scripts inside Workflow or Flow Designer when a dedicated Assignment Lookup rule (navigated at **Incident > Administration > Assignment Lookup Rules**) already exists. Avoid using the legacy `incident_state` field for custom workflow branching; use the standard `state` field and Incident State Model instead.

### Why it matters
Manual priority setting creates inconsistent SLA commitments and compliance failures. Bypassing Assignment Rules means logic lives in Workflows that are invisible to operations managers and breaks when the workflow is upgraded or cloned.

### Source
ServiceNow Product Documentation — Incident Management (Washington DC release); ServiceNow CIS-ITSM Exam Study Guide, Domain 3: Incident Management Configuration

---

## SLA Definition and Pause/Stop Conditions

### Recommended
Define SLAs using **SLA Definitions** (`contract_sla` table). Set **Start condition**, **Pause condition**, **Stop condition**, and **Reset condition** using encoded query strings (not scripted conditions) wherever possible. Attach SLAs to the `incident` table via the Task SLA (`task_sla`) relationship — never manipulate `task_sla` records directly via script. Use **SLA Workflow** (field `sla_workflow`) to trigger escalation notifications at 50%, 75%, and 100% of elapsed time. Set timezone handling via the **Schedule** field on the SLA definition to respect business hours correctly.

### Avoid
Do not create SLAs with scripted start/stop conditions unless encoded queries cannot express the logic — scripted conditions fire on every record save and cannot be optimised by the query engine. Do not delete `task_sla` records to "reset" an SLA; use the **Reset** action or set the reset condition correctly on the definition. Never hardcode SLA durations in Business Rules.

### Why it matters
Incorrectly paused SLAs lead to false SLA breach reports and contractual disputes. Scripted SLA conditions significantly increase save-time latency on high-volume tables like `incident` (which may have millions of rows).

### Source
ServiceNow Developer Docs — SLA Definitions and Task SLA; ServiceNow Knowledge (Knowledge18) session "SLA Deep Dive — Configuration and Troubleshooting"

---

## Major Incident Process

### Recommended
Use the built-in **Major Incident Management** plugin (com.snc.itsm.major_incident) rather than building a custom major incident state. Configure the **Major Incident Workbench** available from the Incident form. Drive promotion to major incident via a defined criteria script on the `major_incident_state` field. Create a dedicated **Communication Plan** using the Notify plugin for stakeholder updates. Link all related incidents to the Major Incident using the Parent Incident (`parent_incident`) field, not ad-hoc related lists.

### Avoid
Do not repurpose the `category` or `subcategory` fields to track major incident status. Do not manage major incident communications via manual email — use Notify or Connect messaging to maintain an audit trail. Avoid closing related child incidents before the major incident root cause is confirmed.

### Why it matters
Homegrown major incident tracking breaks upgrade paths when ServiceNow ships improvements to the Major Incident Workbench. Unlinked related incidents prevent accurate impact analysis and post-incident review.

### Source
ServiceNow Product Documentation — Major Incident Management; ServiceNow Success Playbook: Major Incident Management

---

## Problem Management and Known Error Records

### Recommended
Use the `problem` table for root cause investigation and the `problem_task` table for investigation activities — never use incident tasks. Set **Problem State** using the OOTB state model (Open → Root Cause Analysis → Fix in Progress → Resolved → Closed). Create a **Known Error** record (`kb_knowledge` with workflow state "Published" and linked to `problem` via `cause_notes`) once a workaround is confirmed. Use **Problem → Incident** relationships via the Related Incidents list, not free-text descriptions. Enable **Continual Improvement Management** (CIM) integration to track corrective actions.

### Avoid
Do not resolve problems without completing a root cause analysis — the `cause_notes` field must be populated before the Problem can transition to "Resolved." Do not skip the Known Error step when a workaround exists; it prevents knowledge reuse at the service desk. Avoid using Problem records as change requests — they are investigative, not prescriptive.

### Why it matters
Problems closed without root cause inflate repeat incident rates. Missing Known Error records force agents to rediscover workarounds on every recurrence, directly impacting MTTR.

### Source
ServiceNow Product Documentation — Problem Management; ITIL 4 Foundation aligned with ServiceNow ITSM process model

---

## Change Management — CAB Process and Approval Workflows

### Recommended
Configure the **CAB Workbench** (requires Change Management CAB Workbench plugin: com.snc.change_management.cab_workbench). Define a **CAB Definition** record that specifies the recurring meeting schedule, membership rules, and which change types require CAB review. Use **Change Approval Policies** to drive approvals based on Change Type (Normal, Standard, Emergency) rather than hardcoding approver lists in workflows. For Normal changes, require a minimum of one Change Manager approval plus group-level approval from the Assignment Group's manager. Configure **Change Risk Assessment** using the Risk Calculator (risk score drives automatic scheduling flags).

### Avoid
Do not add ad-hoc approvers to individual change records — this bypasses audit trails and makes approval policy reporting inaccurate. Do not run CAB approvals via email only; all approvals must be captured in ServiceNow approval records (`sysapproval_approver`). Avoid approving changes by modifying `state` directly via script without going through the proper approval transition.

### Why it matters
Manual CAB approvals outside ServiceNow create compliance gaps for ITIL audits. Bypassing the Approval Policy means changes can be implemented without proper authorization, exposing the organisation to regulatory risk.

### Source
ServiceNow Product Documentation — Change Management CAB Workbench (Washington DC); ServiceNow CIS-ITSM Certification Guide, Domain 6: Change Management

---

## Standard Change Catalog

### Recommended
Implement Standard Changes as **Standard Change Proposals** promoted to a **Standard Change Catalog** (navigated at **Change > Standard Change Catalog**). Each catalog item maps to a pre-approved change model with a fixed template, risk level, and assignment group. Use **Change Templates** (`change_request_template`) to pre-populate fields. Set the Change Type to "Standard" and configure an automatic approval rule that grants instant approval when a Standard Change catalog item is selected. Retire catalog items that have not been used in 12 months via a scheduled report review.

### Avoid
Do not create Standard Changes as Normal Changes with a "Standard" label in the short description. Do not allow the standard change process to be bypassed by submitting Emergency Changes for routine, pre-approved activities. Avoid duplicating standard change templates — use Change Models as the single source of truth.

### Why it matters
Misclassified standard changes inflate CAB workload and introduce unnecessary approval delays for low-risk, routine work. Unmanaged catalog sprawl leads to outdated templates with incorrect assignment groups or missing implementation tasks.

### Source
ServiceNow Product Documentation — Standard Change Catalog; ServiceNow Knowledge (Knowledge23) session "Streamlining Change with Standard Change Catalogs"

---

## Request Management — Service Catalog and Fulfillment

### Recommended
Model all user-facing requests as **Catalog Items** (`sc_cat_item`) within the **Service Catalog**. Use **Record Producers** for ITSM table entries (incidents, problems, changes) initiated from the catalog. Fulfillment should flow through **Catalog Tasks** (`sc_task`) — never use incident tasks for catalog fulfillment. Use **Flow Designer** for fulfillment automation, connected to catalog items via the Catalog Flow trigger. Define **Approval Definitions** (`sc_approval_definition`) on catalog items rather than embedding approver logic in flows. Enable **Item Versioning** to manage changes to catalog items without disrupting in-flight requests.

### Avoid
Do not embed fulfillment logic directly inside catalog item variables via UI Actions — put it in flows or business rules. Do not use the `sc_req_item` (RITM) table for both tracking and communication — use the `sc_req` (REQ) as the parent for customer communication. Avoid creating catalog items that map directly to raw table inserts without validation — always use variable validation and Required fields.

### Why it matters
Catalog items without proper approval definitions produce ungoverned provisioning. Fulfillment built inside catalog items (rather than flows) is invisible to the process owner and breaks when the catalog item is retired or cloned.

### Source
ServiceNow Product Documentation — Service Catalog Administration; ServiceNow CIS-Service Catalog Certification Guide

---

## Assignment Rules and Escalation

### Recommended
Configure **Assignment Lookup Rules** (`sys_assignment_source`) as the primary mechanism for group and agent assignment. Sequence rules carefully — rules are evaluated in order (lowest `order` field first), and the first match wins. For escalation, use **SLA Workflow** stages (50%, 75%, 100%) combined with **Event-driven Notifications** (`sysevent`) rather than polling Business Rules. Use the `escalate` field on incident to trigger manager notifications. For VIP users, use the **VIP flag** (`sys_user.vip`) combined with Assignment Rules to route to a dedicated support group.

### Avoid
Do not build escalation logic as time-based Business Rules that query the `incident` table every few minutes — this produces full table scans at scale. Do not combine Assignment Rule logic with SLA escalation logic in the same Business Rule; keep them separate and auditable. Avoid creating more than 20 active Assignment Rules on a single table — consolidate using encoded query conditions.

### Why it matters
Polling-based escalation Business Rules on `incident` are a leading cause of node performance degradation in large instances. Over-specified assignment rules create ordering conflicts and assignment failures that go silently undetected.

### Source
ServiceNow Developer Docs — Assignment Rules; ServiceNow Performance Best Practices guide (Hi portal KB0727636)

---

## Knowledge Management Integration with ITSM

### Recommended
Enable the **Knowledge-Centered Service (KCS)** plugin (com.snc.knowledge_centered_support) to integrate knowledge creation directly into the incident resolution workflow. Configure the **Resolve with Knowledge** UI Action on the incident form so agents can attach a KB article at resolution time. Use **Knowledge Feedback** (`kb_feedback`) to surface article quality metrics. Set up **Suggested Articles** on the Incident form (via Related Search on the `incident` table, field `short_description`) to deflect tickets. Publish resolved Known Errors from Problem Management directly as KB articles using the Problem → KB relationship.

### Avoid
Do not allow agents to create KB articles outside the incident/problem resolution workflow — this produces orphaned articles with no quality review. Do not publish articles without a **Workflow** state of "Review" first (i.e., skip the draft-to-published pipeline). Avoid using KB categories that mirror your ITSM assignment group structure — KB categories should reflect the user's perspective, not the IT team's.

### Why it matters
Uncontrolled KB article creation leads to duplicate, outdated, and inaccurate content that erodes agent and user trust. Knowledge that bypasses the review workflow creates legal and compliance risk if incorrect technical information is published.

### Source
ServiceNow Product Documentation — Knowledge Management Advanced; ServiceNow KCS Verified methodology documentation

---

## Approval Workflows and Notification Design

### Recommended
Use **Flow Designer Approval steps** (not legacy Workflow Approval activities) for all new development. Define approval conditions using **Approval Rule** records (`sysapproval_rule`) so they are configurable without code changes. Send approval notifications using **Notification records** (`sysevent_email_action`) with approval-specific templates that include direct **Approve/Reject** links. Set notification **Send when** conditions carefully to avoid approval reminder spam. For multi-level approvals, use sequential approval in Flow Designer with clear stage names and timeout actions.

### Avoid
Do not use `GlideRecord` inside a notification email script to look up additional data — this executes a synchronous DB query per email sent and causes send-queue backup under load. Do not hard-code approver `sys_id` values in any approval record or flow — always reference roles or groups. Avoid building approval chains longer than 3 levels without a documented escalation path for when an approver is unavailable.

### Why it matters
Hardcoded approver sys_ids break immediately when staff changes occur and cannot be managed by business owners without admin access. GlideRecord inside email scripts has caused notification queue backlogs that delayed thousands of emails in production instances.

### Source
ServiceNow Developer Docs — Flow Designer Approval Steps; ServiceNow Knowledge (Knowledge22) session "Approval Design Patterns"
