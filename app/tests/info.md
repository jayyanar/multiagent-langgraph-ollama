# Data Aggregation Agent

| Data Source Type             | Integration Complexity | LLM Required (Data Agent) | Rationale                                                                 |
|-----------------------------|------------------------|----------------------------|---------------------------------------------------------------------------|
| API (via APIGEE)            | Small (S)              | ❌ Not Required             | Structured access through standardized APIs; minimal transformation needed|
| RDBMS with Defined Schema   | Medium (M)             | ❌ Not Required             | Tabular, structured data; well-understood schema enables direct extraction|
| NoSQL                       | Medium (M)             | ❌ Not Required             | Requires schema alignment but manageable through structured config        |
| SharePoint                  | Medium (M)             | ❌ Not Required             | File-based documents with metadata; limited parsing needed                |
| RDBMS with Defined Schema   | Medium (M)             | ✅ Required                 | Tabular, structured data; schema is known, but LLM needed for semantic extraction|
| Email                       | Medium (M)             | ✅ Required                 | Semi-structured body content; requires LLM to extract key insights        |
| ICMP (Document-based)       | Low (L)                | ✅ Required                 | Unstructured documents; needs intelligent parsing and classification      |
| Mainframe                   | Extra Large (XL)       | ✅ Required                 | Legacy formats and nested structures require LLM-powered data interpretation|
| MCP System                  | Medium (M)             | ✅ Required                 | Complex system-generated files; schema may vary between cycles            |
| JIRA                        | Medium (M)             | ✅ Required                 | Requires context understanding of ticket states, fields, and embedded content|


# Answering and Reasoning Agent

| Interaction Pattern                                             | Complexity Level |
|----------------------------------------------------------------|------------------|
| Fewer than 10 queries, no advanced reasoning required           | Medium (M)       |
| More than 10 queries, no reasoning required                     | Low (L)          |
| Fewer than 10 queries, reasoning and contextual explanation required | Low (L)      |
| More than 10 queries with reasoning and interpretation required | Extra Large (XL) |
