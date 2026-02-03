# Design Document: MCP Fleet

## Overview

The MCP Fleet is a standardized data integration layer that provides a unified query interface for agents to access heterogeneous data sources. The system acts as an abstraction layer between agents executing SOP instructions and the underlying data systems (Claims_data, Mainframe Transaction_data, VSPS, etc.).

The architecture follows a layered approach:
1. **Query Interface Layer**: Accepts standardized queries from agents
2. **Translation Layer**: Converts unified queries to data-source-specific formats
3. **Execution Layer**: Manages connections, executes queries, and handles results
4. **Caching Layer**: Optimizes performance through intelligent result caching
5. **Registry Layer**: Maintains metadata about available data sources

Key design principles:
- **Abstraction**: Hide data source complexity from agents
- **Extensibility**: Support adding new data sources without code changes
- **Performance**: Handle 4000+ concurrent agents efficiently
- **Resilience**: Gracefully handle failures and transient errors
- **Security**: Enforce authentication and authorization at all levels

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Agents (4000+)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Query Interface API                       │
│  - Request validation                                        │
│  - Authentication/Authorization                              │
│  - Query parsing                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Query Orchestrator                       │
│  - Multi-source coordination                                 │
│  - Cache lookup                                              │
│  - Query optimization                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Query     │  │   Query     │  │   Query     │
│ Translator  │  │ Translator  │  │ Translator  │
│ (Claims)    │  │(Mainframe)  │  │   (VSPS)    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Connection  │  │ Connection  │  │ Connection  │
│    Pool     │  │    Pool     │  │    Pool     │
│  (Claims)   │  │(Mainframe)  │  │   (VSPS)    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Claims_    │  │Transaction_ │  │    VSPS     │
│    data     │  │    data     │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

### Component Interaction Flow

1. Agent submits query to Query Interface API
2. API validates syntax and authenticates agent
3. Query Orchestrator checks Result Cache
4. If cache miss, Orchestrator routes to appropriate Query Translator(s)
5. Translator converts unified query to data-source-specific format
6. Connection Pool provides connection to data source
7. Query executes and results return through the stack
8. Results cached and returned to agent

## Components and Interfaces

### 1. Query Interface API

**Responsibility**: Accept and validate queries from agents, enforce authentication/authorization

**Interface**:
```typescript
interface QueryRequest {
  query: string;              // Unified query in SQL-like syntax
  parameters?: Record<string, any>;  // Query parameters
  options?: QueryOptions;     // Pagination, timeout, etc.
}

interface QueryOptions {
  timeout?: number;           // Query timeout in milliseconds
  pageSize?: number;          // Results per page
  pageToken?: string;         // Pagination token
  cachePolicy?: 'use' | 'bypass' | 'refresh';
}

interface QueryResponse {
  data: Record<string, any>[];
  metadata: QueryMetadata;
  nextPageToken?: string;
}

interface QueryMetadata {
  executionTimeMs: number;
  rowCount: number;
  dataSources: string[];
  cached: boolean;
}

interface QueryAPI {
  executeQuery(request: QueryRequest, agentId: string): Promise<QueryResponse>;
  validateQuery(query: string): Promise<ValidationResult>;
  getDataSources(agentId: string): Promise<DataSourceInfo[]>;
  getSchema(dataSourceId: string, agentId: string): Promise<SchemaInfo>;
}
```

**Key Operations**:
- `executeQuery`: Main entry point for query execution
- `validateQuery`: Syntax validation without execution
- `getDataSources`: Discovery of available data sources
- `getSchema`: Retrieve schema information for a data source

### 2. Schema Registry

**Responsibility**: Maintain metadata about data sources and their schemas

**Interface**:
```typescript
interface DataSourceInfo {
  id: string;
  name: string;
  type: 'sql' | 'mainframe' | 'api' | 'custom';
  status: 'online' | 'offline' | 'degraded';
  capabilities: string[];     // Supported operations
}

interface SchemaInfo {
  dataSourceId: string;
  tables: TableSchema[];
  relationships: Relationship[];
}

interface TableSchema {
  name: string;
  columns: ColumnSchema[];
  primaryKey: string[];
}

interface ColumnSchema {
  name: string;
  dataType: string;
  nullable: boolean;
  description?: string;
}

interface Relationship {
  fromTable: string;
  fromColumn: string;
  toTable: string;
  toColumn: string;
  type: 'one-to-one' | 'one-to-many' | 'many-to-many';
}

interface SchemaRegistry {
  registerDataSource(config: DataSourceConfig): Promise<void>;
  getDataSource(id: string): Promise<DataSourceInfo>;
  listDataSources(): Promise<DataSourceInfo[]>;
  getSchema(dataSourceId: string): Promise<SchemaInfo>;
  updateSchema(dataSourceId: string, schema: SchemaInfo): Promise<void>;
  setDataSourceStatus(id: string, status: string): Promise<void>;
}
```

### 3. Query Translator

**Responsibility**: Convert unified queries to data-source-specific formats

**Interface**:
```typescript
interface TranslationContext {
  dataSourceType: string;
  schema: SchemaInfo;
  capabilities: string[];
}

interface TranslatedQuery {
  nativeQuery: string;        // Data-source-specific query
  parameters: any[];
  estimatedCost?: number;     // Query complexity estimate
}

interface QueryTranslator {
  translate(unifiedQuery: string, context: TranslationContext): Promise<TranslatedQuery>;
  validate(unifiedQuery: string, context: TranslationContext): Promise<ValidationResult>;
  supportsDataSource(dataSourceType: string): boolean;
}

// Specific implementations
interface ClaimsDataTranslator extends QueryTranslator {
  // Translates to Claims_data specific format
}

interface MainframeTranslator extends QueryTranslator {
  // Translates to Mainframe query format (COBOL, JCL, etc.)
}

interface VSPSTranslator extends QueryTranslator {
  // Translates to VSPS API calls
}
```

**Translation Strategy**:
- Parse unified query into Abstract Syntax Tree (AST)
- Apply data-source-specific transformations
- Generate native query string
- Validate against data source capabilities

### 4. Query Orchestrator

**Responsibility**: Coordinate query execution across multiple data sources, manage caching

**Interface**:
```typescript
interface ExecutionPlan {
  steps: ExecutionStep[];
  estimatedTimeMs: number;
  cacheable: boolean;
}

interface ExecutionStep {
  dataSourceId: string;
  query: TranslatedQuery;
  dependencies: string[];     // IDs of steps that must complete first
  joinStrategy?: JoinStrategy;
}

interface JoinStrategy {
  type: 'nested-loop' | 'hash' | 'merge';
  leftKey: string;
  rightKey: string;
}

interface QueryOrchestrator {
  planExecution(request: QueryRequest): Promise<ExecutionPlan>;
  execute(plan: ExecutionPlan): Promise<QueryResponse>;
  checkCache(cacheKey: string): Promise<QueryResponse | null>;
  cacheResult(cacheKey: string, result: QueryResponse, ttl: number): Promise<void>;
}
```

**Orchestration Logic**:
1. Parse query to identify required data sources
2. Check cache for existing results
3. Build execution plan with dependency graph
4. Execute steps in parallel where possible
5. Perform joins for multi-source queries
6. Cache results with appropriate TTL
7. Return unified response

### 5. Connection Pool Manager

**Responsibility**: Manage database connections efficiently across data sources

**Interface**:
```typescript
interface ConnectionConfig {
  dataSourceId: string;
  maxConnections: number;
  minConnections: number;
  idleTimeoutMs: number;
  connectionTimeoutMs: number;
  credentials: Credentials;
}

interface Connection {
  id: string;
  dataSourceId: string;
  status: 'idle' | 'active' | 'failed';
  createdAt: Date;
  lastUsedAt: Date;
}

interface ConnectionPool {
  initialize(config: ConnectionConfig): Promise<void>;
  acquire(dataSourceId: string): Promise<Connection>;
  release(connection: Connection): Promise<void>;
  healthCheck(connection: Connection): Promise<boolean>;
  getPoolStats(dataSourceId: string): Promise<PoolStats>;
  shutdown(dataSourceId: string): Promise<void>;
}

interface PoolStats {
  dataSourceId: string;
  totalConnections: number;
  activeConnections: number;
  idleConnections: number;
  waitingRequests: number;
}
```

**Connection Management Strategy**:
- Maintain minimum pool size for fast query response
- Scale up to maximum based on demand
- Health check connections before use
- Close idle connections after timeout
- Queue requests when pool is exhausted

### 6. Authentication and Authorization Manager

**Responsibility**: Verify agent identity and enforce access controls

**Interface**:
```typescript
interface AuthContext {
  agentId: string;
  roles: string[];
  permissions: Permission[];
}

interface Permission {
  dataSourceId: string;
  operations: ('read' | 'write' | 'admin')[];
  constraints?: Record<string, any>;  // Row-level security, etc.
}

interface AuthManager {
  authenticate(credentials: Credentials): Promise<AuthContext>;
  authorize(context: AuthContext, dataSourceId: string, operation: string): Promise<boolean>;
  getPermissions(agentId: string): Promise<Permission[]>;
  revokeAccess(agentId: string, dataSourceId: string): Promise<void>;
}
```

### 7. Result Cache

**Responsibility**: Cache query results to improve performance

**Interface**:
```typescript
interface CacheEntry {
  key: string;
  value: QueryResponse;
  ttl: number;
  createdAt: Date;
  accessCount: number;
}

interface CacheStrategy {
  computeKey(request: QueryRequest): string;
  computeTTL(request: QueryRequest, response: QueryResponse): number;
  shouldCache(request: QueryRequest, response: QueryResponse): boolean;
}

interface ResultCache {
  get(key: string): Promise<QueryResponse | null>;
  set(key: string, value: QueryResponse, ttl: number): Promise<void>;
  invalidate(pattern: string): Promise<void>;
  getStats(): Promise<CacheStats>;
}

interface CacheStats {
  hitRate: number;
  missRate: number;
  evictionRate: number;
  totalEntries: number;
  memoryUsageBytes: number;
}
```

**Caching Strategy**:
- Cache key based on query + parameters + data sources
- TTL based on data volatility (configurable per data source)
- Invalidate on data source updates (if supported)
- LRU eviction when cache is full

### 8. Circuit Breaker

**Responsibility**: Prevent cascading failures when data sources are unhealthy

**Interface**:
```typescript
interface CircuitBreakerConfig {
  dataSourceId: string;
  failureThreshold: number;    // Failures before opening
  successThreshold: number;    // Successes before closing
  timeoutMs: number;
  halfOpenRetryDelayMs: number;
}

interface CircuitBreakerState {
  status: 'closed' | 'open' | 'half-open';
  failureCount: number;
  successCount: number;
  lastFailureAt?: Date;
  nextRetryAt?: Date;
}

interface CircuitBreaker {
  execute<T>(operation: () => Promise<T>): Promise<T>;
  getState(): CircuitBreakerState;
  reset(): void;
  forceOpen(): void;
  forceClosed(): void;
}
```

**Circuit Breaker Logic**:
- **Closed**: Normal operation, track failures
- **Open**: Reject requests immediately, return error
- **Half-Open**: Allow test request, close if successful

## Data Models

### Unified Query Language

The system uses a SQL-like syntax for the unified query language:

```sql
-- Simple query
SELECT column1, column2 
FROM datasource.table 
WHERE condition = value

-- Multi-source join
SELECT c.Trans_detail, c.Auth_data, t.Customer_ID
FROM claims_data.transactions c
JOIN transaction_data.mainframe t 
  ON c.Customer_ID = t.Customer_ID
WHERE c.POS_MOTO = 'POS'

-- Aggregation
SELECT COUNT(*), AVG(amount)
FROM vsps.stop_payments
WHERE CA_ID = ?
GROUP BY SM_ID
```

### Query AST (Abstract Syntax Tree)

```typescript
interface QueryAST {
  type: 'select' | 'insert' | 'update' | 'delete';
  select?: SelectClause;
  from?: FromClause;
  where?: WhereClause;
  groupBy?: GroupByClause;
  orderBy?: OrderByClause;
  limit?: number;
  offset?: number;
}

interface SelectClause {
  columns: ColumnReference[];
  distinct: boolean;
}

interface ColumnReference {
  dataSource?: string;
  table?: string;
  column: string;
  alias?: string;
  aggregation?: 'COUNT' | 'SUM' | 'AVG' | 'MIN' | 'MAX';
}

interface FromClause {
  tables: TableReference[];
  joins: JoinClause[];
}

interface TableReference {
  dataSource: string;
  table: string;
  alias?: string;
}

interface JoinClause {
  type: 'INNER' | 'LEFT' | 'RIGHT' | 'FULL';
  table: TableReference;
  on: Expression;
}

interface WhereClause {
  expression: Expression;
}

interface Expression {
  type: 'binary' | 'unary' | 'literal' | 'column' | 'function';
  operator?: string;
  left?: Expression;
  right?: Expression;
  value?: any;
  column?: ColumnReference;
  function?: string;
  args?: Expression[];
}
```

### Data Source Configuration

```typescript
interface DataSourceConfig {
  id: string;
  name: string;
  type: 'sql' | 'mainframe' | 'api' | 'custom';
  connectionString?: string;
  apiEndpoint?: string;
  credentials: Credentials;
  poolConfig: ConnectionConfig;
  translatorType: string;
  capabilities: Capability[];
  metadata: Record<string, any>;
}

interface Capability {
  operation: string;          // 'SELECT', 'JOIN', 'AGGREGATE', etc.
  supported: boolean;
  limitations?: string[];
}

interface Credentials {
  type: 'basic' | 'token' | 'certificate' | 'kerberos';
  username?: string;
  password?: string;
  token?: string;
  certificatePath?: string;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Query Syntax Validation

*For any* query string, if it conforms to the unified query syntax, the Query_Interface should accept it; if it does not conform, the Query_Interface should reject it with a descriptive syntax error before any processing occurs.

**Validates: Requirements 1.1, 1.2, 12.1, 12.3**

### Property 2: Multi-Source Query Coordination

*For any* query that references multiple data sources, the Query_Interface should coordinate execution across all referenced sources and include all sources in the response metadata.

**Validates: Requirements 1.3**

### Property 3: Response Format Consistency

*For any* successful query execution, regardless of the underlying data source(s), the response should follow the standardized QueryResponse format with data array, metadata object, and optional pagination token.

**Validates: Requirements 1.4, 6.1**

### Property 4: Error Response Completeness

*For any* failed query (validation, execution, timeout, or authorization failure), the error response should include error type, descriptive message, and identification of the affected component (data source, query clause, etc.).

**Validates: Requirements 1.5, 3.5, 6.2**

### Property 5: Schema Registry Persistence

*For any* registered data source, the Schema_Registry should persistently store its metadata such that subsequent retrieval returns equivalent information.

**Validates: Requirements 2.1**

### Property 6: Data Source Discovery Completeness

*For any* set of registered data sources, when an agent requests available sources, the returned list should contain all registered sources that the agent is authorized to access.

**Validates: Requirements 2.2**

### Property 7: Schema Information Completeness

*For any* data source, when schema information is requested, the response should include all tables, columns with data types, and relationships defined for that data source.

**Validates: Requirements 2.3**

### Property 8: Data Source Status Tracking

*For any* data source that becomes unavailable, the Schema_Registry should mark it as offline in discovery results until it becomes available again.

**Validates: Requirements 2.5**

### Property 9: Query Translation Semantic Preservation

*For any* unified query and target data source, executing the unified query and the translated native query against equivalent test data should produce equivalent results (same rows, same columns, same values).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 10: Connection Reuse

*For any* sequence of queries to the same data source, the Connection_Pool should reuse existing connections rather than creating new connections for each query (when connections are available).

**Validates: Requirements 4.1**

### Property 11: Connection Pool Limits

*For any* Connection_Pool with maximum connection limit N, attempting to acquire N+1 concurrent connections should result in the (N+1)th request being queued until a connection is released.

**Validates: Requirements 4.2, 4.5**

### Property 12: Connection Idle Timeout

*For any* connection that remains idle beyond the configured timeout period, the Connection_Pool should close that connection to free resources.

**Validates: Requirements 4.3**

### Property 13: Connection Health Monitoring

*For any* connection that fails a health check, the Connection_Pool should remove it from the pool and not provide it for subsequent query execution.

**Validates: Requirements 4.4**

### Property 14: Access Control Enforcement

*For any* query request, the MCP_Fleet should authenticate the agent's identity and authorize access to the target data source(s) before executing the query; unauthorized requests should be denied and logged.

**Validates: Requirements 5.1, 5.2, 5.4**

### Property 15: Multi-Credential Support

*For any* data source type (basic auth, token, certificate, Kerberos), the MCP_Fleet should successfully authenticate and execute queries using the appropriate credential type.

**Validates: Requirements 5.3**

### Property 16: Role-Based Access Control

*For any* agent with assigned roles, the agent should be able to access data sources permitted by those roles and be denied access to data sources not permitted by those roles.

**Validates: Requirements 5.5**

### Property 17: Query Timeout Handling

*For any* query that exceeds the configured timeout, the MCP_Fleet should cancel the operation and return a timeout error without waiting for query completion.

**Validates: Requirements 6.3**

### Property 18: Automatic Pagination

*For any* query result that exceeds the configured page size, the MCP_Fleet should automatically paginate the response and provide a nextPageToken for retrieving subsequent pages.

**Validates: Requirements 6.4, 6.5**

### Property 19: Cache Round-Trip

*For any* query executed twice within the cache TTL period, the second execution should return cached results (indicated by metadata.cached = true) that are equivalent to the first execution's results.

**Validates: Requirements 7.1, 7.2**

### Property 20: Query Deduplication

*For any* set of identical queries submitted concurrently, the MCP_Fleet should execute the query once and return the same results to all requesters.

**Validates: Requirements 7.4**

### Property 21: Parallel Multi-Source Execution

*For any* query referencing multiple independent data sources (no joins), the MCP_Fleet should execute sub-queries in parallel, and the total execution time should be closer to the slowest sub-query than the sum of all sub-query times.

**Validates: Requirements 8.1**

### Property 22: Cross-Source Join Correctness

*For any* query that joins data from multiple sources on common fields, the result should contain only rows where the join condition is satisfied, with columns from all joined sources.

**Validates: Requirements 8.2**

### Property 23: Query Logging Completeness

*For any* executed query, the log entry should include execution time, data source(s), result status (success/failure), and query identifier.

**Validates: Requirements 9.1**

### Property 24: Metrics Accuracy

*For any* sequence of query executions, the exposed metrics (query volume, latency, error rates, cache hit rates) should accurately reflect the actual system behavior.

**Validates: Requirements 9.2**

### Property 25: Latency Alerting

*For any* query with execution time exceeding the configured latency threshold, the MCP_Fleet should generate an alert.

**Validates: Requirements 9.3**

### Property 26: Connection Pool Utilization Tracking

*For any* data source, the connection pool utilization metrics should accurately reflect the number of total, active, idle, and waiting connections at any point in time.

**Validates: Requirements 9.4**

### Property 27: Data Source Registration Validation

*For any* data source registration request, if required fields (connection details, credentials, schema) are missing, the registration should fail with a validation error; if all required fields are present and connectivity succeeds, registration should complete.

**Validates: Requirements 10.1, 10.2, 10.3**

### Property 28: Immediate Discovery Availability

*For any* newly registered data source, it should immediately appear in discovery results for authorized agents.

**Validates: Requirements 10.5**

### Property 29: Transient Failure Retry with Backoff

*For any* query that fails with a transient error, the MCP_Fleet should retry the query with exponentially increasing delays between attempts.

**Validates: Requirements 11.1**

### Property 30: Circuit Breaker State Transitions

*For any* data source with a circuit breaker, after N consecutive failures (where N is the failure threshold), the circuit should open and reject requests immediately; after the half-open retry delay, a test request should be allowed; if the test succeeds, the circuit should close.

**Validates: Requirements 11.3, 11.5**

### Property 31: Circuit Breaker Fallback Routing

*For any* data source with an open circuit breaker and a configured fallback source, queries should be routed to the fallback source instead of being rejected.

**Validates: Requirements 11.4**

### Property 32: Query Operation Support

*For any* query using supported operations (SELECT, WHERE, JOIN, GROUP BY, ORDER BY, aggregations), the Query_Interface should successfully parse, validate, and execute the query.

**Validates: Requirements 12.2**

### Property 33: Parameterized Query Safety

*For any* parameterized query with user-provided parameter values, the query execution should properly escape parameters to prevent SQL injection, and the results should be equivalent to a safely constructed query.

**Validates: Requirements 12.4**

## Error Handling

### Error Categories

The system defines the following error categories:

1. **Validation Errors** (400-level)
   - Invalid query syntax
   - Missing required parameters
   - Unsupported operations
   - Schema violations

2. **Authentication Errors** (401-level)
   - Invalid credentials
   - Expired tokens
   - Missing authentication

3. **Authorization Errors** (403-level)
   - Insufficient permissions
   - Data source access denied
   - Operation not allowed

4. **Resource Errors** (404-level)
   - Data source not found
   - Table/column not found
   - No results found

5. **Execution Errors** (500-level)
   - Query execution failure
   - Connection failure
   - Translation failure
   - Timeout

6. **Service Errors** (503-level)
   - Data source unavailable
   - Circuit breaker open
   - Connection pool exhausted

### Error Response Format

```typescript
interface ErrorResponse {
  error: {
    code: string;              // Error code (e.g., "QUERY_SYNTAX_ERROR")
    message: string;           // Human-readable message
    details: ErrorDetails;     // Additional context
    timestamp: string;         // ISO 8601 timestamp
    requestId: string;         // For tracing
  };
}

interface ErrorDetails {
  component?: string;          // Which component failed
  dataSource?: string;         // Affected data source
  query?: string;              // Original query (sanitized)
  position?: number;           // Error position in query
  suggestion?: string;         // How to fix
  retryAfter?: number;         // Seconds until retry (for transient errors)
}
```

### Error Handling Strategies

**Validation Errors**:
- Fail fast before execution
- Provide specific error location and suggestion
- No retry (client must fix query)

**Transient Errors**:
- Automatic retry with exponential backoff
- Maximum 3 retry attempts
- Return error with retryAfter suggestion

**Circuit Breaker Errors**:
- Immediate failure when circuit is open
- Route to fallback if configured
- Return error with estimated recovery time

**Timeout Errors**:
- Cancel in-flight operations
- Clean up resources
- Return partial results if available

**Connection Errors**:
- Remove failed connections from pool
- Retry with different connection
- Mark data source as degraded after repeated failures

## Testing Strategy

### Dual Testing Approach

The MCP Fleet requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Specific query examples (Claims_data joins, VSPS comparisons)
- Edge cases (empty results, malformed queries, connection failures)
- Integration between components (translator → executor, cache → orchestrator)
- Error conditions (authentication failures, timeouts, circuit breaker triggers)

**Property-Based Tests**: Verify universal properties across all inputs
- Query syntax validation across random valid/invalid queries
- Translation semantic preservation across random query structures
- Connection pool behavior under random load patterns
- Cache consistency across random query sequences
- Access control enforcement across random agent/permission combinations

### Property-Based Testing Configuration

**Testing Library**: Use `fast-check` for TypeScript/JavaScript implementation

**Test Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: **Feature: mcp-fleet, Property {N}: {property_text}**
- Generators for: queries, data sources, schemas, credentials, agent contexts

**Example Property Test Structure**:

```typescript
// Feature: mcp-fleet, Property 9: Query Translation Semantic Preservation
describe('Query Translation', () => {
  it('preserves query semantics across translation', async () => {
    await fc.assert(
      fc.asyncProperty(
        queryGenerator(),
        dataSourceGenerator(),
        testDataGenerator(),
        async (query, dataSource, testData) => {
          // Execute unified query
          const unifiedResult = await executeUnified(query, testData);
          
          // Translate and execute native query
          const translated = await translator.translate(query, dataSource);
          const nativeResult = await executeNative(translated, testData);
          
          // Results should be equivalent
          expect(normalizeResults(unifiedResult))
            .toEqual(normalizeResults(nativeResult));
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### Test Data Generators

**Query Generator**:
- Generate random SELECT queries with various clauses
- Include single-source and multi-source queries
- Generate both valid and invalid syntax

**Data Source Generator**:
- Generate configurations for Claims_data, Mainframe, VSPS
- Include various connection types and credentials
- Generate both healthy and unhealthy states

**Schema Generator**:
- Generate random table/column structures
- Include relationships and constraints
- Generate compatible schemas for join testing

**Agent Context Generator**:
- Generate random agent IDs and roles
- Generate various permission sets
- Include both authorized and unauthorized scenarios

### Integration Testing

**Multi-Component Flows**:
1. End-to-end query execution (API → translator → executor → cache)
2. Authentication and authorization flow
3. Circuit breaker triggering and recovery
4. Connection pool exhaustion and recovery
5. Multi-source join execution

**Performance Testing**:
- Load testing with 4000+ concurrent agents
- Query latency under various loads
- Cache hit rate optimization
- Connection pool sizing

**Resilience Testing**:
- Data source failure scenarios
- Network partition scenarios
- Timeout and retry behavior
- Circuit breaker effectiveness

### Test Coverage Goals

- **Unit Test Coverage**: 80%+ line coverage
- **Property Test Coverage**: All 33 correctness properties implemented
- **Integration Test Coverage**: All critical paths covered
- **Performance Benchmarks**: <100ms p95 latency for cached queries, <500ms p95 for uncached single-source queries
