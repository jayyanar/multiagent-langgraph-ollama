# Design Document: SOP Validator

## Overview

The SOP Validator is a validation and refinement system that tests Standard Operating Procedures against live data from the MCP Fleet to ensure SOPs are accurate, executable, and aligned with operational reality. The system bridges the gap between documented procedures and actual data availability by generating validation queries, executing them against real data sources, identifying discrepancies, and managing iterative SOP refinement through versioning.

### Design Philosophy

The validator follows a test-driven validation approach where SOPs are treated as executable specifications that must be verified against actual system capabilities:

1. **Query Generation**: Convert SOP instructions into testable queries using prompt engineering
2. **Execution**: Run queries against live data through MCP Fleet
3. **Analysis**: Compare expected behavior (from SOP) with actual results (from data)
4. **Reporting**: Generate actionable discrepancy reports with recommendations
5. **Refinement**: Apply fixes and create new SOP versions
6. **Iteration**: Re-validate to verify improvements

### Key Design Decisions

**Prompt Engineering for Query Generation**: Rather than hardcoding query generation logic, we use configurable prompt templates that can be refined over time. This allows validation engineers to optimize query generation without code changes.

**Separation of Validation and Refinement**: Validation identifies problems, refinement fixes them. These are separate phases with clear boundaries, enabling validation to run independently and refinement to be applied selectively.

**Version-Aware Validation**: Every validation run is associated with a specific SOP version, creating a historical record of how SOP quality improves over time.

**Graceful Degradation**: When data sources are unavailable or queries fail, the validator continues with remaining validation tasks and produces partial results rather than failing completely.

**Multi-Level Discrepancy Severity**: Discrepancies are categorized (critical, warning, informational) to help prioritize fixes and distinguish between blocking issues and optimization opportunities.

## Architecture

### System Context

```
┌─────────────────────┐
│ SOP Extraction      │
│ Pipeline            │
│ (Formatted SOPs)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│              SOP Validator                              │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │Data      ├─►│Query     ├─►│Query Executor    │    │
│  │Source    │  │Generator │  │                  │    │
│  │Validator │  └──────────┘  └────────┬─────────┘    │
│  └──────────┘                          │              │
│                                        ▼              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │Decision  │  │Discrepancy│◄─┤Result Analyzer  │    │
│  │Path      │  │Reporter   │  └──────────────────┘    │
│  │Tester    │  └─────┬─────┘                          │
│  └──────────┘        │                                │
│                      ▼                                │
│  ┌──────────┐  ┌──────────────────┐                  │
│  │Version   │◄─┤SOP Refiner       │                  │
│  │Tracker   │  └──────────────────┘                  │
│  └──────────┘                                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   MCP Fleet          │
          │ (Query Interface)    │
          └──────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │Claims_  │  │Trans_   │  │  VSPS   │
   │data     │  │data     │  │         │
   └─────────┘  └─────────┘  └─────────┘
```

### Component Architecture

The validator consists of seven primary components:

**1. Data Source Validator**
- Verifies data source availability through MCP Fleet Schema_Registry
- Validates field references against actual schemas
- Checks data type compatibility
- Outputs: Data source validation report

**2. Query Generator**
- Converts SOP instructions into MCP Fleet queries
- Uses prompt engineering with configurable templates
- Supports multi-source query generation
- Outputs: Validation queries with metadata

**3. Query Executor**
- Submits queries to MCP Fleet Query_Interface
- Handles authentication and rate limiting
- Manages query timeouts and retries
- Outputs: Query results or error details

**4. Result Analyzer**
- Compares query results with SOP expectations
- Identifies discrepancies and categorizes by severity
- Analyzes query performance
- Outputs: Discrepancy list with details

**5. Decision Path Tester**
- Generates test cases for SOP decision paths
- Executes complete flows from root to terminal nodes
- Verifies all branches are reachable
- Outputs: Decision path test results

**6. Discrepancy Reporter**
- Aggregates discrepancies from all validation components
- Generates comprehensive validation reports
- Provides actionable recommendations
- Outputs: Validation_Report with quality metrics

**7. SOP Refiner**
- Applies fixes to SOPs based on validation findings
- Creates new SOP versions with change tracking
- Triggers re-validation of changed sections
- Outputs: Refined SOP versions

**8. Version Tracker**
- Manages SOP version history
- Stores validation results with each version
- Supports version comparison and rollback
- Outputs: Version metadata and diffs

### Data Flow

```
SOP (from Extraction Pipeline)
    ↓
[Data Source Validator] → Check data sources and fields
    ↓
Data Source Validation Report
    ↓
[Query Generator] → Generate validation queries from instructions
    ↓
Validation Queries
    ↓
[Query Executor] → Execute queries via MCP Fleet
    ↓
Query Results
    ↓
[Result Analyzer] → Compare results with expectations
    ↓
Discrepancies
    ↓
[Decision Path Tester] → Test complete decision flows
    ↓
Decision Path Results
    ↓
[Discrepancy Reporter] → Aggregate and report findings
    ↓
Validation Report
    ↓
[SOP Refiner] → Apply fixes (if requested)
    ↓
Refined SOP
    ↓
[Version Tracker] → Create new version with validation results
    ↓
Versioned SOP → Storage / Re-validation
```

## Components and Interfaces

### 1. Data Source Validator

**Responsibilities:**
- Extract data source references from SOPs
- Verify data source availability via MCP Fleet
- Validate field references against schemas
- Check data type compatibility

**Interface:**
```typescript
interface DataSourceValidator {
  validateDataSources(sop: EnrichedSOP): Promise<DataSourceValidationReport>;
  extractDataSourceTags(sop: EnrichedSOP): DataSourceTag[];
  checkAvailability(dataSourceTag: DataSourceTag): Promise<AvailabilityStatus>;
  validateFieldReference(fieldRef: FieldReference, schema: SchemaInfo): FieldValidationResult;
}

interface DataSourceValidationReport {
  sopId: string;
  dataSources: DataSourceStatus[];
  fieldValidations: FieldValidationResult[];
  overallStatus: 'pass' | 'fail' | 'warning';
  criticalIssues: number;
  warnings: number;
}

interface DataSourceStatus {
  dataSourceTag: DataSourceTag;
  available: boolean;
  status: 'online' | 'offline' | 'not_found';
  schemaAccessible: boolean;
  issues: string[];
}

interface FieldReference {
  dataSource: string;
  table?: string;
  field: string;
  expectedType?: string;
  location: string;  // SOP location (S.No, instruction)
}

interface FieldValidationResult {
  fieldRef: FieldReference;
  exists: boolean;
  actualType?: string;
  compatible: boolean;
  severity: 'critical' | 'warning' | 'info';
  message: string;
}
```

**Key Algorithms:**

*Data Source Tag Extraction*:
```
For each questionnaire item in SOP:
  For each instruction in item:
    Extract data source tags using pattern matching
    Normalize tag names to MCP Fleet identifiers
    Store location reference (S.No, instruction text)
Return unique list of data source tags with locations
```

*Field Reference Validation*:
```
For each field reference:
  Query MCP Fleet Schema_Registry for data source schema
  If schema not found:
    Return critical error (data source not accessible)
  Search schema for table and field
  If field not found:
    Return critical error (field does not exist)
  If field found but type mismatch:
    Return warning (type incompatibility)
  Return success
```

### 2. Query Generator

**Responsibilities:**
- Parse SOP instructions to identify data requirements
- Generate MCP Fleet queries using prompt engineering
- Support multi-source query generation
- Optimize queries for performance

**Interface:**
```typescript
interface QueryGenerator {
  generateValidationQuery(instruction: Instruction, context: QueryContext): Promise<ValidationQuery>;
  generateMultiSourceQuery(instructions: Instruction[], context: QueryContext): Promise<ValidationQuery>;
  applyPromptTemplate(template: PromptTemplate, instruction: Instruction): string;
  optimizeQuery(query: ValidationQuery): ValidationQuery;
}

interface QueryContext {
  dataSourceSchemas: Map<string, SchemaInfo>;
  availableFields: Map<string, ColumnSchema[]>;
  promptTemplates: PromptTemplate[];
}

interface ValidationQuery {
  queryId: string;
  mcpQuery: string;  // Unified query for MCP Fleet
  dataSources: string[];
  purpose: string;  // What this query validates
  expectedOutcome: ExpectedOutcome;
  metadata: QueryMetadata;
}

interface ExpectedOutcome {
  type: 'data_exists' | 'data_matches' | 'condition_met' | 'consistency_check';
  criteria: Record<string, any>;
  successCondition: string;
}

interface QueryMetadata {
  instructionLocation: string;  // S.No and instruction text
  generatedBy: string;  // Prompt template ID
  estimatedComplexity: number;
  timeout: number;
}

interface PromptTemplate {
  templateId: string;
  name: string;
  instructionPattern: string;  // Regex to match instruction types
  queryTemplate: string;  // Template with placeholders
  exampleInputs: string[];
  exampleOutputs: string[];
  performance: TemplatePerformance;
}

interface TemplatePerformance {
  successRate: number;
  avgQueryTime: number;
  usageCount: number;
}
```

**Prompt Engineering Strategy:**

The Query Generator uses a library of prompt templates that convert SOP instructions into MCP Fleet queries. Templates are structured as:

```
Template: Data Lookup Validation
Pattern: "Check {field} in {data_source} for {condition}"
Query Template:
  SELECT {field}
  FROM {data_source}.{table}
  WHERE {condition}
  LIMIT 1

Example:
  Instruction: "Check Trans_detail in Claims_data for Customer_ID = ?"
  Generated Query:
    SELECT Trans_detail
    FROM claims_data.transactions
    WHERE Customer_ID = ?
    LIMIT 1
```

**Query Generation Algorithm:**
```
1. Parse instruction text to extract:
   - Data sources referenced
   - Fields mentioned
   - Conditions or comparisons
   - Expected outcomes

2. Match instruction against prompt template patterns

3. If match found:
   - Apply template with extracted parameters
   - Validate generated query syntax
   - Add expected outcome criteria

4. If no match:
   - Use generic template
   - Flag for manual review

5. Optimize query:
   - Add appropriate indexes hints
   - Limit result set size
   - Set reasonable timeout

6. Return ValidationQuery with metadata
```

### 3. Query Executor

**Responsibilities:**
- Submit queries to MCP Fleet
- Handle authentication and authorization
- Manage rate limiting and retries
- Capture results and errors

**Interface:**
```typescript
interface QueryExecutor {
  executeQuery(query: ValidationQuery, credentials: Credentials): Promise<QueryResult>;
  executeBatch(queries: ValidationQuery[], credentials: Credentials): Promise<QueryResult[]>;
  retryWithBackoff(query: ValidationQuery, maxRetries: number): Promise<QueryResult>;
}

interface QueryResult {
  queryId: string;
  status: 'success' | 'error' | 'timeout';
  data?: Record<string, any>[];
  error?: QueryError;
  executionTime: number;
  metadata: QueryExecutionMetadata;
}

interface QueryError {
  errorType: 'auth' | 'timeout' | 'data_source_unavailable' | 'syntax' | 'unknown';
  message: string;
  dataSource?: string;
  retryable: boolean;
}

interface QueryExecutionMetadata {
  timestamp: Date;
  dataSources: string[];
  rowsReturned: number;
  cached: boolean;
  retryCount: number;
}
```

**Execution Strategy:**

*Rate Limiting*:
- Maximum 100 queries per second to MCP Fleet
- Per-data-source limits based on capacity
- Queue queries when limits reached

*Retry Logic*:
```
For transient errors (timeout, temporary unavailability):
  Retry with exponential backoff: 1s, 2s, 4s
  Maximum 3 retries
  
For auth errors:
  No retry (requires credential fix)
  
For syntax errors:
  No retry (requires query fix)
```

### 4. Result Analyzer

**Responsibilities:**
- Compare query results with expected outcomes
- Identify discrepancies
- Categorize by severity
- Analyze performance issues

**Interface:**
```typescript
interface ResultAnalyzer {
  analyzeResult(query: ValidationQuery, result: QueryResult): Discrepancy[];
  compareWithExpectation(result: QueryResult, expected: ExpectedOutcome): boolean;
  categorizeDiscrepancy(discrepancy: Discrepancy): DiscrepancySeverity;
  analyzePerformance(result: QueryResult): PerformanceIssue[];
}

interface Discrepancy {
  discrepancyId: string;
  type: DiscrepancyType;
  severity: DiscrepancySeverity;
  location: string;  // SOP location
  description: string;
  expected: string;
  actual: string;
  recommendation: string;
  queryId: string;
}

type DiscrepancyType = 
  | 'missing_data_source'
  | 'invalid_field'
  | 'data_not_found'
  | 'type_mismatch'
  | 'logic_error'
  | 'performance_issue'
  | 'access_denied'
  | 'inconsistent_data';

type DiscrepancySeverity = 'critical' | 'warning' | 'info';

interface PerformanceIssue {
  queryId: string;
  issueType: 'slow_query' | 'large_result_set' | 'timeout';
  executionTime: number;
  threshold: number;
  recommendation: string;
}
```

**Analysis Algorithm:**
```
For each query result:
  1. Check result status:
     - If error: Create discrepancy based on error type
     - If timeout: Create performance issue
     - If success: Continue to outcome validation
  
  2. Validate expected outcome:
     - data_exists: Check if rows returned > 0
     - data_matches: Check if data meets criteria
     - condition_met: Evaluate condition against results
     - consistency_check: Compare across sources
  
  3. If outcome not met:
     - Create discrepancy with details
     - Categorize severity based on impact
     - Generate recommendation
  
  4. Check performance:
     - If execution time > threshold: Create performance issue
     - If result set too large: Suggest pagination
  
  5. Return list of discrepancies and issues
```

### 5. Decision Path Tester

**Responsibilities:**
- Generate test cases for decision paths
- Execute complete flows through decision trees
- Verify all branches are reachable
- Test with various data scenarios

**Interface:**
```typescript
interface DecisionPathTester {
  generateTestCases(decisionTree: DecisionTree): TestCase[];
  executeTestCase(testCase: TestCase, sop: EnrichedSOP): Promise<TestResult>;
  testAllPaths(sop: EnrichedSOP): Promise<PathTestReport>;
  verifyBranchReachability(decisionTree: DecisionTree): ReachabilityReport;
}

interface TestCase {
  testCaseId: string;
  path: DecisionPath;
  testData: TestData;
  expectedTerminalNode: string;
}

interface DecisionPath {
  startNode: string;
  steps: PathStep[];
  terminalNode: string;
}

interface PathStep {
  nodeId: string;
  questionRef: string;  // S.No
  outcome: string;  // "Yes", "No", or choice value
  nextNode: string;
}

interface TestData {
  dataSource: string;
  records: Record<string, any>[];
  scenario: string;  // Description of test scenario
}

interface TestResult {
  testCaseId: string;
  status: 'pass' | 'fail' | 'error';
  actualPath: DecisionPath;
  discrepancies: Discrepancy[];
  executionTime: number;
}

interface PathTestReport {
  sopId: string;
  totalPaths: number;
  testedPaths: number;
  passedPaths: number;
  failedPaths: number;
  unreachableBranches: string[];
  testResults: TestResult[];
}

interface ReachabilityReport {
  totalBranches: number;
  reachableBranches: number;
  unreachableBranches: BranchInfo[];
  deadEnds: string[];  // Nodes with no terminal condition
}

interface BranchInfo {
  nodeId: string;
  questionRef: string;
  outcome: string;
  reason: string;  // Why unreachable
}
```

**Test Case Generation Algorithm:**
```
1. Traverse decision tree to identify all unique paths:
   - Start from root node
   - Follow each branch recursively
   - Record complete path to each terminal node

2. For each path:
   - Identify data requirements at each step
   - Generate test data that satisfies path conditions
   - Create TestCase with path and test data

3. Generate edge case test data:
   - Empty data sets
   - Boundary values
   - Missing fields
   - Conflicting data

4. Return comprehensive test case suite
```

**Path Execution Algorithm:**
```
For each test case:
  1. Start at root node
  2. For each step in path:
     - Execute query for current node's question
     - Evaluate validation rule with test data
     - Determine outcome (Yes/No/choice)
     - Move to next node based on outcome
  3. Verify reached terminal node matches expected
  4. If mismatch: Create discrepancy
  5. Return test result
```

### 6. Discrepancy Reporter

**Responsibilities:**
- Aggregate discrepancies from all validation components
- Generate comprehensive validation reports
- Provide actionable recommendations
- Calculate quality metrics

**Interface:**
```typescript
interface DiscrepancyReporter {
  generateReport(validationResults: ValidationResults): ValidationReport;
  aggregateDiscrepancies(discrepancies: Discrepancy[]): DiscrepancySummary;
  calculateQualityScore(validationResults: ValidationResults): QualityScore;
  generateRecommendations(discrepancies: Discrepancy[]): Recommendation[];
  exportReport(report: ValidationReport, format: 'json' | 'pdf' | 'html'): string;
}

interface ValidationResults {
  sopId: string;
  sopVersion: string;
  dataSourceReport: DataSourceValidationReport;
  queryResults: QueryResult[];
  discrepancies: Discrepancy[];
  pathTestReport: PathTestReport;
  performanceIssues: PerformanceIssue[];
  timestamp: Date;
}

interface ValidationReport {
  sopId: string;
  sopVersion: string;
  overallStatus: 'ready' | 'needs_fixes' | 'critical_issues';
  qualityScore: QualityScore;
  summary: DiscrepancySummary;
  detailedFindings: DetailedFindings;
  recommendations: Recommendation[];
  metrics: ValidationMetrics;
  timestamp: Date;
}

interface QualityScore {
  overall: number;  // 0-100
  dataSourceAvailability: number;
  fieldValidity: number;
  decisionPathCompleteness: number;
  queryPerformance: number;
}

interface DiscrepancySummary {
  totalDiscrepancies: number;
  criticalCount: number;
  warningCount: number;
  infoCount: number;
  byType: Map<DiscrepancyType, number>;
  byLocation: Map<string, number>;  // S.No → count
}

interface DetailedFindings {
  dataSourceIssues: DataSourceStatus[];
  fieldIssues: FieldValidationResult[];
  queryDiscrepancies: Discrepancy[];
  pathTestFailures: TestResult[];
  performanceIssues: PerformanceIssue[];
}

interface Recommendation {
  priority: 'high' | 'medium' | 'low';
  category: 'data_source' | 'field' | 'logic' | 'performance';
  description: string;
  affectedLocations: string[];
  suggestedFix: string;
  estimatedImpact: string;
}

interface ValidationMetrics {
  totalQueriesExecuted: number;
  avgQueryTime: number;
  dataSourcesCovered: number;
  pathsCovered: number;
  validationDuration: number;
}
```

**Quality Score Calculation:**
```
Quality Score = weighted_average([
  dataSourceAvailability,    // All sources accessible
  fieldValidity,             // All fields exist and compatible
  decisionPathCompleteness,  // All paths reachable and valid
  queryPerformance           // Queries execute efficiently
])

Weights: [0.3, 0.3, 0.3, 0.1]

Each component score:
  - 100: No issues
  - 75-99: Minor warnings
  - 50-74: Multiple warnings or some critical issues
  - 0-49: Multiple critical issues
```

### 7. SOP Refiner

**Responsibilities:**
- Apply fixes to SOPs based on validation findings
- Update data source references
- Correct field names and types
- Fix decision logic
- Create new SOP versions

**Interface:**
```typescript
interface SOPRefiner {
  refineSOP(sop: EnrichedSOP, fixes: Fix[]): Promise<EnrichedSOP>;
  applyFix(sop: EnrichedSOP, fix: Fix): EnrichedSOP;
  validateRefinement(original: EnrichedSOP, refined: EnrichedSOP): RefinementValidation;
  generateChangeDescription(fixes: Fix[]): string;
}

interface Fix {
  fixId: string;
  discrepancyId: string;
  fixType: FixType;
  location: string;  // S.No or section
  changes: Change[];
  rationale: string;
}

type FixType = 
  | 'update_data_source'
  | 'correct_field_name'
  | 'fix_decision_logic'
  | 'add_missing_instruction'
  | 'update_validation_rule';

interface Change {
  field: string;
  oldValue: any;
  newValue: any;
}

interface RefinementValidation {
  valid: boolean;
  schemaCompliant: boolean;
  preservesUnchangedSections: boolean;
  issues: string[];
}
```

**Refinement Algorithm:**
```
For each fix:
  1. Locate target section in SOP (by S.No or section ID)
  
  2. Apply changes based on fix type:
     - update_data_source: Replace data source tag
     - correct_field_name: Update field reference
     - fix_decision_logic: Modify decision tree branch
     - add_missing_instruction: Insert new instruction
     - update_validation_rule: Modify validation criteria
  
  3. Validate change:
     - Check schema compliance
     - Verify unchanged sections preserved
     - Ensure no new inconsistencies introduced
  
  4. If validation fails:
     - Rollback change
     - Report validation error
  
  5. If validation succeeds:
     - Apply change to SOP
     - Record change in metadata

6. Return refined SOP with all changes applied
```

### 8. Version Tracker

**Responsibilities:**
- Create new SOP versions after refinement
- Store validation results with versions
- Support version comparison
- Enable rollback to previous versions

**Interface:**
```typescript
interface VersionTracker {
  createVersion(sop: EnrichedSOP, validationReport: ValidationReport, changeDescription: string): Promise<SOPVersion>;
  getVersion(sopId: string, versionId: string): Promise<SOPVersion>;
  getLatestVersion(sopId: string): Promise<SOPVersion>;
  compareVersions(versionId1: string, versionId2: string): Promise<VersionComparison>;
  getVersionHistory(sopId: string): Promise<SOPVersion[]>;
}

interface SOPVersion {
  versionId: string;
  sopId: string;
  sop: EnrichedSOP;
  validationReport: ValidationReport;
  parentVersionId?: string;
  changeDescription: string;
  createdAt: Date;
  createdBy: string;
  qualityScore: number;
}

interface VersionComparison {
  version1: SOPVersion;
  version2: SOPVersion;
  diff: VersionDiff;
  qualityImprovement: number;  // Change in quality score
  discrepancyReduction: number;  // Change in discrepancy count
}

interface VersionDiff {
  changedSections: SectionChange[];
  addedItems: string[];  // S.No of new items
  removedItems: string[];  // S.No of removed items
  modifiedItems: ItemModification[];
}

interface SectionChange {
  location: string;
  changeType: 'added' | 'removed' | 'modified';
  before?: any;
  after?: any;
}

interface ItemModification {
  sNo: string;
  fieldChanges: Change[];
}
```

## Data Models

### Core Data Structures

**EnrichedSOP** (Input from SOP Extraction Pipeline)
```typescript
// Reuses data model from SOP Extraction Pipeline
interface EnrichedSOP {
  document_id: string;
  version: string;
  questionnaire_items: QuestionnaireItem[];
  decision_tree: DecisionTree;
  metadata: DocumentMetadata;
}
```

**ValidationQuery**
```typescript
interface ValidationQuery {
  queryId: string;
  mcpQuery: string;
  dataSources: string[];
  purpose: string;
  expectedOutcome: ExpectedOutcome;
  metadata: QueryMetadata;
}
```

**Discrepancy**
```typescript
interface Discrepancy {
  discrepancyId: string;
  type: DiscrepancyType;
  severity: DiscrepancySeverity;
  location: string;
  description: string;
  expected: string;
  actual: string;
  recommendation: string;
  queryId: string;
}
```

**ValidationReport**
```typescript
interface ValidationReport {
  sopId: string;
  sopVersion: string;
  overallStatus: 'ready' | 'needs_fixes' | 'critical_issues';
  qualityScore: QualityScore;
  summary: DiscrepancySummary;
  detailedFindings: DetailedFindings;
  recommendations: Recommendation[];
  metrics: ValidationMetrics;
  timestamp: Date;
}
```

**SOPVersion**
```typescript
interface SOPVersion {
  versionId: string;
  sopId: string;
  sop: EnrichedSOP;
  validationReport: ValidationReport;
  parentVersionId?: string;
  changeDescription: string;
  createdAt: Date;
  createdBy: string;
  qualityScore: number;
}
```
## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Data Source Tag Extraction Completeness

*For any* SOP with data source tags in questionnaire items and instructions, when the Validator extracts tags, all tags should be present in the extraction result.

**Validates: Requirements 1.1**

### Property 2: Data Source Availability Verification

*For any* data source tag extracted from an SOP, when the Validator checks availability, it should query MCP Fleet Schema_Registry and return the correct accessibility status.

**Validates: Requirements 1.2**

### Property 3: Missing Data Source Detection

*For any* data source tag that is not registered in MCP Fleet, when the Validator checks it, it should be flagged as a critical discrepancy.

**Validates: Requirements 1.3**

### Property 4: Offline Data Source Warning

*For any* data source that is registered but marked as offline, when the Validator checks it, it should be flagged as a warning-level discrepancy.

**Validates: Requirements 1.4**

### Property 5: Data Source Report Completeness

*For any* SOP validation, the data source availability report should list all data sources referenced in the SOP with their accessibility status.

**Validates: Requirements 1.5**

### Property 6: Field Reference Validation

*For any* SOP instruction referencing data fields, when the Validator processes it, all field references should be validated against MCP Fleet Schema_Registry.

**Validates: Requirements 2.1**

### Property 7: Invalid Field Detection

*For any* field reference that does not exist in the data source schema, when the Validator checks it, it should be flagged as a critical discrepancy with the instruction location.

**Validates: Requirements 2.2**

### Property 8: Type Mismatch Warning

*For any* field reference with a type mismatch, when the Validator checks it, it should be flagged as a warning with type mismatch details.

**Validates: Requirements 2.3**

### Property 9: Multi-Source Field Validation

*For any* SOP referencing fields from Claims_data, Transaction_data, VSPS, or Mainframe, when the Validator validates fields, all data source types should be supported.

**Validates: Requirements 2.4**

### Property 10: Field Validation Report Completeness

*For any* SOP validation, the field validation report should list all field references with their validation status.

**Validates: Requirements 2.5**

### Property 11: Instruction Parsing

*For any* SOP instruction, when the Query_Generator receives it, it should successfully parse the instruction to identify data requirements and validation logic.

**Validates: Requirements 3.1**

### Property 12: Valid Query Generation

*For any* SOP instruction, when the Query_Generator generates a validation query, the query should be syntactically valid for MCP Fleet.

**Validates: Requirements 3.2, 3.3**

### Property 13: Multi-Source Query Generation

*For any* instruction referencing multiple data sources, when the Query_Generator processes it, it should generate a multi-source query with appropriate joins.

**Validates: Requirements 3.4**

### Property 14: Comprehensive Instruction Type Support

*For any* instruction type (data lookup, comparison, conditional logic), when the Query_Generator processes it, it should generate an appropriate validation query.

**Validates: Requirements 3.5**

### Property 15: Query Execution with Authentication

*For any* validation query, when the Validator executes it, the query should be submitted to MCP Fleet with appropriate authentication credentials.

**Validates: Requirements 4.1**

### Property 16: Result and Metadata Capture

*For any* successful validation query, when it executes, the Validator should capture both results and execution metadata.

**Validates: Requirements 4.2**

### Property 17: Authentication Failure Detection

*For any* validation query that fails due to authentication or authorization issues, when it executes, it should be flagged as a critical discrepancy indicating access control problems.

**Validates: Requirements 4.3**

### Property 18: Timeout Handling

*For any* validation query that times out, when it executes, it should be flagged as a performance issue with optimization suggestions.

**Validates: Requirements 4.4**

### Property 19: Rate Limiting Compliance

*For any* sequence of validation queries, when the Validator executes them, the query rate should stay within configured limits to avoid overwhelming MCP Fleet.

**Validates: Requirements 4.5**

### Property 20: Decision Path Test Case Coverage

*For any* decision path in an SOP, when the Validator tests it, test cases should cover all possible validation outcomes.

**Validates: Requirements 5.1**

### Property 21: Decision Path Execution Correctness

*For any* decision path test case, when the Validator executes it, the execution should follow the SOP decision tree from root to terminal node.

**Validates: Requirements 5.2**

### Property 22: Multi-Source Decision Path Coordination

*For any* decision path requiring data from multiple sources, when the Validator tests it, queries should be coordinated across all required sources.

**Validates: Requirements 5.3**

### Property 23: Branch Reachability Verification

*For any* decision tree, when the Validator analyzes it, all decision branches should be verified to have reachable terminal conditions.

**Validates: Requirements 5.4**

### Property 24: Logic Error Detection

*For any* decision path leading to an undefined state or missing instruction, when the Validator tests it, it should be flagged as a critical logic error.

**Validates: Requirements 5.5**

### Property 25: Discrepancy Severity Categorization

*For any* validation run, when the Validator completes, all discrepancies should be categorized by severity (critical, warning, informational).

**Validates: Requirements 6.1**

### Property 26: Discrepancy Detail Completeness

*For any* discrepancy, when the Validator reports it, the report should include SOP location, discrepancy type, and detailed description.

**Validates: Requirements 6.2**

### Property 27: Comprehensive Discrepancy Type Detection

*For any* validation run, when the Validator identifies discrepancies, all discrepancy types (missing data sources, invalid fields, inaccessible data, logic errors, performance issues) should be detectable.

**Validates: Requirements 6.3**

### Property 28: Discrepancy Grouping by Location

*For any* validation run with multiple discrepancies affecting the same SOP section, when the Validator reports them, they should be grouped by location.

**Validates: Requirements 6.4**

### Property 29: Discrepancy Prioritization and Recommendations

*For any* validation run, when the Validator generates the discrepancy list, it should be prioritized and include recommendations for each discrepancy.

**Validates: Requirements 6.5**

### Property 30: Prompt Template Application

*For any* validation query generation, when the Query_Generator creates queries, it should use configurable prompt templates.

**Validates: Requirements 7.1**

### Property 31: Template Variation Support

*For any* SOP instruction type, when the Query_Generator processes it, it should support multiple prompt template variations.

**Validates: Requirements 7.2**

### Property 32: Template Update Application

*For any* prompt template that is updated, when the Query_Generator uses it, the updated version should be applied to generate new queries.

**Validates: Requirements 7.3**

### Property 33: Template Performance Tracking

*For any* prompt template, when the Query_Generator uses it, performance metrics (accuracy, efficiency) should be tracked.

**Validates: Requirements 7.4**

### Property 34: Custom Template Validation

*For any* custom prompt template provided by a validation engineer, when the Query_Generator receives it, it should validate template compatibility before use.

**Validates: Requirements 7.5**

### Property 35: Validation Report Completeness

*For any* completed validation, when the Validator generates the report, it should contain overall quality score, discrepancy summary, and detailed findings.

**Validates: Requirements 8.1**

### Property 36: Validation Metrics Inclusion

*For any* validation report, when generated, it should include metrics for data source availability, field validity, decision path completeness, and query performance.

**Validates: Requirements 8.2**

### Property 37: Discrepancy Recommendations

*For any* discrepancy in a validation report, when reported, it should have an actionable recommendation.

**Validates: Requirements 8.3**

### Property 38: Section and Overall Status Reporting

*For any* validation report, when generated, it should include pass/fail status for each SOP section and overall SOP readiness assessment.

**Validates: Requirements 8.4**

### Property 39: Multi-Format Report Export

*For any* validation report, when exported, it should support JSON, PDF, and HTML formats.

**Validates: Requirements 8.5**

### Property 40: Refinement Suggestion Generation

*For any* identified discrepancy, when the Validator processes it, it should suggest a specific SOP refinement to address the issue.

**Validates: Requirements 9.1**

### Property 41: Selective Section Updates

*For any* refinement applied to an SOP, when the Validator updates it, only affected sections should be modified while unchanged sections are preserved.

**Validates: Requirements 9.2**

### Property 42: Comprehensive Refinement Type Support

*For any* refinement type (updating data sources, correcting fields, fixing logic, adding instructions), when the Validator applies it, the refinement should be supported.

**Validates: Requirements 9.3**

### Property 43: Automatic Re-validation After Refinement

*For any* SOP refinement, when applied, the Validator should automatically re-validate the changed sections.

**Validates: Requirements 9.4**

### Property 44: Refinement-Discrepancy Tracking

*For any* refinement applied, when the Validator processes it, it should track which discrepancies were addressed.

**Validates: Requirements 9.5**

### Property 45: Initial Version Creation

*For any* SOP validated for the first time, when validation completes, the Version_Tracker should create an initial version with validation results.

**Validates: Requirements 10.1**

### Property 46: Version Lineage Preservation

*For any* SOP refinement, when a new version is created, it should include a change description and link to the previous version.

**Validates: Requirements 10.2**

### Property 47: Validation Result Storage with Versions

*For any* SOP version, when created, it should store the validation results for historical comparison.

**Validates: Requirements 10.3**

### Property 48: Version Retrieval Round-Trip

*For any* SOP version stored, when retrieved, it should return the identical SOP and validation results.

**Validates: Requirements 10.4**

### Property 49: Version Diff Accuracy

*For any* two SOP versions, when compared, the diff report should accurately show what changed and how validation results improved or degraded.

**Validates: Requirements 10.5**

### Property 50: A/B Test Variation Acceptance

*For any* A/B test, when created, the Validator should accept multiple SOP variations for the same process.

**Validates: Requirements 11.1**

### Property 51: Consistent Test Case Application

*For any* A/B test, when validating variations, the same test cases should be executed against all variations.

**Validates: Requirements 11.2**

### Property 52: Variation Comparison Metrics

*For any* A/B test, when comparing variations, the comparison should include discrepancy counts, query performance, and decision path coverage.

**Validates: Requirements 11.3**

### Property 53: Variation Performance Reporting

*For any* A/B test, when generating the comparison report, it should show which variation performs better on each metric.

**Validates: Requirements 11.4**

### Property 54: Superior Variation Recommendation

*For any* A/B test that identifies a superior variation, when the Validator analyzes results, it should recommend promoting the better variation.

**Validates: Requirements 11.5**

### Property 55: Cross-Source Consistency Query Generation

*For any* SOP instruction comparing data from multiple sources, when the Validator processes it, it should generate queries to check data consistency.

**Validates: Requirements 12.1**

### Property 56: Data Inconsistency Detection

*For any* cross-source data comparison, when the Validator detects inconsistent data, it should flag it as a data quality issue with specific examples.

**Validates: Requirements 12.2**

### Property 57: Common Field Consistency Validation

*For any* SOP referencing common fields (Customer_ID, Merchant_Name, CA_ID, SM_ID, PF_ID), when the Validator checks consistency, these fields should be validated across sources.

**Validates: Requirements 12.3**

### Property 58: Configurable Consistency Rules

*For any* consistency validation, when the Validator applies rules, it should support configurable rules defining acceptable variance.

**Validates: Requirements 12.4**

### Property 59: Consistency Report Generation

*For any* cross-source validation, when the Validator completes, it should generate a consistency report showing which fields are consistent and which have discrepancies.

**Validates: Requirements 12.5**

### Property 60: Validation Operation Logging

*For any* validation operation, when executed, it should be logged with execution time, query count, and resource usage.

**Validates: Requirements 13.1**

### Property 61: Metrics Exposure

*For any* validation system, when running, it should expose metrics for validation throughput, query latency, discrepancy detection rate, and success rate.

**Validates: Requirements 13.2**

### Property 62: Performance Degradation Alerting

*For any* validation performance degradation, when detected, the Validator should generate alerts with performance diagnostics.

**Validates: Requirements 13.3**

### Property 63: Query Performance Tracking

*For any* MCP Fleet query, when executed, the Validator should track performance to identify slow data sources or inefficient queries.

**Validates: Requirements 13.4**

### Property 64: Transient Error Retry with Backoff

*For any* validation query failing with a transient error, when it fails, the Validator should retry with exponential backoff.

**Validates: Requirements 14.1**

### Property 65: Graceful Degradation on Data Source Unavailability

*For any* temporarily unavailable data source, when encountered, the Validator should continue validating other SOP sections and flag the unavailable source.

**Validates: Requirements 14.2**

### Property 66: Error Resilience

*For any* unexpected error during validation, when encountered, the Validator should log detailed error information and continue with remaining validation tasks.

**Validates: Requirements 14.3**

### Property 67: Error Classification

*For any* error during validation, when encountered, the Validator should distinguish between SOP issues (discrepancies) and system issues (validator or MCP Fleet errors).

**Validates: Requirements 14.4**

### Property 68: Partial Report Generation

*For any* validation that cannot complete due to errors, when errors occur, the Validator should generate a partial validation report.

**Validates: Requirements 14.5**

### Property 69: Batch Processing Independence

*For any* batch of SOPs, when the Validator processes them, each SOP should be processed independently without affecting others.

**Validates: Requirements 15.1**

### Property 70: Batch Parallel Processing

*For any* large batch of SOPs, when the Validator processes them, multiple SOPs should be processed in parallel to optimize throughput.

**Validates: Requirements 15.2**

### Property 71: Batch Error Isolation

*For any* batch of SOPs with some failing validations, when processing, the Validator should continue processing remaining SOPs.

**Validates: Requirements 15.3**

### Property 72: Batch Report Completeness

*For any* batch validation, when completed, the report should contain aggregate metrics and individual results for all SOPs.

**Validates: Requirements 15.4**

### Property 73: Batch Completion Notification

*For any* batch validation, when completed, the Validator should notify administrators with summary statistics.

**Validates: Requirements 15.5**

### Property 74: Completeness Verification

*For any* SOP, when the Validator checks completeness, it should verify that all questionnaire items have validation rules and instructions for each outcome.

**Validates: Requirements 16.1**

### Property 75: Decision Tree Terminal Verification

*For any* decision tree, when the Validator checks it, all branches should lead to terminal conditions.

**Validates: Requirements 16.2**

### Property 76: Data Source Reference Detail Verification

*For any* data source reference in an SOP, when the Validator checks it, it should verify sufficient detail exists for query generation.

**Validates: Requirements 16.3**

### Property 77: Incompleteness Detection

*For any* incomplete SOP section, when the Validator checks it, it should flag the section with specific missing elements.

**Validates: Requirements 16.4**

### Property 78: Completeness Score Calculation

*For any* SOP validation, when completed, the Validator should generate completeness scores for each section and overall SOP.

**Validates: Requirements 16.5**

### Property 79: Custom Rule Registration

*For any* custom validation rule, when registered, the Validator should accept it with rule definition and severity level.

**Validates: Requirements 17.1**

### Property 80: Custom Rule Application

*For any* registered custom rule, when validation runs, the rule should be applied to all relevant SOPs.

**Validates: Requirements 17.2**

### Property 81: Custom Rule Query Generation

*For any* custom rule requiring data checks, when applied, the Validator should generate appropriate validation queries.

**Validates: Requirements 17.3**

### Property 82: Custom Rule Violation Reporting

*For any* custom rule violation, when detected, the Validator should report it with rule-specific details.

**Validates: Requirements 17.4**

### Property 83: Custom Rule Configuration

*For any* custom rule, when configured, the Validator should support enabling/disabling without code changes.

**Validates: Requirements 17.5**

### Property 84: Automatic SOP Reception from Pipeline

*For any* new SOP version from the SOP Extraction Pipeline, when produced, the Validator should automatically receive it for validation.

**Validates: Requirements 18.1**

### Property 85: Standard Format Acceptance

*For any* SOP in standard format from the SOP Extraction Pipeline, when received, the Validator should accept and process it.

**Validates: Requirements 18.2**

### Property 86: Result Delivery to Pipeline

*For any* completed validation, when finished, the Validator should provide results back to the SOP Extraction Pipeline for storage.

**Validates: Requirements 18.3**

### Property 87: Dual Trigger Mode Support

*For any* validation request, when received, the Validator should support both automatic (pipeline-triggered) and manual (user-triggered) validation.

**Validates: Requirements 18.4**

### Property 88: Schema Version Compatibility

*For any* SOP schema version from the extraction pipeline, when received, the Validator should maintain compatibility and process it correctly.

**Validates: Requirements 18.5**

## Error Handling

### Error Categories

The SOP Validator handles five categories of errors:

1. **Data Source Errors**: Data sources not found, offline, or inaccessible
2. **Query Errors**: Query generation failures, syntax errors, execution failures
3. **MCP Fleet Errors**: Authentication failures, timeouts, connection issues
4. **Validation Errors**: Logic errors in SOPs, incomplete sections, inconsistent data
5. **System Errors**: Internal validator failures, resource exhaustion

### Error Handling Strategy

**Graceful Degradation**: When data sources are unavailable or queries fail, the validator continues with remaining validation tasks and produces partial results.

**Retry with Backoff**: Transient errors (timeouts, temporary unavailability) trigger automatic retry with exponential backoff (1s, 2s, 4s, max 3 retries).

**Error Classification**: All errors are classified as either SOP issues (discrepancies to fix) or system issues (infrastructure problems), enabling appropriate routing and response.

**Detailed Logging**: All errors are logged with:
- Error type and severity
- Affected SOP location (S.No, instruction)
- Context information (query, data source, operation)
- Timestamp and correlation ID
- Suggested remediation

### Error Handling by Component

**Data Source Validator Error Handling:**
```typescript
// Continue validation even if some data sources are unavailable
async validateDataSources(sop: EnrichedSOP): Promise<DataSourceValidationReport> {
  const results: DataSourceStatus[] = [];
  const errors: Error[] = [];
  
  for (const tag of extractDataSourceTags(sop)) {
    try {
      const status = await checkAvailability(tag);
      results.push(status);
    } catch (error) {
      errors.push(error);
      // Flag as unavailable but continue
      results.push({
        dataSourceTag: tag,
        available: false,
        status: 'not_found',
        issues: [error.message]
      });
    }
  }
  
  return {
    sopId: sop.document_id,
    dataSources: results,
    overallStatus: determineOverallStatus(results),
    criticalIssues: countCritical(results),
    warnings: countWarnings(results)
  };
}
```

**Query Executor Error Handling:**
```typescript
// Retry transient errors, fail fast on permanent errors
async executeQuery(query: ValidationQuery): Promise<QueryResult> {
  let retryCount = 0;
  const maxRetries = 3;
  
  while (retryCount <= maxRetries) {
    try {
      const result = await mcpFleet.executeQuery(query.mcpQuery);
      return {
        queryId: query.queryId,
        status: 'success',
        data: result.data,
        executionTime: result.executionTime,
        metadata: { retryCount, ...result.metadata }
      };
    } catch (error) {
      if (isTransientError(error) && retryCount < maxRetries) {
        // Exponential backoff
        await sleep(Math.pow(2, retryCount) * 1000);
        retryCount++;
      } else {
        // Permanent error or max retries exceeded
        return {
          queryId: query.queryId,
          status: 'error',
          error: {
            errorType: classifyError(error),
            message: error.message,
            retryable: isTransientError(error)
          },
          executionTime: 0,
          metadata: { retryCount }
        };
      }
    }
  }
}
```

**Decision Path Tester Error Handling:**
```typescript
// Continue testing other paths even if some fail
async testAllPaths(sop: EnrichedSOP): Promise<PathTestReport> {
  const testCases = generateTestCases(sop.decision_tree);
  const results: TestResult[] = [];
  let passedPaths = 0;
  let failedPaths = 0;
  
  for (const testCase of testCases) {
    try {
      const result = await executeTestCase(testCase, sop);
      results.push(result);
      if (result.status === 'pass') passedPaths++;
      else failedPaths++;
    } catch (error) {
      // Log error but continue with other test cases
      results.push({
        testCaseId: testCase.testCaseId,
        status: 'error',
        actualPath: testCase.path,
        discrepancies: [{
          discrepancyId: generateId(),
          type: 'logic_error',
          severity: 'critical',
          location: testCase.path.startNode,
          description: `Test case execution failed: ${error.message}`,
          expected: 'Successful path execution',
          actual: 'Execution error',
          recommendation: 'Review decision path logic and data requirements',
          queryId: ''
        }],
        executionTime: 0
      });
      failedPaths++;
    }
  }
  
  return {
    sopId: sop.document_id,
    totalPaths: testCases.length,
    testedPaths: results.length,
    passedPaths,
    failedPaths,
    unreachableBranches: [],
    testResults: results
  };
}
```

### Error Recovery Strategies

**Automatic Recovery:**
- Use cached schema information when MCP Fleet is temporarily unavailable
- Generate validation queries with fallback templates when preferred templates fail
- Continue validation with partial data when some sources are inaccessible

**Manual Intervention Required:**
- Authentication or authorization failures (requires credential update)
- Critical SOP logic errors (requires SOP refinement)
- Persistent data source unavailability (requires infrastructure fix)

**Error Notification:**
- Real-time alerts for critical errors (auth failures, persistent unavailability)
- Hourly summaries for warnings (slow queries, type mismatches)
- Daily reports for informational issues (optimization opportunities)

## Testing Strategy

### Dual Testing Approach

The SOP Validator requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests**: Verify specific examples, edge cases, and integration points
- Specific SOP examples with known discrepancies
- Edge cases (empty SOPs, maximum size SOPs, malformed data)
- Error conditions (auth failures, timeouts, unavailable sources)
- Integration between components (query generator → executor, analyzer → reporter)

**Property Tests**: Verify universal properties across all inputs
- Data source extraction completeness across random SOPs
- Query generation validity across random instructions
- Discrepancy detection across random validation scenarios
- Version tracking correctness across random refinement sequences

Both approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across the input space.

### Property-Based Testing Configuration

**Testing Library**: Use `fast-check` for TypeScript/JavaScript implementation

**Test Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test references its design document property
- Tag format: **Feature: sop-validator, Property {number}: {property_text}**

**Example Property Test Structure**:
```typescript
import * as fc from 'fast-check';

// Feature: sop-validator, Property 1: Data Source Tag Extraction Completeness
describe('Data Source Validator', () => {
  it('extracts all data source tags from SOP', async () => {
    await fc.assert(
      fc.asyncProperty(
        sopWithDataSourceTagsGenerator(),
        async (sop) => {
          const validator = new DataSourceValidator();
          const extractedTags = validator.extractDataSourceTags(sop);
          
          // Verify all tags in SOP are extracted
          const expectedTags = getAllDataSourceTagsFromSOP(sop);
          expect(extractedTags.length).toBe(expectedTags.length);
          
          for (const expectedTag of expectedTags) {
            expect(extractedTags).toContainEqual(
              expect.objectContaining({
                system_name: expectedTag.system_name
              })
            );
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});

// Feature: sop-validator, Property 48: Version Retrieval Round-Trip
describe('Version Tracker', () => {
  it('retrieves stored versions identically', async () => {
    await fc.assert(
      fc.asyncProperty(
        sopVersionGenerator(),
        async (originalVersion) => {
          const tracker = new VersionTracker();
          
          // Store version
          await tracker.createVersion(
            originalVersion.sop,
            originalVersion.validationReport,
            originalVersion.changeDescription
          );
          
          // Retrieve version
          const retrieved = await tracker.getVersion(
            originalVersion.sopId,
            originalVersion.versionId
          );
          
          // Verify identical
          expect(retrieved.sop).toEqual(originalVersion.sop);
          expect(retrieved.validationReport).toEqual(originalVersion.validationReport);
          expect(retrieved.versionId).toBe(originalVersion.versionId);
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### Test Data Generators

**SOP Generator**:
- Generate random SOPs with various structures
- Include data source tags, field references, decision trees
- Generate both valid and invalid SOPs

**Instruction Generator**:
- Generate random instructions with data requirements
- Include single-source and multi-source instructions
- Generate various instruction types (lookup, comparison, conditional)

**Data Source Generator**:
- Generate data source configurations for Claims_data, Transaction_data, VSPS, Mainframe
- Include various states (online, offline, not_found)
- Generate schemas with tables and fields

**Query Result Generator**:
- Generate random query results with various structures
- Include success, error, and timeout scenarios
- Generate performance metrics

### Integration Testing

**End-to-End Validation Flow**:
1. SOP input → Data source validation → Query generation → Query execution → Result analysis → Report generation
2. Validation → Refinement → Re-validation cycle
3. Batch validation with multiple SOPs
4. A/B testing with SOP variations

**MCP Fleet Integration**:
- Test with mock MCP Fleet for controlled scenarios
- Test with real MCP Fleet for integration verification
- Test error scenarios (auth failures, timeouts, unavailable sources)

**SOP Extraction Pipeline Integration**:
- Test automatic validation trigger from pipeline
- Test result delivery back to pipeline
- Test schema version compatibility

### Test Coverage Goals

- **Unit Test Coverage**: 85%+ line coverage
- **Property Test Coverage**: All 88 correctness properties implemented
- **Integration Test Coverage**: All critical paths covered
- **Performance Benchmarks**: <5s for single SOP validation, >20 SOPs/minute for batch processing
