"""
Demo data seed script for SN Consultant.

Creates a demo user with realistic ServiceNow CSM conversations demonstrating
multi-agent handoffs across real implementation challenges.

Usage (from project root):
    venv\\Scripts\\activate
    python scripts/create_demo_data.py

To reset and re-run:
    python scripts/create_demo_data.py --reset
"""

import sys
import uuid
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db_connection, init_database
from user_manager import hash_password

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "Demo@1234"
DEMO_EMAIL    = "demo@snconsultant.ai"


def ago(**kwargs) -> str:
    return (datetime.now() - timedelta(**kwargs)).isoformat()


def create_demo_user(cursor) -> str:
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (DEMO_USERNAME,))
    row = cursor.fetchone()
    if row:
        print(f"  Demo user already exists (id={row['user_id']})")
        return row["user_id"]
    user_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO users
            (user_id, username, password_hash, email,
             is_admin, is_superadmin, created_at, last_login, is_active)
        VALUES (?, ?, ?, ?, 0, 0, ?, ?, 1)
        """,
        (user_id, DEMO_USERNAME, hash_password(DEMO_PASSWORD), DEMO_EMAIL,
         ago(days=30), ago(minutes=5)),
    )
    print(f"  Created user '{DEMO_USERNAME}' (id={user_id})")
    return user_id


def delete_demo_user(cursor):
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (DEMO_USERNAME,))
    row = cursor.fetchone()
    if row:
        cursor.execute("DELETE FROM users WHERE user_id = ?", (row["user_id"],))
        print(f"  Deleted existing demo user (id={row['user_id']})")


CONVERSATIONS = [

    # ═══════════════════════════════════════════════════════════════════════
    # CONVERSATION 1  ·  HANDOFF SHOWCASE  ·  All three agents
    #
    # Challenge: Enterprise Platinum customer's P1 cases are running on
    # the wrong SLA schedule — breaching SLAs they should be hitting.
    # Root cause: schedule is hardcoded in the SLA Definition instead of
    # sourcing from the contract/account.  Full Consultant → Architect →
    # Implementation pipeline.
    # ═══════════════════════════════════════════════════════════════════════
    {
        "title": "Platinum SLA Breach — Entitlement-Contract Chain Misconfiguration",
        "days_ago": 1,
        "messages": [

            # Turn 1 — user
            {
                "role": "user",
                "content": (
                    "One of our largest enterprise accounts — Nexus Global, Platinum tier — "
                    "is escalating because their P1 cases are consistently breaching SLA. "
                    "They have a dedicated 24/7 support contract. "
                    "Our agents swear the SLA is configured correctly. "
                    "Can you diagnose what's actually happening?"
                ),
            },

            # Turn 1 — Consultant diagnoses
            {
                "role": "assistant",
                "content": """\
I've traced the likely failure chain. This is a classic SLA schedule-source misconfiguration that's invisible in demos but surfaces immediately with real accounts.

**Diagnosis: The SLA clock is using the wrong business hours schedule.**

Here is the authoritative data path ServiceNow evaluates when a P1 case opens for Nexus Global:

```
sn_customerservice_case.account  →  customer_account (Nexus Global)
  ↓
case.entitlement  →  sn_customerservice_entitlement (Platinum 24x7)
  ↓
entitlement.contract  →  ast_contract (Nexus Global Master Services Agreement)
  ↓
contract_rel_contract_sla  →  (bridge table)
    Fields: contract, sla, timezone, schedule
  ↓
sla_definition  →  (the enforcing rule with start/pause/stop conditions)
    Field: schedule  ←  THIS IS WHERE THE BREAK IS
```

**Root Cause**

The `sla_definition` record for "Platinum P1 4-Hour Resolution" almost certainly has its **Schedule** field hardcoded to `8-5 weekdays excluding holidays` — the default US Eastern business hours schedule.

The `contract_rel_contract_sla` bridge table does carry a `timezone` and `schedule` override field, but those fields are only honoured when the SLA Definition's **Schedule Source** field is set to dot-walk to the case's contract or account. If Schedule Source is left blank, ServiceNow ignores the contract-level schedule entirely and falls back to whatever is hardcoded in the SLA Definition.

For a Nexus Global P1 raised at 2 AM Tokyo time on a Sunday, the SLA clock is paused because it thinks it's outside business hours — even though their contract guarantees 24/7 coverage.

**Confirming the defect — run this in a background script:**

```javascript
var gr = new GlideRecord('task_sla');
gr.addQuery('task.account.name', 'Nexus Global');
gr.addQuery('sla.name', 'CONTAINS', 'Platinum');
gr.query();
while (gr.next()) {
    gs.log(
        'Case: ' + gr.task.getDisplayValue() +
        ' | SLA Schedule: ' + gr.sla.schedule.getDisplayValue() +
        ' | Schedule Source: ' + gr.sla.schedule_source.getDisplayValue() +
        ' | Paused: ' + gr.paused
    );
}
```

If `Schedule Source` comes back empty and `Schedule` shows a business-hours value, that confirms it.

**Secondary risk I see:** Check whether `contract_rel_contract_sla` has a record linking the Nexus Global contract to the Platinum SLA at all — or whether the case is picking up a generic SLA definition that doesn't touch the contract bridge table. If the `entitlement` field on the case is blank (common when entitlement auto-population logic fails), no contract-level SLA binding occurs and the case gets the default SLA.

This needs a proper architecture fix, not a one-off SLA record edit. Escalating to our Solution Architect to design the correct SLA chain.""",
                "metadata": {
                    "current_agent": "consultant",
                    "is_cached": False,
                    "judge_result": {
                        "hallucination_score": 0.04,
                        "is_hallucination": False,
                        "reasoning": "Grounded in ServiceNow SLA and entitlement data model",
                    },
                },
            },

            # Turn 2 — user
            {
                "role": "user",
                "content": (
                    "That matches exactly what we're seeing. Design the correct SLA architecture "
                    "for a multi-tier entitlement model — Platinum/Gold/Silver — that sources "
                    "schedule and timezone from the contract, not hardcoded values. "
                    "It needs to scale to hundreds of accounts without SLA definition sprawl."
                ),
            },

            # Turn 2 — Solution Architect (handoff from Consultant)
            {
                "role": "assistant",
                "content": """\
*Picking up from the Consultant's root-cause analysis — designing a scalable, contract-driven SLA architecture.*

---

## SLA Architecture: Service Offering → Service Commitment → Single Parameterised SLA

The key principle: **one SLA definition per priority level per tier** (12 definitions total for 3 tiers × 4 priorities), with schedule and timezone resolved dynamically at runtime from the contract — not hardcoded.

### The Correct Data Chain

```
customer_account
  └─ ast_contract  (Nexus Global Master Services Agreement)
       ├─ sold_product  (links account to purchased service tier)
       │    └─ service_offering  (Platinum Support)
       │         └─ service_commitment  (P1: Respond 15min, Resolve 4hr, 24x7)
       └─ contract_rel_contract_sla  (bridge: contract ↔ sla_definition)
            ├─ sla  →  sla_definition  ("Platinum P1 Resolution")
            ├─ schedule  →  "24x7 All Days"
            └─ timezone  →  "America/New_York" (or account timezone)
```

### SLA Definition Configuration — The Critical Fields

For "Platinum P1 — 4 Hour Resolution":

| Field | Value | Why |
|-------|-------|-----|
| Name | Platinum P1 Resolution | — |
| Table | Case [sn_customerservice_case] | — |
| Type | Resolution | — |
| Duration | 4 Hours | — |
| **Schedule Source** | `contract.schedule` | ← Dot-walks to contract_rel_contract_sla.schedule at runtime |
| Schedule | *(leave blank)* | Overridden by Schedule Source |
| **Workflow** | SLA Workflow - Resolution | Drives breach notifications |
| Start condition | `priority=1^state=1^entitlement.tier=platinum` | Tier-gated |
| Stop condition | `state=6` (Resolved) | — |
| Pause condition | `state=3` (Pending) `^hold_reason=awaiting_customer` | Avoid inflating clock on customer delays |

**Schedule Source** is the field most implementations miss. Setting it to `contract.schedule` means the SLA looks up `sn_customerservice_case.contract` → `ast_contract` → `contract_rel_contract_sla.schedule` at the moment the SLA starts. Each customer gets their contractual schedule applied without a separate SLA definition.

### Entitlement Auto-Population (Prevents the blank-entitlement failure mode)

Create a **Business Rule** on `sn_customerservice_case` to auto-populate the `entitlement` field:

```javascript
// Business Rule: "Auto-Populate Entitlement from Account Contract"
// Table: sn_customerservice_case
// When: Before Insert
// Order: 100

(function autoPopulateEntitlement(current) {
    if (current.entitlement.nil() && !current.account.nil()) {
        var ent = new GlideRecord('sn_customerservice_entitlement');
        ent.addQuery('account', current.account);
        ent.addActiveQuery();
        ent.addQuery('expires', '>', gs.nowDateTime());
        ent.orderByDesc('tier');  // prefer highest-tier active entitlement
        ent.setLimit(1);
        ent.query();
        if (ent.next()) {
            current.entitlement = ent.sys_id;
            current.contract = ent.contract;
        }
    }
})(current);
```

This ensures `contract` is populated on every new case, which is required for `Schedule Source` dot-walking to work.

### Tier Governance Model (No SLA Sprawl)

| Tier | Priority | SLA Name | Duration | Schedule Source |
|------|----------|----------|----------|-----------------|
| Platinum | P1 | Platinum P1 Resolution | 4 hr | contract.schedule |
| Platinum | P2 | Platinum P2 Resolution | 8 hr | contract.schedule |
| Gold | P1 | Gold P1 Resolution | 8 hr | contract.schedule |
| Gold | P2 | Gold P2 Resolution | 24 hr | contract.schedule |
| Silver | P1 | Silver P1 Resolution | 4 hr (bus. hrs) | account.support_schedule |

12 SLA definitions, each parameterised. Adding 200 new accounts requires zero new SLA definitions — only new `contract_rel_contract_sla` bridge records pointing to the correct schedule.

Ready to hand to Implementation for the exact configuration steps and the audit script to remediate existing breached cases.""",
                "metadata": {
                    "current_agent": "solution_architect",
                    "handoff_from": "consultant",
                    "handoff_count": 1,
                    "is_cached": False,
                    "judge_result": {"hallucination_score": 0.03, "is_hallucination": False},
                },
            },

            # Turn 3 — user
            {
                "role": "user",
                "content": (
                    "Perfect. I need the exact steps to fix Nexus Global right now, "
                    "plus a script to identify all other accounts affected by the same misconfiguration."
                ),
            },

            # Turn 3 — Implementation (handoff from Architect)
            {
                "role": "assistant",
                "content": """\
*Translating the Solution Architect's design into the immediate fix for Nexus Global and the fleet-wide audit.*

---

## Immediate Fix: Nexus Global

### Step 1 — Fix the SLA Definition Schedule Source

Navigate to: **Customer Service > SLA Definitions > Platinum P1 Resolution**

Change these two fields:

| Field | Old Value | New Value |
|-------|-----------|-----------|
| Schedule | 8-5 weekdays excluding holidays | *(clear it — leave blank)* |
| **Schedule Source** | *(blank)* | `contract.schedule` |

Save. The change applies to all **future** SLAs started on cases for Nexus Global.

---

### Step 2 — Create the contract_rel_contract_sla Bridge Record

Navigate to: **Customer Service > Contracts > [Nexus Global Master Services Agreement]**

In the **SLAs** related list, click **New**:

| Field | Value |
|-------|-------|
| Contract | Nexus Global Master Services Agreement |
| SLA | Platinum P1 Resolution |
| Schedule | 24x7 All Days |
| Timezone | Customer's timezone (e.g., `America/New_York`) |
| Active | true |

Repeat for P2, P3, P4 SLAs.

---

### Step 3 — Deploy the Entitlement Auto-Population Business Rule

In Studio or the Business Rules module, create:

```
Name:   Auto-Populate Entitlement from Account Contract
Table:  Case [sn_customerservice_case]
When:   Before > Insert
Order:  100
Active: true
Script: (paste the script from the architect's design)
```

---

### Step 4 — Remediate Currently Breached/Running SLAs for Nexus Global

Run this **background script** to cancel the misconfigured running SLA records and trigger fresh ones:

```javascript
// WARNING: Run in background script, non-production first.
// Resets running SLA records for Nexus Global to pick up the corrected schedule.

var gr = new GlideRecord('task_sla');
gr.addQuery('task.account.name', 'Nexus Global');
gr.addQuery('sla.name', 'CONTAINS', 'Platinum');
gr.addQuery('stage', 'IN', 'in_progress,paused');
gr.query();

var count = 0;
while (gr.next()) {
    gs.log('Resetting SLA ' + gr.sys_id + ' on case ' + gr.task.getDisplayValue());
    gr.setValue('stage', 'cancelled');
    gr.setValue('cancelled', true);
    gr.update();
    count++;
}
gs.log('Cancelled ' + count + ' SLA records. Re-trigger by opening/updating the cases.');
```

After running, update each affected case to trigger the SLA Business Rules and start fresh SLA records with the correct schedule.

---

### Fleet-Wide Audit: Find All Accounts with the Same Misconfiguration

```javascript
// Background Script: Identify all SLA Definitions without Schedule Source
// where the schedule is a business-hours (not 24x7) schedule.

var results = [];

var slaDef = new GlideRecord('contract_sla');
slaDef.addQuery('name', 'CONTAINS', 'Resolution');
slaDef.addQuery('schedule_source', '');          // Schedule Source is blank
slaDef.addQuery('schedule.name', 'NOT CONTAINS', '24x7'); // Not a 24x7 schedule
slaDef.query();

while (slaDef.next()) {
    // Find accounts actively using this SLA through open cases
    var cases = new GlideRecord('sn_customerservice_case');
    cases.addQuery('state', 'NOT IN', '6,7,8');  // not resolved/closed/cancelled
    cases.addJoinQuery('task_sla', 'sys_id', 'task')
         .addCondition('sla', slaDef.sys_id);
    cases.addQuery('entitlement.tier', 'IN', 'platinum,gold'); // premium tiers most at risk
    cases.query();

    while (cases.next()) {
        results.push({
            case:     cases.getValue('number'),
            account:  cases.account.getDisplayValue(),
            tier:     cases.entitlement.getDisplayValue('tier'),
            sla:      slaDef.getValue('name'),
            sla_due:  cases.getValue('sla_due')
        });
    }
}

gs.log(JSON.stringify(results, null, 2));
// Paste output into Excel — sort by sla_due ASC to triage the most urgent accounts first.
```

**Expected findings:** Any SLA Definition where `schedule_source` is blank but the account has a 24/7 contract will appear. Sort by `sla_due` ascending to prioritise the accounts at immediate breach risk.""",
                "metadata": {
                    "current_agent": "implementation",
                    "handoff_from": "solution_architect",
                    "handoff_count": 1,
                    "is_cached": False,
                    "judge_result": {"hallucination_score": 0.03, "is_hallucination": False},
                },
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════════════
    # CONVERSATION 2  ·  Consultant → Architect handoff
    #
    # Challenge: Salesforce + ServiceNow co-existence — who owns accounts,
    # how to sync without creating duplicate cases, and how to handle the
    # 1:M contact-to-account mismatch between the two platforms.
    # ═══════════════════════════════════════════════════════════════════════
    {
        "title": "Salesforce–ServiceNow Account Sync — Ownership Boundary & Dedup",
        "days_ago": 4,
        "messages": [
            {
                "role": "user",
                "content": (
                    "We're going live with ServiceNow CSM alongside Salesforce CRM. "
                    "The client insists on bi-directional account and contact sync. "
                    "Their Salesforce has contacts linked to multiple accounts — "
                    "a shared CFO contact appears under both the parent and two subsidiaries. "
                    "What breaks and how do we design around it?"
                ),
            },
            {
                "role": "assistant",
                "content": """\
This is the most common architectural collision in dual-platform implementations. Let me be specific about exactly what breaks and the defensible design patterns.

**What Breaks OOB**

ServiceNow's `customer_contact` table extends `sys_user` with a single `account` reference field — strictly 1:1 contact-to-account. When you sync a Salesforce contact linked to three accounts, ServiceNow will bind it to whichever account was most recently synced, silently dropping the other two relationships. No error, no warning.

The consequence: a case opened by the CFO contact will only show entitlements for one of the three accounts. If that isn't the account with the active Platinum contract, the case gets no SLA.

**Platform Ownership Boundary — Agree This Before Build**

The authoritative pattern for dual-platform environments:

```
Salesforce owns:
  Account (create, update, deactivate)     ← System of Record
  Contact (create, update)                 ← System of Record
  Opportunity, Order                       ← ServiceNow read-only or not synced

ServiceNow owns:
  Case (sn_customerservice_case)           ← System of Record
  Entitlement, Contract                    ← ServiceNow owns, sync summary to SFDC
  Install Base / Sold Product              ← ServiceNow owns
  SLA performance data                     ← ServiceNow owns
```

Bi-directional sync for *every* entity type is the pattern that creates infinite sync loops. Case status is the most dangerous: a case resolved in ServiceNow pushes to Salesforce, Salesforce automation fires and re-opens the case, which pushes back to ServiceNow.

**Fix for the 1:M Contact:Account Problem**

Two options depending on how complex the client's model is:

*Option A — Platform Property (Low Effort, Works for Parent/Child Hierarchies)*

Set the system property:
```
sn_customerservice.contact_relationship.restrict_within_account_hierarchy = false
```
This relaxes the 1:1 constraint and allows a contact to be linked to multiple accounts **within the same account hierarchy**. Works for the parent + subsidiary model. Does **not** work for contacts shared across unrelated accounts.

*Option B — Custom Contact-Account Relationship Table (Full Flexibility)*

Create a custom many-to-many junction table:
```
Table: u_contact_account_rel
Fields:
  contact     Reference → customer_contact
  account     Reference → customer_account
  role        String (Primary Contact / Billing / Technical)
  is_primary  Boolean (drives case entitlement lookup)
  active      Boolean
```
Modify the case entitlement auto-population Business Rule to query `u_contact_account_rel.is_primary = true` for the opening contact rather than relying on `customer_contact.account` directly.

**Sync Loop Prevention — source_system Field**

Add a custom field `u_source_system` (String: `salesforce` | `servicenow` | `manual`) to both `customer_account` and `customer_contact`. Your IntegrationHub Flow must:

```javascript
// In the Flow step before upsert:
// Check if the record's source is the opposite system
if (current.u_source_system == 'servicenow') {
    // This update originated inside ServiceNow — suppress outbound push to Salesforce
    // to prevent echo loop
    action.setPreference('skip_outbound_sync', true);
}
```

This needs the full architecture designed before any spoke configuration starts. Escalating to the Solution Architect for the IntegrationHub Flow design.""",
                "metadata": {
                    "current_agent": "consultant",
                    "is_cached": False,
                    "judge_result": {"hallucination_score": 0.04, "is_hallucination": False},
                },
            },
            {
                "role": "user",
                "content": (
                    "Go deeper on the IntegrationHub architecture — "
                    "specific Flow Designer steps, Transform Map design, "
                    "and how to handle the initial bulk load of 50,000 Salesforce accounts."
                ),
            },
            {
                "role": "assistant",
                "content": """\
*Building on the Consultant's ownership boundary design — engineering the IntegrationHub sync architecture.*

---

## IntegrationHub Salesforce Spoke: Account Sync Flow Design

### Flow: Salesforce Account → ServiceNow customer_account

**Trigger:** Scheduled (every 15 minutes for delta) + webhook (for immediate updates)

```
[Trigger: Salesforce Record Changed webhook OR Schedule]
        ↓
[Action: Salesforce Spoke — Query Accounts]
  SOQL: SELECT Id, Name, AccountNumber, Type, BillingCountry,
               ParentId, RecordType.Name, LastModifiedDate
        FROM Account
        WHERE LastModifiedDate > {last_sync_watermark}
        LIMIT 200
        ↓
[Script: Transform & Deduplicate]
  For each SF Account:
    1. Query ServiceNow: customer_account where account_number = SF.AccountNumber
    2. If found → UPDATE (patch changed fields only)
       If not found → INSERT
    3. Set u_source_system = 'salesforce'
    4. Set u_sf_account_id = SF.Id  (custom field — your dedup key)
    5. Map ParentId → customer_account.parent (requires second lookup)
        ↓
[Action: ServiceNow Table API — Upsert customer_account]
  Method: PATCH /api/now/table/customer_account/{sys_id}
  OR POST  /api/now/table/customer_account  (if new)
        ↓
[Action: Update Watermark]
  Store LastModifiedDate of last processed record in sys_properties
  Key: com.sn_csm_sf_sync.account_watermark
```

### Transform Map: Salesforce Account → customer_account

| Salesforce Field | ServiceNow Field | Transform Logic |
|-----------------|-----------------|-----------------|
| `AccountNumber` | `account_number` | Direct — use as dedup key |
| `Name` | `name` | Direct |
| `Id` | `u_sf_account_id` | Direct — store for reverse sync |
| `BillingCountry` | `country` | Direct |
| `RecordType.Name` | `u_account_tier` | Map: "Platinum Customer" → "platinum", "Enterprise" → "gold" |
| `ParentId` | `parent` | Resolve via second API call: GET `/query?account_number={parent.AccountNumber}` |
| `Type` | `category` | Map: "Customer" → "customer", "Partner" → "reseller" |

**Do not sync:** `AnnualRevenue`, `NumberOfEmployees` — these are Salesforce analytics fields with no ServiceNow equivalent and create noise in the Transform Map.

### Handling the 50,000 Account Initial Load

Never run the delta Flow for bulk loads — the watermark-based SOQL will timeout.

**Bulk Load Pattern:**

```
Phase 1 — Extract (Salesforce Data Export)
  Export: Accounts.csv via Salesforce Data Loader
  Filter: IsDeleted = false, RecordType.IsActive = true

Phase 2 — Stage (ServiceNow Import Set)
  Table: u_import_sf_accounts (Import Set table, 1:1 field mapping)
  Upload: /api/now/import/u_import_sf_accounts  (chunked, 1,000 rows/request)

Phase 3 — Transform (Transform Map run)
  Transform Map: "SF Account Import → customer_account"
  Coalesce field: account_number  (prevents duplicates on re-run)
  Run transform via: POST /api/now/table/sys_import_state

Phase 4 — Validate
  Query: SELECT COUNT(*) FROM customer_account WHERE u_source_system = 'salesforce'
  Should match Salesforce export row count ± closed/inactive accounts filtered
```

**Chunking script for the API upload:**

```python
import pandas as pd, requests, json

df = pd.read_csv("Accounts.csv")
chunks = [df[i:i+1000] for i in range(0, len(df), 1000)]

for idx, chunk in enumerate(chunks):
    payload = {"records": chunk.to_dict(orient="records")}
    r = requests.post(
        "https://instance.service-now.com/api/now/import/u_import_sf_accounts",
        json=payload, auth=("admin", "password"),
        headers={"Content-Type": "application/json"}
    )
    print(f"Chunk {idx+1}/{len(chunks)}: HTTP {r.status_code}")
```

### Reverse Sync: ServiceNow Case Summary → Salesforce

Only push **summary data** back to Salesforce — never push the full case record:

| ServiceNow Field | Salesforce Field | Frequency |
|-----------------|-----------------|-----------|
| `sn_customerservice_case.number` | `Case.ServiceNow_Case_Number__c` | On create |
| `sn_customerservice_case.state` | `Case.ServiceNow_Status__c` | On state change |
| `task_sla.sla_due` | `Case.SLA_Due__c` | On SLA start |
| `sn_customerservice_case.resolved_at` | `Case.ServiceNow_Resolved__c` | On resolution |

This keeps Salesforce account executives informed without giving ServiceNow write access to Salesforce opportunity or order data.""",
                "metadata": {
                    "current_agent": "solution_architect",
                    "handoff_from": "consultant",
                    "handoff_count": 1,
                    "is_cached": False,
                    "judge_result": {"hallucination_score": 0.04, "is_hallucination": False},
                },
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════════════
    # CONVERSATION 3  ·  Consultant only — AWA skill routing failure
    #
    # Cases aging in queue because skill definitions don't match agent
    # records. Shows cached response on the second question.
    # ═══════════════════════════════════════════════════════════════════════
    {
        "title": "AWA Skills-Based Routing — Cases Aging in Queue",
        "days_ago": 7,
        "messages": [
            {
                "role": "user",
                "content": (
                    "We went live with Advanced Work Assignment for CSM three weeks ago. "
                    "Cases for our 'Network Infrastructure' product line are sitting in queue "
                    "for 4+ hours before assignment, even though we have 12 agents available. "
                    "AWA says they're 'eligible agents: 0' for every case. What's happening?"
                ),
            },
            {
                "role": "assistant",
                "content": """\
"Eligible agents: 0" with available agents is the telltale sign of a skill mismatch. AWA will hold a work item in queue indefinitely rather than assign it to an agent missing a required skill — no error, no alert, just silent aging.

**Root Cause Diagnosis**

AWA skill enforcement works through three linked records:

```
awa_queue  (Network Infrastructure Queue)
  └─ Assignment Criteria
       └─ Skill requirement: "Network Infrastructure Support" (MANDATORY)
            ↓  checked against ↓
       sys_user_has_skill  (agent → skill mapping)
            sys_user  =  [agent]
            skill     =  cmn_skill.sys_id matching "Network Infrastructure Support"
            proficiency  =  [any]
```

The most common cause of 0 eligible agents: the **skill name in `cmn_skill`** and the **skill name in `sys_user_has_skill`** don't match exactly — usually a capitalisation difference, a trailing space, or a duplicate skill record created by two admins independently.

**Step 1 — Check for Duplicate Skill Records**

```javascript
// Background Script: Find duplicate skills by similar name
var gr = new GlideRecord('cmn_skill');
gr.addQuery('name', 'CONTAINS', 'Network');
gr.query();
while (gr.next()) {
    gs.log('Skill: [' + gr.name + '] sys_id: ' + gr.sys_id);
}
```

If you see "Network Infrastructure Support" and "network infrastructure support" as separate records, your agents are mapped to one but the queue requires the other.

**Step 2 — Check Agent Skill Records**

```javascript
// How many agents have the skill the queue actually requires?
var queueSkillSysId = 'PASTE_SYS_ID_FROM_AWA_ASSIGNMENT_CRITERIA';

var skill = new GlideRecord('sys_user_has_skill');
skill.addQuery('skill', queueSkillSysId);
skill.addQuery('user.active', true);
skill.query();
gs.log('Agents with required skill: ' + skill.getRowCount());
```

If this returns 0, none of your agents are mapped to the skill the queue requires, regardless of how many are online.

**Step 3 — Verify Agent Capacity**

AWA also blocks assignment when an agent is at capacity. Check the `awa_agent_capacity_definition` record for the CSM Case channel. If `max_cases_per_agent` is set to 1 and all 12 agents already have 1 open case each, AWA will again show 0 eligible agents.

```
Navigate to: Advanced Work Assignment > Configuration > Agent Capacity
Channel: CSM Case
Check: Max items in progress
```

**Immediate Fix**

1. Identify the canonical skill record (correct capitalisation, no duplicates)
2. Add that skill to `sys_user_has_skill` for all 12 Network Infrastructure agents
3. Check AWA Assignment Criteria on the queue — confirm it references the correct `cmn_skill.sys_id`
4. Increase agent capacity limit if that's also a factor

**Prevention**

Add a **PA Indicator** for "Cases in queue > 1 hour with 0 eligible agents" — this is not OOB but can be built on `awa_work_item` filtered by `eligible_agents=0^created_on<javascript:gs.hoursAgoEnd(1)`. Set an alert threshold of 5+ cases to page the AWA admin before queues age.""",
                "metadata": {
                    "current_agent": "consultant",
                    "is_cached": False,
                    "judge_result": {"hallucination_score": 0.04, "is_hallucination": False},
                },
            },
            {
                "role": "user",
                "content": (
                    "Got it — the duplicate skill record was the culprit. "
                    "Now we want to add omnichannel: route chat interactions alongside cases "
                    "through the same AWA queues and skill model. What's the architecture?"
                ),
            },
            {
                "role": "assistant",
                "content": """\
Serving from the knowledge base — omnichannel AWA extension is a well-documented pattern.

**Omnichannel AWA: Adding Chat to CSM Queues**

AWA uses separate **Service Channels** per work item type. You cannot combine `sn_customerservice_case` and `chat.queue.entry` in a single channel — they require separate channel definitions but can share the same skill model.

### Service Channel Configuration

| Channel | Table | Capacity Type |
|---------|-------|--------------|
| CSM Cases | `sn_customerservice_case` | Concurrent items |
| Chat Interactions | `live_group_profile` | Concurrent conversations |

Each channel has its own `awa_agent_capacity_definition`:
- Cases: Max 5 concurrent (recommended starting point)
- Chat: Max 3 concurrent (chat requires more real-time attention)
- Combined: AWA enforces **cross-channel capacity** — an agent at 5 cases + 3 chats won't receive new work from either channel

### Shared Skill Model

Skills defined in `cmn_skill` apply across all channels. An agent with "Network Infrastructure Support" skill can receive both cases and chats requiring that skill. No duplicate skill definitions needed.

### Queue Structure for Omnichannel

```
Network Infrastructure — Cases Queue  (table: sn_customerservice_case)
  Required skills: Network Infrastructure Support
  Priority: case.priority value (1=highest)

Network Infrastructure — Chat Queue  (table: live_group_profile)
  Required skills: Network Infrastructure Support
  Priority: FIFO (chat is time-sensitive)
```

### Routing Condition for Chat

In `awa_routing_condition` for the chat queue:
```
department=Network^active=true^agent_type=chat_capable
```

### Key Difference from Cases

Chat work items expire if not accepted within the **acceptance timeout** (default: 30 seconds). Unaccepted chats re-enter the queue and can be offered to the next eligible agent. Cases never expire — they age. Set your chat acceptance timeout at `awa_service_channel.acceptance_timeout` on the Chat channel record.

In **Yokohama**, if you're on Genesys Cloud CCaaS, you can route voice calls through the same skill model via the Genesys Unified Routing integration — one skill record, three channels (case, chat, voice).""",
                "metadata": {
                    "current_agent": "consultant",
                    "is_cached": True,
                    "judge_result": {"hallucination_score": 0.03, "is_hallucination": False},
                },
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════════════
    # CONVERSATION 4  ·  Consultant → Architect handoff
    #
    # Challenge: PCSO alert storm — a network event auto-created 300 cases
    # simultaneously, flooding agent queues. Design the correct gate logic.
    # ═══════════════════════════════════════════════════════════════════════
    {
        "title": "PCSO Alert Storm — Proactive Case Flood Prevention",
        "days_ago": 11,
        "messages": [
            {
                "role": "user",
                "content": (
                    "We enabled Proactive Customer Service Operations last month. "
                    "Last Tuesday a network degradation event fired PCSO rules and "
                    "auto-created 312 cases simultaneously for every customer with "
                    "a network CI in their install base. "
                    "Agents couldn't see their normal queue. How do we prevent this?"
                ),
            },
            {
                "role": "assistant",
                "content": """\
This is the single most common PCSO go-live failure. The issue is not PCSO itself — it's that the alert-to-case rules fired without deduplication or aggregation gates.

**What Happened**

PCSO's case-creation logic follows this chain:

```
em_event (raw event from monitoring)
    ↓ Event Rules
em_alert (correlated alert)
    ↓ PCSO Rule: "Create Case when alert severity = Critical AND CI has install base"
sn_customerservice_case (one case per account with a matching install_base_item)
```

If a network degradation affects a shared CI (e.g., a core router), every customer account that has that CI in their install base (`sn_installed_base_item`) gets a separate case. With 312 accounts on that CI, you get 312 cases — simultaneously.

**Root Causes**

1. **No alert count threshold**: The PCSO rule fired on the first alert, not after confirming sustained degradation. A single event spike (which could be a monitoring tool blip) triggered mass case creation.

2. **No alert deduplication**: Multiple alerts for the same CI within a time window were each treated as independent triggers.

3. **No account-tier filter**: PCSO created cases for every account with the CI — including Silver/Standard tier customers where proactive service isn't part of their contract.

4. **No case aggregation**: Instead of one "parent" major customer case with child notifications, 312 independent cases were created with no relationship to each other.

**Diagnostic — What to Check**

```javascript
// How many accounts were affected by the alert?
var gr = new GlideRecord('sn_installed_base_item');
gr.addQuery('ci', 'PASTE_AFFECTED_CI_SYS_ID');
gr.addQuery('install_status', '1');  // Installed
gr.addQuery('account.active', true);
gr.query();
gs.log('Accounts with this CI in install base: ' + gr.getRowCount());
```

If this returns 312, your PCSO rule has no tier filter, and any critical alert on this CI will repeat the flood.

This needs a full architectural redesign of the PCSO rule conditions and a Major Customer Incident pattern for mass-impact events. Escalating to Solution Architect.""",
                "metadata": {
                    "current_agent": "consultant",
                    "is_cached": False,
                    "judge_result": {"hallucination_score": 0.05, "is_hallucination": False},
                },
            },
            {
                "role": "assistant",
                "content": """\
*Picking up from the Consultant's diagnosis — designing the corrected PCSO architecture with appropriate gates.*

---

## Redesigned PCSO Architecture: Alert Gates + MCI Aggregation

### Three-Gate Model

Every PCSO rule should enforce three gates before case creation:

```
em_alert fires (severity = Critical)
        |
Gate 1: Sustained degradation check
  Condition: alert.count >= 3  AND  alert.last_occurrence > gs.minutesAgoEnd(-10)
  Purpose: Filters monitoring blips; requires confirmed, recurring alerts
        |
Gate 2: Account tier filter
  Condition: install_base_item.account.u_support_tier IN ('platinum','gold')
  Purpose: Proactive service is a Platinum/Gold entitlement, not Standard
        |
Gate 3: De-duplicate by event fingerprint
  Condition: No open case exists WHERE u_pcso_event_id = alert.sys_id
  Purpose: Prevents duplicate cases if the alert re-fires during the same incident
        |
Decision: How many accounts affected?
  COUNT(install_base_item.account) where CI = alert.cmdb_ci
    ├─ 1–5 accounts  →  Create individual cases per account (standard PCSO)
    └─ 6+ accounts   →  Create ONE Major Customer Incident + notify all accounts
```

### PCSO Rule Configuration — Corrected

Navigate to: **Customer Service > Proactive Cases > PCSO Rules > New**

| Field | Value |
|-------|-------|
| Name | Network Degradation — Proactive Case (Gated) |
| Active | true |
| Alert condition | `severity=1^count>=3^u_event_type=network_degradation` |
| Run frequency | Every 5 minutes (not on every alert update) |
| **Before create script** | (see below — the gate logic) |

**Before Create Script:**

```javascript
(function beforeCreate(alertRecord) {
    var ciSysId = alertRecord.getValue('cmdb_ci');
    var eventId = alertRecord.getValue('sys_id');

    // Gate 3: Check for existing open case with same event ID
    var existing = new GlideRecord('sn_customerservice_case');
    existing.addQuery('u_pcso_event_id', eventId);
    existing.addQuery('state', 'NOT IN', '6,7,8');
    existing.query();
    if (existing.next()) {
        gs.log('PCSO: Duplicate suppressed for alert ' + eventId);
        answer = false;   // cancel case creation
        return;
    }

    // Gate 2: Count affected premium accounts
    var accounts = new GlideRecord('sn_installed_base_item');
    accounts.addQuery('ci', ciSysId);
    accounts.addQuery('account.u_support_tier', 'IN', 'platinum,gold');
    accounts.addQuery('install_status', '1');
    accounts.query();
    var affectedCount = accounts.getRowCount();

    if (affectedCount > 5) {
        // Mass impact — trigger MCI pattern instead of individual cases
        gs.log('PCSO: Mass impact (' + affectedCount + ' accounts). Creating MCI.');
        createMajorCustomerIncident(alertRecord, affectedCount);
        answer = false;  // cancel individual case creation
    }
    // 1–5 accounts: allow normal PCSO case creation per account
})(current);
```

### Major Customer Incident (MCI) Aggregation Pattern

When Gate 3 fires (6+ accounts affected), create a single MCI case:

```
sn_customerservice_case (MCI)
  priority = 1
  case_type = Major Customer Case
  u_is_mci = true
  u_affected_account_count = 312
  u_pcso_event_id = alert.sys_id
  short_description = "Network Degradation — Multiple Accounts Affected"
    ↓
Flow Designer: "MCI Notification Flow"
  For each affected Platinum/Gold account:
    → Send proactive notification email to account.primary_contact
    → Template: "We have detected an issue affecting your service..."
    → Create child case linked to MCI (relationship: parent_case → MCI)
```

### PA Monitoring for PCSO Health

Add these two indicators to your CSM Operations dashboard:

| Indicator | Alert Threshold | Action |
|-----------|----------------|--------|
| PCSO Cases Created per Hour | > 20 | Page CSM Platform Admin |
| Cases with u_pcso_event_id (open, age > 4hr) | > 10 | Escalate to Support Manager |

This converts PCSO from a case flood mechanism into a precision early-warning system.""",
                "metadata": {
                    "current_agent": "solution_architect",
                    "handoff_from": "consultant",
                    "handoff_count": 1,
                    "is_cached": False,
                    "judge_result": {"hallucination_score": 0.04, "is_hallucination": False},
                },
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════════════
    # CONVERSATION 5  ·  Consultant only — Now Assist + case deflection
    # Shows cached response on the second question.
    # ═══════════════════════════════════════════════════════════════════════
    {
        "title": "Now Assist Case Deflection — Measuring and Improving Deflection Rate",
        "days_ago": 16,
        "messages": [
            {
                "role": "user",
                "content": (
                    "We're rolling out Now Assist on our customer portal. "
                    "Leadership wants a deflection rate metric. "
                    "How do we measure it accurately, and what's a realistic target "
                    "for a B2B CSM portal in Xanadu?"
                ),
            },
            {
                "role": "assistant",
                "content": """\
Deflection rate is the most requested and most incorrectly measured metric in CSM portal implementations. Let me give you the precise definition and the data model behind it.

**The Correct Deflection Rate Formula**

```
Deflection Rate =
    (Portal Sessions with AI Interaction but NO Case Created)
    ─────────────────────────────────────────────────────────  × 100
    (All Portal Sessions with AI Interaction)
```

The common mistake is using "KB article views" as the numerator — that overcounts dramatically because customers read articles *after* submitting a case, not instead of submitting one.

**Where the Data Lives in ServiceNow**

| Metric | Table | Key Field |
|--------|-------|-----------|
| Portal sessions | `sys_user_session` filtered by portal user | `logged_in_url` CONTAINS 'csm_portal' |
| AI Search interactions | `ai_search_usage_log` | `result_clicked = true` |
| Now Assist interactions | `sn_gf_prompt_request` | `source = 'csm_portal'` |
| Cases submitted via portal | `sn_customerservice_case` | `source = 'portal'` |
| KB articles that preceded a case | `kb_use` + case join | `kb_use.created_on < case.opened_at` |

**Building the Deflection PA Indicator**

```
Indicator: Portal Deflection Rate
Type: Percentage
Numerator:  COUNT(ai_search_usage_log)
            WHERE result_clicked = true
            AND   session_id NOT IN
                  (SELECT session_id FROM sn_customerservice_case WHERE source = 'portal'
                   AND opened_at WITHIN same session window)
Denominator: COUNT(ai_search_usage_log) WHERE result_clicked = true
Frequency: Daily
Breakdown: Portal Section (AI Search, Virtual Agent, Now Assist chat)
```

This requires a **Formula Indicator** combining two automated collectors because the session join logic can't be expressed as a single table aggregate. Build it as two separate indicator records and reference them in a formula indicator.

**Realistic Targets for B2B CSM (Xanadu)**

| Deflection Source | Realistic Range | Best-in-Class |
|------------------|-----------------|---------------|
| AI Search (keyword + semantic) | 18–25% | 30% |
| Now Assist generative answers | +8–12% incremental | +15% |
| Virtual Agent (transactional) | +5–8% incremental | +10% |
| **Combined total** | **30–40%** | **50%+** |

B2B deflection is structurally lower than B2C because enterprise customers have complex, configuration-specific questions that KB articles rarely fully answer. A 35% deflection rate in B2B is genuinely excellent. Be cautious of leadership targets above 50% — they're achievable only when the KB is comprehensive and actively maintained via KCS.

**The KCS Loop — Closing the Gap**

Every case that bypasses deflection is a potential KB article. Enable the KCS prompt on case resolution:

```
Knowledge Management property: glide.knowman.case_close_prompt = true
```

This surfaces a prompt asking agents to create or link a KB article when closing a case. Track KB article creation rate as a paired metric to deflection rate — if deflection plateaus, KB article creation rate will tell you why.""",
                "metadata": {
                    "current_agent": "consultant",
                    "is_cached": False,
                    "judge_result": {"hallucination_score": 0.04, "is_hallucination": False},
                },
            },
            {
                "role": "user",
                "content": (
                    "How does Now Assist for CSM in Yokohama change the deflection architecture "
                    "compared to Xanadu?"
                ),
            },
            {
                "role": "assistant",
                "content": """\
Serving from the knowledge base — this is a well-indexed release comparison.

**Now Assist Deflection: Xanadu → Yokohama Delta**

The fundamental shift in Yokohama is moving from **reactive AI** (customer asks, AI answers) to **agentic interception** (AI acts before the customer submits).

| Capability | Xanadu | Yokohama | Architectural Impact |
|-----------|--------|----------|---------------------|
| Portal AI Search | Semantic search, surfaces KB links | Same, plus AI Agents deliver direct answers inline (not just links) | Deflection happens *inside* the case form, not before it |
| Email-to-Case | Auto-creates `sn_customerservice_case` on inbound email | Creates `sn_interaction` first; agent reviews before promoting to case | Reduces noise cases by ~30%; changes case volume metric baseline |
| Triage Cases Agentic Workflow | Agent Assist suggestions (passive) | Autonomous AI gathers missing data, validates entitlement, responds to informational requests without human | Changes staffing model — agents handle exceptions, not routine triage |
| Virtual Agent | Script + AI Search hybrid | Scheduling, appointment booking, entitlement self-service natively | Transactional deflection expands beyond informational |
| Case Form Portal | KB suggestions appear in sidebar | AI Agents deliver natural language answers *inside* the description field as customer types | Intercepts at point of intent — highest-quality deflection |

**Architectural Implication for Your Portal**

In Xanadu, your deflection funnel looks like:

```
Customer lands on portal → AI Search → KB article → (no case) ✓ OR (submits case) ✗
```

In Yokohama, with AI Agents in the Case Form:

```
Customer starts filling case form
    ↓
As they type the description, AI Agent interprets intent
    ↓
AI Agent delivers a direct generative answer inline
    ↓
Customer reads answer → (abandons form) ✓  OR  (submits anyway) ✗
```

This moves deflection from **pre-submission** (Xanadu) to **at-submission** (Yokohama), capturing customers who previously bypassed the search step and went directly to the case form — historically your hardest-to-deflect segment.

**Measurement Change Required**

In Yokohama, the "portal session with AI interaction but no case created" formula breaks for the new Email-to-Interaction flow, because cases are no longer created directly from email — they become interactions first. You'll need to update your denominator:

```
Updated Denominator =
    Portal sessions with AI interaction
    + Inbound email interactions (sn_interaction.source = 'email')
      that did NOT escalate to a case within 24 hours
```

Adjust your PA Indicator formula before upgrading to Yokohama to avoid deflection rate appearing artificially inflated.""",
                "metadata": {
                    "current_agent": "consultant",
                    "is_cached": True,
                    "judge_result": {"hallucination_score": 0.03, "is_hallucination": False},
                },
            },
        ],
    },
]


def seed_conversations(cursor, user_id) -> list[int]:
    conv_ids = []
    for conv in CONVERSATIONS:
        base_dt = datetime.now() - timedelta(days=conv["days_ago"], hours=2)
        last_dt = base_dt + timedelta(minutes=len(conv["messages"]) * 3)
        msg_count = sum(1 for m in conv["messages"] if m["role"] != "system")

        cursor.execute(
            """
            INSERT INTO conversations (user_id, title, started_at, last_activity, message_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, conv["title"], base_dt.isoformat(), last_dt.isoformat(), msg_count),
        )
        conv_id = cursor.lastrowid

        for i, msg in enumerate(conv["messages"]):
            msg_dt = base_dt + timedelta(minutes=i * 3 + (2 if msg["role"] == "assistant" else 0))
            cursor.execute(
                """
                INSERT INTO messages (conversation_id, role, content, tool_calls, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    conv_id, msg["role"], msg["content"],
                    json.dumps(msg.get("tool_calls")) if msg.get("tool_calls") else None,
                    json.dumps(msg.get("metadata", {})),
                    msg_dt.isoformat(),
                ),
            )

        conv_ids.append(conv_id)
        print(f"    '{conv['title']}' (id={conv_id}, {msg_count} messages)")

    return conv_ids


SESSIONS = [
    (0,  1200, 8),  (1,  2100, 14), (2,  3600, 22), (4,   900, 6),
    (5,  2700, 17), (7,  1800, 11), (8,  3900, 25), (10, 1500, 9),
    (11, 2400, 15), (15, 3000, 19), (16, 2100, 13),
]


def seed_sessions(cursor, user_id):
    for days_ago, duration, prompts in SESSIONS:
        started = datetime.now() - timedelta(days=days_ago, hours=1)
        ended   = started + timedelta(seconds=duration)
        cursor.execute(
            """
            INSERT INTO user_sessions
                (session_id, user_id, started_at, ended_at, last_activity, prompt_count, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), user_id,
             started.isoformat(), ended.isoformat(), ended.isoformat(),
             prompts, duration),
        )
    print(f"  {len(SESSIONS)} sessions (16-day history)")


PREFERENCES = [
    ("Always include exact table names, field names, and sys_ids in technical explanations",
     "ServiceNow CSM configuration and scripting"),
    ("Frame recommendations in terms of business impact and implementation risk",
     "Architecture and design conversations"),
    ("Include before/after comparisons and migration considerations",
     "Platform upgrade and redesign discussions"),
    ("Show the anti-pattern alongside the recommended pattern",
     "Best practice and governance conversations"),
]


def seed_preferences(cursor, user_id):
    for i, (text, context) in enumerate(PREFERENCES):
        cursor.execute(
            """
            INSERT INTO user_learned_preferences (user_id, preference_text, context, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, text, context, ago(days=20 - i * 4)),
        )
    print(f"  {len(PREFERENCES)} learned preferences")


DOCUMENTS = [
    ("CSM_Implementation_Playbook_Xanadu.pdf",          "pdf",  3_100_000, 247, 25),
    ("Entitlement_SLA_Design_Patterns_v4.pdf",           "pdf",  1_850_000, 142, 20),
    ("Salesforce_ServiceNow_Integration_Architecture.pdf","pdf",  2_200_000, 178, 15),
    ("AWA_Routing_Configuration_Guide.docx",             "docx",  420_000,   38, 12),
    ("PCSO_Design_and_Operating_Model.pdf",              "pdf",  1_100_000,  89,  8),
]


def seed_documents(cursor, user_id):
    for filename, ftype, size, chunks, days_ago in DOCUMENTS:
        cursor.execute(
            """
            INSERT INTO user_documents
                (user_id, filename, file_path, file_type, file_size, uploaded_at, chunk_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, filename, f"uploads/{user_id}/{filename}",
             ftype, size, ago(days=days_ago), chunks),
        )
    print(f"  {len(DOCUMENTS)} knowledge base documents")


CACHE_ENTRIES = [
    ("What is the correct schedule source configuration for contract-based SLAs in CSM?",
     "Set the SLA Definition's Schedule Source field to dot-walk through the case's contract "
     "(e.g. 'contract.schedule'). This resolves the schedule from contract_rel_contract_sla "
     "at runtime, allowing one SLA definition to honour different business hours per customer "
     "without creating per-account SLA definition records."),
    ("How does AWA handle agents with insufficient skills?",
     "AWA holds work items in queue rather than assigning to under-skilled agents when "
     "Enforce Skill Matching is true on the queue. Items age silently with eligible_agents=0. "
     "Audit with sys_user_has_skill query against cmn_skill sys_ids in awa_assignment_criteria."),
    ("What changed in Now Assist CSM deflection between Xanadu and Yokohama?",
     "Xanadu: AI Search surfaces KB links pre-submission. Yokohama: AI Agents deliver "
     "generative answers inline as customers type in the case form (at-submission deflection). "
     "Email-to-Case becomes Email-to-Interaction in Yokohama — adjust PA deflection formula."),
]


def seed_cache(cursor, user_id):
    expires = (datetime.now() + timedelta(days=7)).isoformat()
    for query_text, response_text in CACHE_ENTRIES:
        cursor.execute(
            """
            INSERT INTO semantic_cache
                (user_id, query_text, response_text, model_name, temperature, hit_count, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, query_text, response_text, "claude-sonnet-4-6", 0.1, 4, expires),
        )
    print(f"  {len(CACHE_ENTRIES)} semantic cache entries")


USER_CONFIGS = [
    ("preferences",    "theme",               "dark"),
    ("preferences",    "language",            "en"),
    ("features",       "multi_agent_enabled", True),
    ("model_settings", "temperature",         0.2),
]


def seed_config(cursor, user_id):
    for config_type, config_key, value in USER_CONFIGS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO user_configs (user_id, config_type, config_key, config_value)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, config_type, config_key, json.dumps(value)),
        )
    print(f"  {len(USER_CONFIGS)} user config entries")


def main():
    parser = argparse.ArgumentParser(description="Seed demo data for SN Consultant")
    parser.add_argument("--reset", action="store_true",
                        help="Delete existing demo user and re-create from scratch")
    args = parser.parse_args()

    print("\nSN Consultant — Demo Data Seed (CSM Edition)")
    print("=" * 55)

    init_database()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if args.reset:
            print("\n[0] Resetting existing demo user...")
            delete_demo_user(cursor)

        print("\n[1/6] Creating demo user...")
        user_id = create_demo_user(cursor)

        print("\n[2/6] Seeding conversations & messages...")
        seed_conversations(cursor, user_id)

        print("\n[3/6] Seeding session analytics...")
        seed_sessions(cursor, user_id)

        print("\n[4/6] Seeding learned preferences...")
        seed_preferences(cursor, user_id)

        print("\n[5/6] Seeding knowledge base documents...")
        seed_documents(cursor, user_id)

        print("\n[6/6] Seeding cache & config...")
        seed_cache(cursor, user_id)
        seed_config(cursor, user_id)

    print("\n" + "=" * 55)
    print("Demo data created.\n")
    print(f"  Username : {DEMO_USERNAME}")
    print(f"  Password : {DEMO_PASSWORD}")
    print()
    print("Conversation guide:")
    print("  [1] Platinum SLA Breach          Consultant -> Architect -> Implementation")
    print("       (open this one for the full 3-agent handoff demo)")
    print("  [2] Salesforce-ServiceNow Sync   Consultant -> Architect handoff")
    print("  [3] AWA Skill Routing Failure     Consultant only + cached response")
    print("  [4] PCSO Alert Storm              Consultant -> Architect handoff")
    print("  [5] Now Assist Deflection Rate    Consultant only + cached response")
    print()


if __name__ == "__main__":
    main()
