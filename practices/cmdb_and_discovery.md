# ServiceNow CMDB and Discovery Best Practices

---

## CI Class Hierarchy — Always Extend cmdb_ci

### Recommended
All custom CI types must extend an existing class in the `cmdb_ci` hierarchy — never create a standalone table for CIs. Choose the most specific applicable parent class: servers extend `cmdb_ci_server`, applications extend `cmdb_ci_appl`, network devices extend `cmdb_ci_netgear`. If no suitable class exists, extend `cmdb_ci_hardware` for physical items or `cmdb_ci_service` for services. Define class-specific attributes only at the level where they are first applicable. Register the new class in the **CI Class Manager** (navigated at **Configuration > CI Class Manager**) to ensure Discovery, IRE, and CSDM tools recognise it.

### Avoid
Do not create custom tables that are not in the `cmdb_ci` hierarchy to store infrastructure data — they will be invisible to CMDB Health, IRE, Discovery, and all CSDM-based service mapping. Do not add columns directly to `cmdb_ci` itself — this pollutes the base class and can cause upgrade conflicts. Do not create duplicate classes (e.g., a custom `u_server` table alongside `cmdb_ci_server`) — reconciliation between them is impossible without custom ETL.

### Why it matters
Tools like CMDB Health, Service Graph Connectors, and Impact Analysis rely entirely on class inheritance from `cmdb_ci`. A CI class outside this hierarchy is effectively invisible to automated tooling and cannot participate in dependency mapping or service health calculations.

### Source
ServiceNow Product Documentation — CI Class Manager; ServiceNow CMDB Data Model Reference (Washington DC); CSDM documentation v3.0

---

## CMDB Identification and Reconciliation Engine (IRE)

### Recommended
Use the **Identification and Reconciliation Engine (IRE)** for all programmatic CI creation and update — call `IdentificationEngineScriptableApi` (scoped) or `CIIdentifier` from server-side scripts and Import Set Transform Maps. Define **Identification Rules** (`cmdb_identifier_entry`) per CI class that specify the unique lookup keys (e.g., `serial_number` + `manufacturer` for servers, `ip_address` + `fqdn` for network devices). Define **Reconciliation Rules** (`cmdb_reconciliation_rule`) to control which data source wins when multiple sources report the same CI attribute. Mark high-trust sources (Discovery, SCCM) with a higher precedence than low-trust sources (manual import).

### Avoid
Do not insert or update CI records by calling `GlideRecord.insert()` or `GlideRecord.update()` directly on CMDB tables — this bypasses IRE, creates duplicate CIs, and corrupts reconciliation metadata. Do not rely solely on `name` as the identification key — names are not guaranteed unique across environments. Avoid creating Identification Rules that use only the `name` field; always combine with a hardware identifier or network address.

### Why it matters
Direct GlideRecord inserts on CMDB tables are the single largest cause of duplicate CIs in production instances. Once duplicates exist, downstream Impact Analysis, Service Mapping, and CSDM service models produce incorrect data that cannot be trusted without remediation.

### Source
ServiceNow Product Documentation — Identification and Reconciliation Engine (IRE); ServiceNow CMDB Data Management Guide; Knowledge (Knowledge21) session "IRE Deep Dive"

---

## Discovery Configuration and Scheduling

### Recommended
Organise Discovery schedules by network segment using **IP Networks** (`discovery_ip_network`) — assign each network to a MID Server with line-of-sight access. Use **Quick Discovery** for on-demand single-device scans during testing. Set the **Discover** field on CI records to "Rediscover" (not "Always") to prevent overwriting manually curated fields. Configure **Discovery Exclusions** to skip known scanning dead zones (printers, IoT devices not in scope). Use **Horizontal Discovery** for infrastructure and **Top-Down Service Mapping** for application-layer dependencies. Review **Discovery Log** (`discovery_log`) daily for credential failures and probe timeouts.

### Avoid
Do not run Discovery against the entire network on a single broad schedule — this creates discovery storms and MID Server saturation. Do not disable the **Discovery Status** dashboard record — it is the only audit trail for what was discovered and when. Avoid overlapping Discovery schedules on the same IP range with different MID Servers — this causes race conditions in IRE and produces phantom CI duplicates.

### Why it matters
Discovery storms cause MID Server queue backlogs that can take hours to clear, delaying CMDB updates across the entire environment. Overlapping schedules are a documented cause of duplicate CI creation even when IRE is correctly configured.

### Source
ServiceNow Product Documentation — Discovery Administration; MID Server Best Practices guide; ServiceNow Success Playbook: CMDB and Discovery

---

## MID Server Best Practices

### Recommended
Deploy MID Servers on dedicated Windows Server or Linux hosts — never on application servers, domain controllers, or database servers. Size MID Servers according to the **MID Server Sizing Guide**: minimum 8 CPU cores and 16 GB RAM for medium Discovery workloads. Join each MID Server to the domain it will scan to enable Windows WMI credential pass-through. Use **MID Server Clusters** for high-availability — configure a minimum of two MID Servers per cluster with automatic failover. Pin specific probes to specific MID Servers using **MID Server Capabilities** to ensure the right MID Server handles each protocol (WMI, SNMP, SSH). Upgrade MID Servers immediately after each instance upgrade — mixed-version MID Servers cause probe failures.

### Avoid
Do not run MID Server software on the same host as the ServiceNow instance or any production application. Do not use a single MID Server for both Discovery and IntegrationHub/spoke execution in production — separate concerns to prevent resource contention. Avoid running MID Servers with domain admin credentials — use a dedicated service account with the minimum permissions defined in the MID Server credential requirements documentation.

### Why it matters
An overloaded or misconfigured MID Server silently drops discovery probes without surfacing errors in the UI, leading to stale CMDB data. Over-privileged MID Server credentials are a significant security attack surface — a compromised MID Server with domain admin access can pivot across the entire network.

### Source
ServiceNow Product Documentation — MID Server Installation and Configuration; MID Server Sizing Guide (KB0747227); ServiceNow Security Best Practices for MID Servers

---

## Duplicate CI Prevention

### Recommended
Run the **CMDB Deduplication** task (`cmdb_deduplication_task`) regularly — schedule it monthly. Use **CMDB Health** (navigated at **Configuration > CMDB Health**) to monitor the Duplicate CIs KPI and set an alert threshold. Configure IRE Identification Rules with the strongest possible key set (prefer hardware serial numbers over names). For import-based data sources, validate CI identity lookups in the Transform Map's `onBefore` script using `IdentificationEngineScriptableApi.identifyCI()` before inserting. Maintain a **Master Data Source** designation in Reconciliation Rules so there is always a single source of truth for `name` and `serial_number`.

### Avoid
Do not merge duplicate CIs manually by deleting one record — use the **CI Relationship Builder** merge function or the CMDB Deduplication utility to preserve all relationship data. Do not run deduplication against `cmdb_ci` without filtering to a specific CI class — global deduplication can incorrectly merge CIs from different classes that share a name. Avoid populating the `correlation_id` field inconsistently — it is used by IRE as an alternate identity key.

### Why it matters
Each duplicate CI creates phantom relationships in service maps, inflates hardware asset counts, and generates incorrect compliance and cost reports. Deleting a duplicate CI without merging its relationships breaks all open incidents, changes, and problems that referenced it.

### Source
ServiceNow Product Documentation — CMDB Deduplication; IRE Identification Rules; ServiceNow CMDB Health documentation

---

## CMDB Health and Governance

### Recommended
Configure **CMDB Health** dashboards to track the four key dimensions: Completeness, Compliance, Correctness, and Staleness. Set **Staleness Rules** per CI class (e.g., servers stale after 30 days without a Discovery update, laptops after 14 days). Create a **CMDB Governance** process: assign a CMDB Manager role, schedule quarterly CI class audits, and set up automated reports for classes with health scores below 80%. Use **Instance Scan** checks (navigated at **System Diagnostics > Instance Scan**) for CMDB-specific hygiene checks. Enable the **CMDB 360 View** on CI records so stakeholders can see all active relationships and health indicators.

### Avoid
Do not treat CMDB Health scores as advisory — failing scores must trigger a remediation task in the Problem or Improvement process. Do not disable Staleness Rules to hide data quality issues — stale CIs must be remediated or explicitly retired. Avoid creating CI records manually in bulk without IRE — it circumvents all identification and reconciliation logic.

### Why it matters
An unhealthy CMDB produces incorrect impact analysis during major incidents and false positives in compliance reports. Stale CI data causes service maps to show infrastructure that was decommissioned months or years ago, misleading architects and operations teams.

### Source
ServiceNow Product Documentation — CMDB Health (Washington DC); ServiceNow CMDB KPIs and Dashboards

---

## CSDM — Common Service Data Model

### Recommended
Align your CMDB implementation to the **CSDM v3.0** (or current) framework layers: Technology, Application Service, Business Service, and Business Capability. Use `cmdb_ci_service` for modelling Business Services and `cmdb_ci_appl` for Technical Services. Populate the **Managed By Group** and **Owned By** fields on all service CIs — they drive notification routing and ownership reports. Use **Service Graph Connectors** (SGC) from the ServiceNow Store to ingest third-party data in a CSDM-compliant way, rather than writing custom integrations that bypass the model. Define **Service Offerings** (`service_offering`) under Business Services to connect ITSM processes to business context.

### Avoid
Do not skip the CSDM layer alignment because it seems complex — implementing ITSM, ITOM, or SPM without CSDM means each product builds its own service model independently, creating inconsistency. Do not model every application as a Business Service — distinguish between Technical Services (IT-facing) and Business Services (business-outcome-facing). Avoid adding custom fields directly to CSDM-mapped tables without checking the CSDM upgrade guide — some fields are reserved for future CSDM versions.

### Why it matters
Without CSDM alignment, ServiceNow products like ITOM Visibility, ITSM Impact Analysis, and SPM cannot communicate through a shared service model — each sees a different picture of the organisation, and cross-product automation is unreliable.

### Source
ServiceNow CSDM Documentation v3.0; ServiceNow Knowledge (Knowledge22) session "CSDM in Practice — From Theory to Implementation"; ServiceNow Success Playbook: CSDM

---

## Import Sets and Transform Maps for CMDB Population

### Recommended
Use **Import Sets** (`sys_import_set`) combined with **Transform Maps** (`sys_transform_map`) as the staging layer for all third-party data loading into CMDB. In the Transform Map's `coalesce` fields, specify the same keys used in your IRE Identification Rules to ensure IRE is invoked correctly. Use the **Field Map** `coalesce` checkbox on the primary identifier fields only — coalescing on too many fields causes false no-match results. In the `onBefore` Transform Script, call `IdentificationEngineScriptableApi.identifyCI()` to pre-check identity before the transform engine creates a new record. Schedule cleanup of Import Set tables using **Data Sources** with a retention policy — staging tables grow large quickly.

### Avoid
Do not use Transform Maps to write directly to CMDB tables without IRE — set the Target Table to the Import Set staging table and let IRE handle the CMDB write. Do not leave Import Set staging tables (`u_*_import`) populated indefinitely — they consume significant database space and slow list queries. Avoid creating Transform Maps that update CMDB tables field-by-field without going through the reconciliation layer — this overwrites data from higher-trust sources.

### Why it matters
Transform Maps that bypass IRE and write directly to CMDB tables are the second-most common cause of CMDB data corruption after manual inserts. Unmanaged Import Set table growth has caused tablespace exhaustion in hosted instances, triggering emergency support calls.

### Source
ServiceNow Developer Docs — Import Sets and Transform Maps; ServiceNow CMDB Data Management Guide; IRE Integration with Transform Maps (docs.servicenow.com)

---

## CI Lifecycle Management

### Recommended
Define a **CI Lifecycle** using the `install_status` field on `cmdb_ci`: Installed (1), On Order (2), In Maintenance (3), Retired (7). Automate lifecycle transitions using **Discovery** state detection (a CI not seen by Discovery for N days triggers an "Absent" state change) combined with a Business Rule that moves the CI to "Retired" after a configurable hold period. Create a **Decommission Change Request** template that includes a CI state transition task as part of the standard decommission workflow. Archive retired CIs by setting `install_status = 7` (Retired) rather than deleting them — historical incident and change relationships must be preserved.

### Avoid
Do not delete CIs from the CMDB — deletion destroys all historical relationship data and breaks audit trails on past incidents and changes. Do not leave decommissioned infrastructure CIs in "Installed" state indefinitely — they inflate active CI counts and cause incorrect impact analysis. Avoid manual lifecycle management without a formal process — CIs should only change lifecycle state via an approved workflow or Discovery automation.

### Why it matters
Deleted CIs cause `sys_id` reference corruption on `task_ci` and `cmdb_rel_ci` records — incidents and changes that referenced the deleted CI lose their CI link permanently. Stale "Installed" CIs in the CMDB have directly caused incorrect Major Incident impact calculations where decommissioned servers were shown as affected.

### Source
ServiceNow Product Documentation — CI Lifecycle and `install_status`; ServiceNow CMDB Data Model Reference; ITIL 4 — Configuration Item Lifecycle
