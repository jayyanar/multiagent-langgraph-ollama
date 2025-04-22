| S.No | Questionnaires | Validation | SOP (When to say Yes/No with Data Source Tags) |
|------|----------------|------------|------------------------------------------------|
| 1    | Q1: Did the customer indicate they no longer wish to be charged by the merchant? | Yes | ✅ Say "Yes" if a documented request exists in Claim2 or Call Notes.📌 Data Sources: Claim2, CRM Logs, Dispute Narrative |
|      |                | No         | ❌ Say "No" if no customer intent found in Claim2 or CRM logs.📌 Data Sources: CRM Logs, Call Recordings, Email Logs |
| 2    | Q2: Is the transaction stop payment eligible? | Yes | ✅ Say "Yes" if transaction type is recurring/ACH and within policy scope (e.g., Reg E).📌 Data Sources: Mainframe, VSPS, Claim2 |
|      |                | No         | ❌ Say "No" if transaction is one-time or falls outside stop payment policy.📌 Data Sources: VSPS, Mainframe, Policy Lookup |
| 3    | Q3: Was the correct form of stop payment placed on the account? | Yes | ✅ Say "Yes" if system logs confirm correct placement (e.g., recurring ACH vs. one-time card stop).📌 Data Sources: VSPS, Stop Payment Logs, Mainframe |
|      |                | No         | ❌ Say "No" if incorrect code/type was selected or misclassified.📌 Data Sources: VSPS, Placement Audit Logs, Mainframe |
| 4    | Q4: Have any new charges posted from this merchant since the notification date that were not added to the claim? | Yes | ✅ Say "Yes" if new transactions from the same merchant post-date customer notification and are missing from the claim.📌 Data Sources: Mainframe, Claim2, VSPS |
|      |                | No         | ❌ Say "No" if no new charges exist, or all new charges are included in the claim.📌 Data Sources: Mainframe, VSPS, Case Audit Logs |
| 5    | Q5: Was a Non-Target Error Discovered? | Yes | ✅ Say "Yes" if the claim was misclassified or system logic caused incorrect routing.📌 Data Sources: Case Routing Logs, QA Exception Logs, Claim2 |
|      |                | No         | ❌ Say "No" if the case was processed correctly and no logic, system, or routing issues were found.📌 Data Sources: System Processing Logs, Claim2, Decision Engine |
