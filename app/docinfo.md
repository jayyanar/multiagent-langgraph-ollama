![workflow](https://github.com/user-attachments/assets/65af9ad9-de4a-44da-b868-67da832c6637)![workflow](https://github.com/user-attachments/assets/123f64c5-58c3-4ee9-91ca-9f4ee4418a5a)![ChatGPT Image Apr 17, 2025, 06_10_00 PM](https://github.com/user-attachments/assets/8f784e44-608b-4c9f-86f4-ce0ebb944bdf)# 🔄 LangGraph-Based Agentic Workflow: PDF Data Reconciliation with Siebel System

## 🎯 Objective
Automate the reconciliation of structured data in Siebel against fields extracted from PDF documents using a multi-agent system powered by **Gemini Pro** and **Document AI**.


---

## 🔹 Agent 1: Document Classifier Agent (LLM – Gemini Pro)

**Purpose:** Automatically determine the document type (e.g., invoice, agreement, claim, etc.) based on uploaded PDF content.  
**Input:** Raw PDF document  
**Output:** Document type label (used to trigger relevant processing flow)

---

## 🔹 Agent 2: Document Extraction Agent (Google Document AI)

**Purpose:** Extract structured fields and values from the classified PDF document using OCR and pre-trained models.  
**Input:** PDF document  
**Output:** JSON object with extracted fields, values, and confidence scores

---

## 🔹 Agent 3: Siebel Data Enrichment Agent (LLM – Gemini Pro)

**Purpose:**  
- Retrieve expected column definitions from Siebel APIs  
- Enrich this data with human-readable field descriptions, business rules, and data types using Gemini Pro  

**Input:** Siebel schema metadata or API response  
**Output:** Enriched schema with field descriptions and validations

---

## 🔹 Agent 4: Data Comparison & Validation Agent (LLM – Gemini Pro)

**Purpose:**  
- Compare extracted document data with the enriched Siebel data  
- Validate field-level matches, mismatches, missing fields, and type conflicts  
- Highlight discrepancies and annotate issues with reasoning  

**Input:**  
- Extracted document data (from Document AI)  
- Enriched Siebel schema (from Agent 3)  

**Output:** Tabular comparison with match status, reason for mismatch, and confidence levels

---

## 🔹 Agent 5: Output Generation Agent (LLM – Gemini Pro)

**Purpose:**  
- Generate a structured, explainable reconciliation report  
- Export in formats such as JSON, CSV, or Markdown  
- *(Optional)* Provide natural language summary of findings  

**Input:** Validated comparison result  
**Output:**  
- JSON report for API integration  
- Human-readable table for user UI  
- Summary paragraph for audit log or compliance report

---

## 🔧 Key Features of the Workflow

| **Component**             | **Technology Used**         | **Role**                                            |
|---------------------------|------------------------------|-----------------------------------------------------|
| **LLM Engine**            | Gemini Pro                   | All reasoning, classification, validation agents    |
| **Document Parser**       | Google Document AI           | Structured field extraction from PDFs               |
| **Orchestration Engine**  | LangGraph                    | Defines agent routing, state transitions            |
| **Reconciliation Report** | Gemini Pro + JSON Formatter  | Structured + explainable result output              |
