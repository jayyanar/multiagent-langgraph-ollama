# Feature Requirement BDD Document

## Feature: Document Reconciliation via Streamlit UI

### Narrative
As a business user,  
I want to upload two documents (structured datasets or invoice PDF and Excel),  
So that I can reconcile their contents, view matches and non-matches, and analyze reasons for non-reconciliation where applicable.

---

## Use Case 1: Structured Dataset Reconciliation

### Scenario: Upload and Reconcile Two Structured Datasets
**Given** the user is on the Document Reconciliation page  
**And** there are two file upload widgets labeled "Upload Document A" and "Upload Document B"  
**When** the user uploads both Document A and Document B (structured datasets, e.g., CSV, XLSX)  
**And** clicks the "Reconcile" button  
**Then** the system should process both documents via the backend reconciliation API  
**And** display two expandable sections:  
- "Positive Matches" with a table of matched entries  
- "Non-Reconciled Entries" with a table of unmatched entries  
**And** show a notification of reconciliation completion

### Scenario: Analyze Reasons for Non-Reconciled Entries
**Given** the user has performed reconciliation and there are non-reconciled entries  
**When** the user clicks the "Reason for Non Reconcile" button  
**Then** the system should send the non-reconciled data to the LLM (Gemini Pro) backend  
**And** display the reasons for non-reconciliation in the UI  
**And** provide an option to download the results as a CSV file

---

## Use Case 2: Invoice PDF vs Excel Comparison

### Scenario: Upload and Reconcile Invoice PDF and Excel Sheet
**Given** the user is on the Document Reconciliation page  
**And** there are two file upload widgets labeled "Upload Invoice PDF" and "Upload Excel Sheet"  
**When** the user uploads an invoice PDF and an Excel sheet  
**And** clicks the "Reconcile" button  
**Then** the system should extract data from the PDF using Agentic AI Document Extraction  
**And** compare the extracted data with the Excel sheet  
**And** display two expandable sections:  
- "Positive Matches" with a table of matched entries  
- "Non-Reconciled Entries" with a table of unmatched entries  
**And** show a notification of reconciliation completion

### Scenario: Reason for Non Reconcile Button Disabled for PDF
**Given** the reconciliation is performed with a PDF as one of the sources  
**Then** the "Reason for Non Reconcile" button should be visible but disabled (greyed out) in the "Non-Reconciled Entries" section

---

## Non-Functional Requirements

- The UI must be responsive and accessible, following Streamlit best practices.
- Processing states (spinners, progress bars) and notifications (success, error) must be displayed appropriately.
- All data tables should support export functionality (CSV).
- The system must handle large files gracefully and provide clear error messages if processing fails.

---

## Glossary

- **Reconcile:** The process of comparing two datasets to identify matches and mismatches.
- **Positive Match:** Entries present in both documents with matching criteria.
- **Non-Reconciled Entry:** Entries that do not have a corresponding match in the other document.
- **LLM:** Large Language Model (e.g., Gemini Pro) used for generating explanations.
