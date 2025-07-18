# Minutes of Meeting (MoM)

**Meeting Title:** Document Translation Use Case Discussion  
**Date:** [Insert Date of Meeting]  
**Attendees:**  
- DTI – Translation Team  
- EDIP Team  
- [Add other attendees if applicable]

---

## 1. Use Case Overview

- Focus: **Inbound document translation** only (No outbound use case).
- DTI will provide a **Document Translation API**.
- EDIP will send **documents as Bytestream** for translation.
- Translated document and metadata will be returned in **Bytestream format**.
- **Kafka** will be used as the messaging queue for event handling.

---

## 2. Key Timelines

| Milestone             | Target Date                  | Status  |
|-----------------------|------------------------------|---------|
| Dev Readiness         | **July 27th, 2025**          | Planned |
| UAT Start             | **August 15th, 2025 (Tentative)** | Planned |
| Production Go-Live    | **October 15th, 2025 (Tentative)** | Planned |

---

## 3. UAT Flow and Components

- **UAT Environment Flow:**
  1. **Input:**
     - Non-English PDF document from S3.
     - Grounded (golden) data manually created and stored in S3.
  2. **API Call:**
     - EDIP invokes DTI Translation API with Bytestream document.
  3. **Output:**
     - Translated English document (Bytestream) + Metadata via Kafka.
  4. **Display Format:**
     - Original Document (Other Language)  
     - Translated Document (via DTI)  
     - Grounded Data (Manual)

---

## 4. Technical Requirements

- **Watermark** on top of each translated page: `"Translated by AI"`.
- **Expected Document Size:** 3–5 pages average.
- **Expected Processing Time:** 2–3 minutes per document.

---

## 5. Action Items & Next Steps

| Action Item                                                                 | Owner      | Due Date | Notes                         |
|------------------------------------------------------------------------------|------------|----------|-------------------------------|
| Internal testing with Dev Translation API                                   | EDIP Team  | TBD      | Notify DTI post-testing       |
| Schedule call with Ramesh (Business) to gather document types & volume      | EDIP       | ASAP     | Required for scoping          |
| Share feedback and finalize API/interface for UAT                           | EDIP & DTI | Post Dev | After internal testing        |
| Confirm production readiness and expected volume handling                   | Joint      | Before Oct | For Go-Live planning          |

---

**Note:** This use case strictly covers **inbound translation only**.

