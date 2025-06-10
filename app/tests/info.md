# Enterprise Document Intelligence Platform (EDIP)

*A unified, agentic pipeline for extraction, translation, validation, and next-best-action on enterprise documents, backed by MongoDB and exposed through typed transaction handles (`edip_transaction_id`).*

---

## 1 · Goals & Scope

| Goal | Rationale |
|------|-----------|
| **Business-Aware Parsing** | Apply domain rules per document type to yield strongly-typed objects (Invoices, Policies, Legal Agreements …). |
| **Enrichment & NBA** | Run optional **translation**, **calculations**, and **validations** (e.g., tax lookup, ERP cross-check); write the result back. |
| **Single Source of Truth** | Persist every step as an immutable document keyed by **`edip_transaction_id`** in MongoDB. |
| **Easy Consumption** | REST + **Chat-over-Mongo** layer so users and downstream systems fetch by `edip_transaction_id` or natural language. |
| **Enterprise-grade** | Security (Enterprise SSO, RBAC), observability, audit, OpenShift deployment. |

---

## 2 · Capability Map

| Layer | Core Features |
|-------|---------------|

| **Agentic Extraction** | Gemini-Pro prompt chain → chunks + groundings. |
| **Business Parsing** | YAML/JSON logic or Python plug-ins to map chunks into domain objects. |
| **Enrichment** | ⇢ **Translation** (Gemini) <br>⇢ **Calculation** (rates, totals, SPI formulas) <br>⇢ **Validation** (call AIMS APIs, ECMP engine). |
| **Persistence** | Collections: `raw_docs`, `parsed_*`, `validated_*`; every write tagged with `edip_transaction_id`. |
| **API / SDK** | `/parse`, `/result/{edip_transaction_id}`, `/chat` (RAG over Mongo). |

---

## 3 · High-Level Architecture

```mermaid
flowchart LR
    subgraph Frontend
        FE[React SPA] -->|Upload & Query| APIGW(API Gateway)
    end

    subgraph Ingestion
        APIGW --> UP[upload-svc<br/>(Node)]
        UP --> Q[(Redis / AMQP Queue)]
    end

    subgraph Orchestrator["LangGraph / Google-ADK"]
        Q --> Flow[EDIP Flow-Runner]
        Flow --> GEM[Gemini Pro]
        Flow --> Rule[Parsing & Validation Plug-ins]
    end

    Flow --> MDB[(MongoDB)]
    MDB -->|Change Stream| NBAPod[Next-Best-Action Workers]
    MDB --> ChatSvc[Chat-svc (LLM RAG)]
    APIGW --> ReadAPI[read-svc<br/>(SpringBoot)]
    ReadAPI --> MDB
    FE --> ChatSvc

    classDef box fill:#f5f7ff,stroke:#5189ff,stroke-width:2px,color:#000;
    class FE,APIGW,UP,Q,Flow,GEM,Rule,MDB,ReadAPI,ChatSvc,NBAPod box
```

---

## 4 · Component View

| Component | Technology | Key Responsibilities |
|-----------|------------|----------------------|
| **React SPA** | React 18, Vite, Tailwind | Upload UI, status polling, PDF canvas, chat widget. |
| **EDIP Flow-Runner** | LangGraph / Google-ADK | Executes *Ingest → Extract → Parse → Enrich → Persist* agents with retries & back-off. |
| **Gemini Pro** | Google Vertex | Zero-shot extraction, translation, reasoning. |
| **Parsing Plug-ins** | Python (pydantic) | User-defined rules & YAML schemas; output domain DTOs. |
| **read-svc** | Spring Boot 3 | REST + GraphQL; read-only access by `edip_transaction_id`, filters. |
| **chat-svc** | LangChain-Java / FastAPI | Embeds chunks (text + vectors), answers ad-hoc questions, returns grounded references. |
| **MongoDB Atlas / Enterprise** | WiredTiger | Stores all artifacts; Atlas Search + Vector Search (or local Enterprise Ops Manager). |
| **OpenShift Ops** | Helm + ArgoCD | Container builds, GPU node-pool, HPA, Istio mTLS. |

... (document trimmed here for brevity) ...
