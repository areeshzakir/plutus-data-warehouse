# Plutus Data Pipeline: PRD for Simple, Reliable Marketing & Sales Analytics

### TL;DR

Plutus Data Pipeline empowers a single analyst with a unified, script-driven or minimal GUI environment to reliably ingest, clean, and prepare marketing and sales funnel data. Emphasizing simplicity, dependability, and high data quality, it minimizes manual effort while maximizing trust in outputs. No frills, no multi-user complexity—just a robust foundation for daily analysis.

---

## Goals

### Core Objectives

* **Centralize all key marketing and sales data sources** into a unified database within 8 weeks.

* **Cut manual data prep time by at least 70%** for the analyst performing recurring reports.

* **Deliver consistent, accurate, and up-to-date datasets** with daily error logs and reliable, user-triggered executions.

* **Enable ad hoc querying and export to CSV** for flexible, self-directed analysis.

* **Maintain data accuracy and reliability** as the highest priorities.

### Non-Goals

* No enterprise authentication (no SSO, no user provisioning).

* No advanced API connections, enrichment services, or external ad networks.

* No company-wide dashboards, metrics, or end-user analytics.

* No onboarding flows, videos, or managed documentation portals.

* No automated scheduling or real-time alerting—pipeline runs are always triggered by the analyst.

* No collaborative features or audit trails for multiple users.

---

## User Stories

### Target Persona: Single Analyst

* As the sole data analyst, I need to ingest all relevant marketing and sales data into one schema so I can perform my analytics work without piecing together disparate sources.

* As an analyst, I want practical, concise documentation for setup and routine maintenance so I can troubleshoot or update flows independently.

* As an analyst, I want plug-and-play API integrations where I provide an API key and endpoint URL, minimizing configuration time.

* As an analyst, I want scripts or a simple interface I can use manually to refresh data, review errors, and rerun failed steps as needed.

* As an analyst, I need logging that clearly reports errors from the previous run in a simple file for review, so I catch and resolve issues before analysis.

* As an analyst, I want an easy way to upload files for non-API sources, check process status, view and download logs, and update API URLs/configs if necessary, with minimal steps.

---

## Functional Requirements

### Ingestion

* **Support for API-driven ingestion:** Provide fields to enter API keys and endpoint URLs.

* **Manual file upload:** Allow uploading of files (e.g., CSV/XLSX/Google Sheets manual downloads) via both CLI and simple GUI.

* **Source configuration:** Allow editing of API URLs and credentials from within the GUI, as well as through a config file.

### Transformation & Deduplication

* All data ingestion steps apply cleaning and deduplication logic as specified by the analyst.

* Logic is transparent and user-editable through configuration.

### Schema Enforcement

* Data is normalized into a unified, analyst-defined schema.

* Schema configuration is accessible in setup documentation and editable as needed.

### Error Handling

* **Daily error logs:** All job runs generate a timestamped error log file.

* **Error log viewing and download:** Analyst can inspect logs in-app (simple text view) and download files.

* **Clear feedback:** Both CLI and GUI provide clear indications of process outcomes or errors.

### Export

* Datasets can be exported as CSV files from both CLI and GUI.

* Output files are placed in a dedicated directory and are available for immediate download from the GUI.

### Operator Interfaces

---

## User Experience

### Entry & Setup

* All operation is available via a command-line and a minimal, pragmatic GUI—choose whichever suits the analyst’s workflow.

* **One-time setup:** Configure database credentials, source API keys/URLs, and schema definition via CLI or GUI.

* Documentation is provided as a markdown file, including setup steps, troubleshooting tips, and usage examples.

* Running the pipeline is as easy as:

  * Executing a script (e.g., `python run_pipeline.py`) via CLI; or

  * Clicking a “Run Pipeline” button in the GUI.

* Output logs and CSV exports are placed in a dedicated directory and are available in the GUI for direct download.

### Operating Flows

Common Flow (CLI or GUI)

1. **Trigger Data Pipeline**

  * Analyst starts the ETL pipeline using the script or GUI button.

2. **View Process Status**

  * CLI prints clear status and error summaries; GUI presents real-time, simple process statuses (running/success/error).

3. **Review Error Log**

  * Analyst checks daily error log—via file (CLI) or inline in GUI—and can download the file.

4. **Correct Issues**

  * If errors occur, analyst inspects logs, adjusts configs (edit files or via minimal config editor in GUI), and reruns as needed.

5. **Manual File Upload**

  * For sources like Google Sheets, analyst uploads files directly in the app or passes files via CLI flag.

6. **Export for Analysis**

  * CSV export available from both interfaces, with recent exports downloadable from the GUI.

Scheduling

* No automated job scheduling; analyst triggers all runs manually via their preferred interface.

* Cron/task scheduling is optional and out of scope for the base product.

UI Design Principles

* Interface is strictly single-user, ultra-simple, and focused on just the core data pipeline operations.

* No dashboards, reporting, or analytics; no advanced filters or visualizations.

* Minimal config editing only for essential ETL parameters (API URLs, keys, schema files).

* No extra onboarding or multi-user features.

---

## Narrative

Before adopting the Plutus Data Pipeline, the analyst managed campaign and sales data from multiple platforms using manual downloads and messy spreadsheet merges. Errors often crept in during cut-and-paste operations, and inconsistent data formats made month-end reporting an ordeal.

After switching to this simple, low-friction pipeline—with both script and GUI trigger options—data from all relevant platforms lands in a single, reliable database, cleaned and deduped per the analyst’s chosen logic. The analyst can now spend minimal time on prep, relying on clear logs for troubleshooting, and confidently moves straight to analysis—knowing the underlying data is trustworthy. The pipeline is easy to understand, inspect, and adapt as needed—no layers of enterprise complexity or tool sprawl.

---

## Milestones & Sequencing

**Team Requirement:** One data engineer/analyst for setup, with analyst as ongoing operator.

---

**End of Document**