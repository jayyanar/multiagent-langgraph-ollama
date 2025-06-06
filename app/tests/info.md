# 🚀 Sprint 1 Goals

## 📌 TSP04 – MVP0

**Goal:**  
Build the initial document ingestion and classification pipeline forming the foundation of EDIP (Early Document Intelligence Pipeline) under MVP0.

### 🎯 Objectives

1. **UI Upload Module**
   - Implement UI to support:
     - File upload (PDF, Image)
     - File type selection: Transaction, Document, Summary
   - Store uploaded files in a temporary backend or mock storage

2. **ICMP Classification Pipeline**
   - Stubbed classification logic to categorize documents into:
     - Lease Agreement
     - Rental Agreement
     - Invoice
     - Grocery Receipt

3. **EDIP Framework Initialization**
   - Set up placeholder UI/logic for:
     - Extracted Key
     - Extracted Value
     - Verified Info
     - PDF/Video placeholder panel

4. **API/Integration Setup**
   - Prepare endpoints for:
     - File ingestion
     - Classification
     - EDIP stubs
   - Set up mock integration with Google/Azure APIs for future OCR/NLP

### ✅ Deliverables

- Functional UI for document upload
- Backend logic for mock classification
- Static EDIP display framework
- Document type tagging
---

## 🔬 Experimentation Team – Sprint 1

**Goal:**  
Develop a prototype to perform **visual grounding** (highlighting) and **layout-preserving translation** on PDFs.

### 🎯 Objectives

1. **Visual Grounding in PDFs**
   - Detect and highlight structural elements:
     - Headers, tables, form fields, checkboxes
   - Tools: PDFPlumber, PyMuPDF, pdf2image, Tesseract OCR
   - Output: PDFs with bounding boxes or overlayed highlights

2. **Layout-Preserving Translation**
   - Translate text (e.g., non-English → English) while retaining:
     - Font sizes, spatial layout, tables, paragraph formatting
   - Use APIs like:
     - Google Translate API
     - Azure Translator
   - Output options:
     - Annotated PDFs
     - JSON (bounding box + translated text)

3. **Sample Evaluations**
   - Test on 2–3 real-world PDFs
   - Visual comparison of:
     - Original PDF
     - Highlighted version
     - Translated, layout-preserved version

### ✅ Deliverables

- Highlighted PDFs with visual grounding
- Translated PDFs with layout intact
- Code scripts/notebooks for repeatability
- Sample outputs and short evaluation summary
