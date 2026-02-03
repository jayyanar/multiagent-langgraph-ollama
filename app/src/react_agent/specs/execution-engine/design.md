# Design Document: Execution Engine

## Overview

The Execution Engine is a scalable runtime platform that executes validated SOPs across 4000+ QA agents and 1000+ controls. It provides two execution paradigms:

1. **System Design Run**: Centralized orchestration with explicit workflow management, dependency resolution, and coordinated task execution
2. **Agent Centric Run**: Distributed autonomous execution where Google ADK agents independently interpret and execute SOPs

The system is built on containerized architecture (Docker/Kubernetes) for isolation, portability, and resource efficiency. Each control process runs in its own container with defined resource limits and lifecycle management.

**Key Design Principles:**
- **Scalability**: Support 4000+ concurrent executions through horizontal scaling and efficient resource management
- **Flexibility**: Support both centralized and distributed execution paradigms
- **Reliability**: Graceful failure handling with automatic retries and comprehensive error recovery
- **Observability**: Complete execution tracking, logging, and metrics for monitoring and compliance
- **Integration**: Seamless integration with MCP Fleet for data access and SOP Validator for SOP validation

## Architecture

The Execution Engine follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Execution Engine                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │  Execution   │         │   Execution  │                      │
│  │  Coordinator │◄────────┤   Monitor    │                      │
│  └──────┬───────┘         └──────────────┘                      │
│         │                                                         │
│         ├──────────┬──────────────────────┐                     │
│         ▼          ▼                       ▼                     │
│  ┌──────────┐  ┌──────────┐        ┌──────────┐                │
│  │ System   │  │  Agent   │        │ Resource │                │
│  │ Design   │  │ Centric  │        │ Manager  │                │
│  │ Run      │  │ Run      │        └────┬─────┘                │
│  │ (Orch.)  │  │ Runtime  │             │                       │
│  └────┬─────┘  └────┬─────┘             │                       │
│       │             │                    │                       │
│       └─────────────┴────────────────────┘                       │
│                     │                                             │
│                     ▼                                             │
│         ┌───────────────────────┐                                │
│         │  Container Manager    │                                │
│         │  (Kubernetes/Docker)  │                                │
│         └───────────┬───────────┘                                │
│                     │                                             │
│         ┌───────────┴───────────┐                                │
│         ▼                       ▼                                 │
│  ┌─────────────┐         ┌─────────────┐                        │
│  │  Failure    │         │   Logging   │                        │
│  │  Handler    │         │   Service   │                        │
│  └─────────────┘         └─────────────┘                        │
│                                                                   │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   MCP Fleet   │
                    └───────────────┘
```

**Component Responsibilities:**

1. **Execution Coordinator**: Entry point for execution requests, routes to appropriate execution mode
2. **System Design Run (Orchestrator)**: Manages centralized workflow execution with dependency resolution
3. **Agent Centric Run Runtime**: Manages autonomous agent deployment and execution
4. **Container Manager**: Handles container lifecycle (create, start, stop, destroy) via Kubernetes/Docker
5. **Resource Manager**: Allocates resources, manages scaling, optimizes utilization
6. **Execution Monitor**: Tracks execution status, collects metrics, generates alerts
7. **Failure Handler**: Manages retries, error recovery, and escalation
8. **Logging Service**: Captures execution logs, audit trails, and provides query interface

## Components and Interfaces

### 1. Execution Coordinator

**Purpose**: Central entry point that receives execution requests and routes them to the appropriate execution mode.

**Interface**:
```python
class ExecutionCoordinator:
    def submit_execution(
        self,
        sop: ValidatedSOP,
        execution_mode: ExecutionMode,
        priority: Priority = Priority.NORMAL,
        schedule: Optional[Schedule] = None
    ) -> ExecutionID:
        """
        Submit an SOP for execution.
        
        Args:
            sop: Validated SOP from SOP Validator
            execution_mode: SYSTEM_DESIGN_RUN or AGENT_CENTRIC_RUN
            priority: Execution priority (CRITICAL, HIGH, NORMAL, LOW)
            schedule: Optional schedule for batch execution
            
        Returns:
            ExecutionID for tracking
        """
        pass
    
    def get_execution_status(self, execution_id: ExecutionID) -> ExecutionStatus:
        """Get current status of an execution."""
        pass
    
    def cancel_execution(self, execution_id: ExecutionID) -> bool:
        """Cancel a running or scheduled execution."""
        pass
```

**Behavior**:
- Validates execution request (SOP is validated, mode is compatible)
- Creates Execution_Context with SOP, data sources, agent config
- Routes to Orchestrator (System Design Run) or Agent_Runtime (Agent Centric Run)
- Registers execution with Execution_Monitor
- Returns ExecutionID for tracking

### 2. System Design Run (Orchestrator)

**Purpose**: Manages centralized workflow execution with explicit dependency management and coordinated task execution.

**Interface**:
```python
class Orchestrator:
    def execute_workflow(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute SOP as centralized workflow.
        
        Args:
            context: Execution context with SOP and configuration
            
        Returns:
            ExecutionResult with status and outputs
        """
        pass
    
    def parse_workflow(self, sop: ValidatedSOP) -> WorkflowGraph:
        """Parse SOP into directed acyclic graph of tasks."""
        pass
    
    def schedule_tasks(self, graph: WorkflowGraph) -> TaskSchedule:
        """Schedule tasks based on dependency resolution."""
        pass
```

**Behavior**:
- Parses SOP into WorkflowGraph (DAG of tasks with dependencies)
- Schedules tasks for execution based on dependency resolution
- Creates containers for each task via Container_Manager
- Monitors task completion and triggers dependent tasks
- Aggregates results from all tasks
- Invokes Failure_Handler on task failures

**Workflow Graph Structure**:
```python
@dataclass
class WorkflowGraph:
    tasks: Dict[TaskID, Task]
    dependencies: Dict[TaskID, List[TaskID]]  # task -> prerequisites
    
@dataclass
class Task:
    task_id: TaskID
    sop_step: SOPStep
    container_spec: ContainerSpec
    timeout: Duration
```

### 3. Agent Centric Run Runtime

**Purpose**: Manages autonomous agent deployment and execution without centralized coordination.

**Interface**:
```python
class AgentRuntime:
    def deploy_agent(self, context: ExecutionContext) -> AgentDeployment:
        """
        Deploy autonomous agent with full SOP.
        
        Args:
            context: Execution context with SOP and configuration
            
        Returns:
            AgentDeployment with agent ID and container info
        """
        pass
    
    def create_agent(self, sop: ValidatedSOP) -> GoogleADKAgent:
        """Create Google ADK agent configured for SOP."""
        pass
```

**Behavior**:
- Creates Google ADK agent with complete SOP and decision-making capabilities
- Packages agent with SOP into container via Container_Manager
- Provides agent with MCP Fleet access credentials
- Deploys container and starts agent execution
- Agent self-monitors and reports status to Execution_Monitor
- Agent makes autonomous decisions based on SOP guidance

### 4. Container Manager

**Purpose**: Manages container lifecycle using Kubernetes or Docker.

**Interface**:
```python
class ContainerManager:
    def create_container(
        self,
        spec: ContainerSpec,
        execution_id: ExecutionID
    ) -> ContainerID:
        """
        Create container for execution.
        
        Args:
            spec: Container specification (image, resources, env)
            execution_id: Associated execution ID
            
        Returns:
            ContainerID for management
        """
        pass
    
    def start_container(self, container_id: ContainerID) -> None:
        """Start container execution."""
        pass
    
    def stop_container(self, container_id: ContainerID) -> None:
        """Stop container execution."""
        pass
    
    def get_container_logs(self, container_id: ContainerID) -> List[LogEntry]:
        """Retrieve container logs."""
        pass
    
    def destroy_container(self, container_id: ContainerID) -> None:
        """Destroy container and release resources."""
        pass
```

**Container Specification**:
```python
@dataclass
class ContainerSpec:
    image: str  # Docker image with agent runtime
    cpu_limit: float  # CPU cores
    memory_limit: int  # Memory in MB
    network_limit: int  # Network bandwidth in Mbps
    environment: Dict[str, str]  # Environment variables
    volumes: List[VolumeMount]  # Mounted volumes
    mcp_credentials: MCPCredentials  # MCP Fleet access
```

**Behavior**:
- Creates containers with specified resource limits
- Ensures isolation between containers
- Manages container lifecycle (create, start, stop, destroy)
- Collects logs and metrics before termination
- Uses Kubernetes for orchestration when available, falls back to Docker

### 5. Resource Manager

**Purpose**: Allocates resources, manages scaling, and optimizes utilization.

**Interface**:
```python
class ResourceManager:
    def allocate_resources(
        self,
        spec: ContainerSpec,
        priority: Priority
    ) -> Optional[ResourceAllocation]:
        """
        Allocate resources for container.
        
        Args:
            spec: Container resource requirements
            priority: Execution priority
            
        Returns:
            ResourceAllocation if resources available, None otherwise
        """
        pass
    
    def release_resources(self, allocation: ResourceAllocation) -> None:
        """Release allocated resources."""
        pass
    
    def scale_up(self, target_capacity: int) -> None:
        """Scale up infrastructure to target capacity."""
        pass
    
    def scale_down(self, target_capacity: int) -> None:
        """Scale down infrastructure to target capacity."""
        pass
    
    def get_utilization_metrics(self) -> UtilizationMetrics:
        """Get current resource utilization metrics."""
        pass
```

**Behavior**:
- Tracks available resources (CPU, memory, network)
- Allocates resources based on priority and availability
- Queues executions when resources are unavailable
- Bin-packs containers to maximize utilization
- Scales infrastructure up/down based on demand
- Collects resource usage metrics for optimization

### 6. Execution Monitor

**Purpose**: Tracks execution status, collects metrics, and generates alerts.

**Interface**:
```python
class ExecutionMonitor:
    def register_execution(
        self,
        execution_id: ExecutionID,
        context: ExecutionContext
    ) -> None:
        """Register new execution for monitoring."""
        pass
    
    def update_status(
        self,
        execution_id: ExecutionID,
        status: ExecutionStatus,
        progress: float
    ) -> None:
        """Update execution status and progress."""
        pass
    
    def get_status(self, execution_id: ExecutionID) -> ExecutionStatus:
        """Get current execution status."""
        pass
    
    def get_metrics(self) -> ExecutionMetrics:
        """Get aggregated execution metrics."""
        pass
    
    def query_executions(
        self,
        filters: ExecutionFilters
    ) -> List[ExecutionInfo]:
        """Query executions with filters."""
        pass
```

**Metrics Collected**:
- Execution count (total, running, completed, failed)
- Success rate (percentage)
- Average duration (by control, by mode)
- Resource utilization (CPU, memory, network)
- Error rate (by error type)
- Queue depth (pending executions)

**Behavior**:
- Tracks execution lifecycle (submitted, running, completed, failed)
- Emits status change events with timestamps
- Generates alerts for long-running executions
- Provides real-time status queries (<100ms response)
- Exposes metrics for dashboards and monitoring tools

### 7. Failure Handler

**Purpose**: Manages retries, error recovery, and escalation.

**Interface**:
```python
class FailureHandler:
    def handle_failure(
        self,
        execution_id: ExecutionID,
        error: ExecutionError
    ) -> FailureAction:
        """
        Handle execution failure.
        
        Args:
            execution_id: Failed execution ID
            error: Error details
            
        Returns:
            FailureAction (RETRY, FAIL, ESCALATE)
        """
        pass
    
    def should_retry(self, error: ExecutionError, attempt: int) -> bool:
        """Determine if error is retryable."""
        pass
    
    def calculate_backoff(self, attempt: int) -> Duration:
        """Calculate exponential backoff duration."""
        pass
```

**Error Classification**:
```python
class ErrorType(Enum):
    TRANSIENT = "transient"  # Network timeout, temporary unavailability
    PERMANENT = "permanent"  # Invalid SOP, missing data source
    RESOURCE = "resource"    # Out of memory, CPU limit exceeded
    CRASH = "crash"          # Container crash, agent failure
```

**Retry Policy**:
- Transient errors: Retry up to 3 times with exponential backoff (1s, 2s, 4s)
- Permanent errors: Fail immediately, no retries
- Resource errors: Retry with increased resource allocation
- Crash errors: Retry with fresh container

**Behavior**:
- Classifies errors as transient or permanent
- Retries transient errors with exponential backoff
- Captures crash logs before retry
- Escalates after exhausting retries
- Records retry attempts in audit log

### 8. Logging Service

**Purpose**: Captures execution logs, audit trails, and provides query interface.

**Interface**:
```python
class LoggingService:
    def log_execution_start(
        self,
        execution_id: ExecutionID,
        context: ExecutionContext
    ) -> None:
        """Log execution start."""
        pass
    
    def log_agent_action(
        self,
        execution_id: ExecutionID,
        action: AgentAction
    ) -> None:
        """Log agent action during execution."""
        pass
    
    def log_execution_complete(
        self,
        execution_id: ExecutionID,
        result: ExecutionResult
    ) -> None:
        """Log execution completion."""
        pass
    
    def query_logs(
        self,
        filters: LogFilters
    ) -> List[LogEntry]:
        """Query logs with filters."""
        pass
```

**Log Entry Structure**:
```python
@dataclass
class LogEntry:
    timestamp: datetime
    execution_id: ExecutionID
    level: LogLevel  # INFO, WARN, ERROR
    component: str  # Component that generated log
    message: str
    metadata: Dict[str, Any]  # Additional context
```

**Behavior**:
- Creates audit log entry on execution start
- Captures all agent actions, decisions, data accesses
- Stores complete execution log on completion
- Retains logs for 90 days minimum
- Supports filtering by execution ID, SOP, agent, time range, status

## Data Models

### Execution Context

```python
@dataclass
class ExecutionContext:
    execution_id: ExecutionID
    sop: ValidatedSOP
    execution_mode: ExecutionMode
    priority: Priority
    data_sources: List[DataSource]
    agent_config: AgentConfig
    resource_requirements: ResourceRequirements
    schedule: Optional[Schedule]
    created_at: datetime
```

### Execution Status

```python
class ExecutionStatus(Enum):
    SUBMITTED = "submitted"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ExecutionInfo:
    execution_id: ExecutionID
    status: ExecutionStatus
    progress: float  # 0.0 to 1.0
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[Duration]
    error: Optional[ExecutionError]
```

### Execution Result

```python
@dataclass
class ExecutionResult:
    execution_id: ExecutionID
    status: ExecutionStatus
    outputs: Dict[str, Any]  # Task outputs
    metrics: ExecutionMetrics
    logs: List[LogEntry]
    retry_count: int
    error: Optional[ExecutionError]
```

### Agent Configuration

```python
@dataclass
class AgentConfig:
    agent_type: str  # Google ADK agent type
    model: str  # LLM model (e.g., "gemini-3-vlm")
    temperature: float
    max_tokens: int
    tools: List[str]  # Available tools/functions
    mcp_access: List[str]  # MCP servers to access
```

### Resource Requirements

```python
@dataclass
class ResourceRequirements:
    cpu_cores: float
    memory_mb: int
    network_mbps: int
    gpu: bool = False
    storage_gb: int = 10
```

### Execution Metrics

```python
@dataclass
class ExecutionMetrics:
    total_executions: int
    running_executions: int
    completed_executions: int
    failed_executions: int
    success_rate: float
    average_duration: Duration
    p95_duration: Duration
    p99_duration: Duration
    resource_utilization: ResourceUtilization
    error_rate: float
    queue_depth: int

@dataclass
class ResourceUtilization:
    cpu_usage: float  # Percentage
    memory_usage: float  # Percentage
    network_usage: float  # Percentage
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all 60 acceptance criteria, I identified several opportunities to consolidate redundant properties:

**Consolidations Made:**
1. **Execution lifecycle logging** (1.4, 1.5, 8.1, 8.3): Combined into single property about complete execution audit trail
2. **Container lifecycle** (4.1, 4.2, 4.4): Combined into single property about proper container packaging and cleanup
3. **MCP Fleet integration** (1.3, 6.1, 6.5): Combined into single property about complete MCP Fleet lifecycle
4. **Status monitoring** (7.1, 7.2): Combined into single property about status tracking and event emission
5. **Resource allocation and release** (10.1, 10.5): Combined into single property about resource lifecycle
6. **Scaling behavior** (10.2, 10.3): Combined into single property about bidirectional scaling
7. **Execution mode validation** (11.3, 11.4): Combined into single property about mode compatibility validation

This reduces 60 criteria to approximately 45 unique, non-redundant properties while maintaining complete coverage.

### Property 1: Execution Context Creation

*For any* validated SOP submitted for execution, creating an Execution_Context should produce a context containing the SOP, all required data sources from the SOP specification, and agent configuration matching the SOP requirements.

**Validates: Requirements 1.1**

### Property 2: Agent Instantiation from Context

*For any* Execution_Context, instantiating an agent should produce a Google ADK agent whose configuration (model, temperature, tools, MCP access) matches the specifications in the Execution_Context.

**Validates: Requirements 1.2**

### Property 3: Complete Execution Audit Trail

*For any* execution from start to completion, the audit log should contain: (1) start entry with execution ID, SOP version, agent ID, timestamp, and execution mode, (2) all agent actions, decisions, and data accesses during execution, and (3) completion entry with results, duration, and final status.

**Validates: Requirements 1.4, 1.5, 8.1, 8.2, 8.3**

### Property 4: Workflow Graph is Valid DAG

*For any* SOP executed in System_Design_Run mode, parsing the SOP should produce a WorkflowGraph where: (1) all tasks are reachable from a start node, (2) no cycles exist in the dependency graph, and (3) all dependencies reference valid tasks.

**Validates: Requirements 2.1**

### Property 5: Dependency-Ordered Task Scheduling

*For any* WorkflowGraph, scheduling tasks should produce a TaskSchedule where every task is scheduled only after all its prerequisite tasks are scheduled.

**Validates: Requirements 2.2**

### Property 6: Dependent Task Triggering

*For any* task completion in System_Design_Run mode, all dependent tasks whose prerequisites are now satisfied should be triggered for execution.

**Validates: Requirements 2.3**

### Property 7: Failure Halts Dependents

*For any* task failure in System_Design_Run mode, all tasks that depend (directly or transitively) on the failed task should be halted and not executed.

**Validates: Requirements 2.4**

### Property 8: Result Aggregation on Completion

*For any* workflow where all tasks complete, the Orchestrator should produce an ExecutionResult containing aggregated outputs from all tasks and mark the execution status as COMPLETED.

**Validates: Requirements 2.5**

### Property 9: Centralized State Maintenance

*For any* execution in System_Design_Run mode, at any point during execution, the Orchestrator should maintain state showing: (1) which tasks have completed, (2) which tasks are running, (3) which tasks are pending, and (4) all dependency relationships.

**Validates: Requirements 2.6**

### Property 10: Complete SOP Deployment in Agent Centric Run

*For any* execution in Agent_Centric_Run mode, the deployed agent should receive the complete SOP with all steps, decision points, and guidance.

**Validates: Requirements 3.1**

### Property 11: Autonomous Agent Capabilities

*For any* agent deployed in Agent_Centric_Run mode, the agent should have: (1) decision-making tools, (2) SOP interpretation capabilities, (3) MCP Fleet access, and (4) status reporting capabilities.

**Validates: Requirements 3.2**

### Property 12: Agent Self-Monitoring

*For any* execution in Agent_Centric_Run mode, the agent should send status updates to the Execution_Monitor at regular intervals (at least every 30 seconds) and whenever significant events occur.

**Validates: Requirements 3.3**

### Property 13: Autonomous Decision Reporting

*For any* ambiguous situation encountered by an agent in Agent_Centric_Run mode, the agent should: (1) make a decision based on SOP guidance, and (2) log the decision with rationale.

**Validates: Requirements 3.4**

### Property 14: Direct Result Reporting

*For any* execution completion in Agent_Centric_Run mode, the agent should report results directly to the Execution_Engine without routing through an orchestrator.

**Validates: Requirements 3.5**

### Property 15: Complete Container Packaging and Cleanup

*For any* control process execution, the container should: (1) be created with the SOP, agent runtime, and all required dependencies, (2) have resource limits (CPU, memory, network) matching the control's requirements, and (3) have logs and metrics collected before termination.

**Validates: Requirements 4.1, 4.2, 4.4**

### Property 16: Container Isolation

*For any* two containers executing concurrently, neither container should be able to access the other's memory, filesystem, or network connections.

**Validates: Requirements 4.3**

### Property 17: Execution Queuing on Resource Exhaustion

*For any* execution request when available resources are insufficient, the Resource_Manager should queue the execution and schedule it when resources become available, maintaining queue order by priority.

**Validates: Requirements 5.2**

### Property 18: Priority-Based Scheduling

*For any* set of queued executions, higher priority executions should be scheduled before lower priority executions when resources become available.

**Validates: Requirements 5.3**

### Property 19: Non-Disruptive Scaling

*For any* scaling operation (up or down), all currently running executions should continue without interruption, failure, or restart.

**Validates: Requirements 5.5**

### Property 20: Complete MCP Fleet Integration Lifecycle

*For any* execution requiring data access, the Execution_Engine should: (1) provide MCP Fleet credentials and endpoints to the agent, (2) authorize and log all MCP Fleet queries, (3) validate returned data format, and (4) close all MCP Fleet connections on execution completion.

**Validates: Requirements 1.3, 6.1, 6.2, 6.3, 6.5**

### Property 21: MCP Fleet Retry with Exponential Backoff

*For any* MCP Fleet unavailability, the Execution_Engine should retry with exponential backoff (1s, 2s, 4s) up to 3 times, and invoke the Failure_Handler if all retries are exhausted.

**Validates: Requirements 6.4**

### Property 22: Comprehensive Status Tracking and Event Emission

*For any* execution, the Execution_Monitor should: (1) track status, progress percentage, and elapsed time continuously, and (2) emit status change events with timestamps and context whenever status changes.

**Validates: Requirements 7.1, 7.2**

### Property 23: Long-Running Execution Alerting

*For any* execution whose duration exceeds 2x the expected duration for its control type, the Execution_Monitor should generate an alert and flag the execution for investigation.

**Validates: Requirements 7.3**

### Property 24: Complete Metrics Collection

*For any* time window, the Execution_Monitor should expose metrics including: execution count (total, running, completed, failed), success rate, average duration, p95 duration, p99 duration, resource utilization (CPU, memory, network), error rate, and queue depth.

**Validates: Requirements 7.4**

### Property 25: Log Query Filtering

*For any* log query with filters (execution ID, SOP, agent, time range, status), the returned logs should contain only entries matching all specified filters.

**Validates: Requirements 8.5**

### Property 26: Transient Error Retry with Exponential Backoff

*For any* execution failure classified as transient, the Failure_Handler should retry up to 3 times with exponential backoff (1s, 2s, 4s), and mark the execution as successful if any retry succeeds, recording the retry count.

**Validates: Requirements 9.1, 9.3**

### Property 27: Permanent Error Immediate Failure

*For any* execution failure classified as permanent, the Failure_Handler should immediately mark the execution as FAILED, record error details, and not attempt any retries.

**Validates: Requirements 9.2**

### Property 28: Retry Exhaustion Escalation

*For any* execution where all retries are exhausted, the Failure_Handler should escalate the failure and notify the operations team.

**Validates: Requirements 9.4**

### Property 29: Container Crash Recovery

*For any* container crash, the Failure_Handler should: (1) capture crash logs, and (2) restart the container with a fresh instance if retries remain.

**Validates: Requirements 9.5**

### Property 30: Resource Lifecycle Management

*For any* execution, resources should be: (1) allocated using bin-packing to maximize utilization when scheduled, and (2) immediately released for reuse when execution completes.

**Validates: Requirements 10.1, 10.5**

### Property 31: Bidirectional Scaling Based on Utilization

*For any* sustained period (>5 minutes) where resource utilization is below 30%, the Resource_Manager should scale down infrastructure, and for any sustained period where utilization is above 80%, the Resource_Manager should scale up infrastructure.

**Validates: Requirements 10.2, 10.3**

### Property 32: Metrics-Driven Resource Optimization

*For any* execution, the Resource_Manager should collect resource usage metrics (CPU, memory, network) and use historical metrics to optimize resource allocation for future executions of the same control type.

**Validates: Requirements 10.4**

### Property 33: Execution Mode Default Selection

*For any* SOP without specified execution mode, the Execution_Engine should default to Agent_Centric_Run if the SOP has no explicit dependencies between steps, and System_Design_Run if the SOP has explicit dependencies.

**Validates: Requirements 11.2**

### Property 34: Execution Mode Compatibility Validation

*For any* execution submission, if the selected execution mode is incompatible with the SOP structure (e.g., Agent_Centric_Run for SOP with complex dependencies), the Execution_Engine should reject the execution and return an error describing the incompatibility.

**Validates: Requirements 11.3, 11.4**

### Property 35: Execution Mode Change Validation

*For any* execution mode change for a control, the Execution_Engine should validate the new mode is compatible with the control's SOP and update the configuration only if validation passes.

**Validates: Requirements 11.5**

### Property 36: Real-Time Immediate Execution

*For any* real-time execution request when resources are available, the Execution_Engine should start the execution within 1 second of request submission.

**Validates: Requirements 12.1**

### Property 37: Batch Execution Scheduling

*For any* batch execution request with a specified time window, the Execution_Engine should schedule the execution to start within that time window.

**Validates: Requirements 12.2**

### Property 38: Batch Resource Optimization

*For any* set of scheduled batch executions, the Resource_Manager should optimize resource allocation to minimize total resource usage while ensuring all executions complete within their time windows.

**Validates: Requirements 12.3**

### Property 39: Real-Time Preemption of Batch Executions

*For any* real-time execution request during high load, if no resources are available, the Execution_Engine should preempt the lowest-priority batch execution to free resources for the real-time execution.

**Validates: Requirements 12.4**

### Property 40: Batch Result Aggregation and Reporting

*For any* batch execution completion, the Execution_Engine should aggregate results from all executions in the batch and generate a batch execution report containing summary statistics and individual execution results.

**Validates: Requirements 12.5**

## Error Handling

The Execution Engine implements comprehensive error handling across all components:

### Error Classification

Errors are classified into four categories to determine appropriate handling:

1. **Transient Errors**: Temporary failures that may succeed on retry
   - Network timeouts
   - Temporary service unavailability
   - Rate limiting
   - **Handling**: Retry up to 3 times with exponential backoff (1s, 2s, 4s)

2. **Permanent Errors**: Failures that will not succeed on retry
   - Invalid SOP structure
   - Missing required data source
   - Authentication failure
   - **Handling**: Fail immediately, no retries, record error details

3. **Resource Errors**: Failures due to insufficient resources
   - Out of memory
   - CPU limit exceeded
   - Disk space exhausted
   - **Handling**: Retry with increased resource allocation if possible

4. **Crash Errors**: Container or agent crashes
   - Segmentation fault
   - Unhandled exception
   - Process killed
   - **Handling**: Capture crash logs, restart with fresh container

### Retry Strategy

```python
def calculate_backoff(attempt: int) -> Duration:
    """Calculate exponential backoff: 1s, 2s, 4s"""
    return Duration(seconds=2 ** (attempt - 1))

def should_retry(error: ExecutionError, attempt: int) -> bool:
    """Determine if error should be retried"""
    if attempt >= 3:
        return False
    
    if error.type == ErrorType.TRANSIENT:
        return True
    elif error.type == ErrorType.RESOURCE:
        return has_additional_resources()
    elif error.type == ErrorType.CRASH:
        return True
    else:  # PERMANENT
        return False
```

### Failure Escalation

When all retries are exhausted:
1. Mark execution as FAILED
2. Record complete error history (all attempts)
3. Generate escalation alert
4. Notify operations team via configured channels
5. Update execution metrics (error rate, failure count)

### Partial Failure Handling

For System_Design_Run mode with multiple tasks:
- **Task Failure**: Halt dependent tasks, continue independent tasks
- **Partial Success**: Mark execution as PARTIALLY_COMPLETED
- **Rollback**: If SOP specifies rollback steps, execute them on failure

### Circuit Breaker Pattern

For external dependencies (MCP Fleet):
- Track failure rate over sliding window (last 100 requests)
- If failure rate exceeds 50%, open circuit breaker
- While circuit open, fail fast without attempting requests
- After cooldown period (30s), attempt single request to test recovery
- If successful, close circuit and resume normal operation

## Testing Strategy

The Execution Engine requires comprehensive testing across multiple dimensions to ensure correctness, reliability, and performance at scale.

### Dual Testing Approach

We employ both unit testing and property-based testing as complementary strategies:

**Unit Tests**: Focus on specific examples, edge cases, and error conditions
- Specific SOP structures (simple, complex, invalid)
- Boundary conditions (resource limits, timeout thresholds)
- Error scenarios (network failures, invalid data)
- Integration points (MCP Fleet, Container Manager)

**Property Tests**: Verify universal properties across all inputs
- Run minimum 100 iterations per property test
- Use property-based testing library (Hypothesis for Python, fast-check for TypeScript)
- Each test references its design document property
- Tag format: **Feature: execution-engine, Property {number}: {property_text}**

### Property-Based Testing Configuration

**Library Selection**:
- Python: Hypothesis
- TypeScript: fast-check
- Java: jqwik
- Go: gopter

**Test Configuration**:
```python
# Example Hypothesis configuration
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(sop=st.from_type(ValidatedSOP))
def test_execution_context_creation(sop):
    """
    Feature: execution-engine, Property 1: Execution Context Creation
    
    For any validated SOP submitted for execution, creating an 
    Execution_Context should produce a context containing the SOP, 
    all required data sources, and agent configuration.
    """
    context = execution_coordinator.create_context(sop)
    
    assert context.sop == sop
    assert all(ds in context.data_sources for ds in sop.required_data_sources)
    assert context.agent_config.matches_sop_requirements(sop)
```

### Test Categories

#### 1. Execution Mode Tests

**Unit Tests**:
- System Design Run with simple linear workflow
- System Design Run with complex branching workflow
- Agent Centric Run with autonomous decision points
- Mode selection defaults for various SOP structures

**Property Tests**:
- Property 4: Workflow Graph is Valid DAG
- Property 5: Dependency-Ordered Task Scheduling
- Property 33: Execution Mode Default Selection

#### 2. Container Management Tests

**Unit Tests**:
- Container creation with specific resource limits
- Container isolation verification
- Container cleanup after execution
- Kubernetes vs Docker fallback

**Property Tests**:
- Property 15: Complete Container Packaging and Cleanup
- Property 16: Container Isolation

#### 3. Resource Management Tests

**Unit Tests**:
- Resource allocation when resources available
- Queuing when resources exhausted
- Priority-based scheduling with specific priorities
- Scaling up/down at specific thresholds

**Property Tests**:
- Property 17: Execution Queuing on Resource Exhaustion
- Property 18: Priority-Based Scheduling
- Property 30: Resource Lifecycle Management
- Property 31: Bidirectional Scaling Based on Utilization

#### 4. Failure Handling Tests

**Unit Tests**:
- Transient error with successful retry
- Permanent error with no retry
- Retry exhaustion and escalation
- Container crash recovery

**Property Tests**:
- Property 26: Transient Error Retry with Exponential Backoff
- Property 27: Permanent Error Immediate Failure
- Property 28: Retry Exhaustion Escalation
- Property 29: Container Crash Recovery

#### 5. MCP Fleet Integration Tests

**Unit Tests**:
- Successful data query through MCP Fleet
- MCP Fleet unavailability with retry
- Data format validation
- Connection cleanup

**Property Tests**:
- Property 20: Complete MCP Fleet Integration Lifecycle
- Property 21: MCP Fleet Retry with Exponential Backoff

#### 6. Monitoring and Logging Tests

**Unit Tests**:
- Status change event emission
- Alert generation for long-running execution
- Log query with specific filters
- Metrics aggregation

**Property Tests**:
- Property 3: Complete Execution Audit Trail
- Property 22: Comprehensive Status Tracking and Event Emission
- Property 24: Complete Metrics Collection
- Property 25: Log Query Filtering

#### 7. Orchestration Tests

**Unit Tests**:
- Task triggering after prerequisite completion
- Dependent task halting on failure
- Result aggregation from multiple tasks

**Property Tests**:
- Property 6: Dependent Task Triggering
- Property 7: Failure Halts Dependents
- Property 8: Result Aggregation on Completion
- Property 9: Centralized State Maintenance

#### 8. Agent Centric Run Tests

**Unit Tests**:
- Agent deployment with complete SOP
- Autonomous decision making
- Direct result reporting

**Property Tests**:
- Property 10: Complete SOP Deployment in Agent Centric Run
- Property 11: Autonomous Agent Capabilities
- Property 12: Agent Self-Monitoring
- Property 13: Autonomous Decision Reporting
- Property 14: Direct Result Reporting

#### 9. Batch and Real-Time Execution Tests

**Unit Tests**:
- Real-time execution immediate start
- Batch execution scheduling
- Real-time preemption of batch execution

**Property Tests**:
- Property 36: Real-Time Immediate Execution
- Property 37: Batch Execution Scheduling
- Property 38: Batch Resource Optimization
- Property 39: Real-Time Preemption of Batch Executions
- Property 40: Batch Result Aggregation and Reporting

### Integration Testing

Beyond unit and property tests, integration tests verify end-to-end workflows:

1. **Complete Execution Flow**: Submit SOP → Execute → Monitor → Complete → Verify Results
2. **Failure Recovery Flow**: Submit SOP → Inject Failure → Verify Retry → Verify Recovery
3. **Scale Testing**: Submit 100 concurrent executions → Verify all complete successfully
4. **MCP Fleet Integration**: Execute SOP requiring data → Verify MCP queries → Verify results
5. **Mode Switching**: Execute same SOP in both modes → Verify equivalent results

### Performance Testing

Performance tests validate scalability and latency requirements:

1. **Concurrency Test**: 4000 concurrent executions, verify all complete
2. **Status Query Latency**: Query status during high load, verify <100ms response
3. **Resource Utilization**: Monitor CPU/memory during peak load, verify <80% utilization
4. **Scaling Speed**: Trigger scale-up, verify new capacity available within 2 minutes

### Test Data Generation

For property-based tests, we generate:

**SOPs**:
- Simple SOPs (1-3 steps, no dependencies)
- Complex SOPs (10+ steps, multiple dependencies)
- Invalid SOPs (cycles, missing steps, invalid references)

**Execution Contexts**:
- Various execution modes
- Different priority levels
- Multiple data source configurations

**Resource Scenarios**:
- Low utilization (<30%)
- Normal utilization (30-80%)
- High utilization (>80%)
- Resource exhaustion

**Error Scenarios**:
- Transient errors (network timeout, rate limit)
- Permanent errors (invalid SOP, missing data)
- Resource errors (OOM, CPU limit)
- Crash errors (segfault, unhandled exception)

### Continuous Testing

All tests run in CI/CD pipeline:
- Unit tests: Run on every commit
- Property tests: Run on every commit (100 iterations each)
- Integration tests: Run on every PR
- Performance tests: Run nightly
- Scale tests: Run weekly

### Test Coverage Goals

- Line coverage: >90%
- Branch coverage: >85%
- Property coverage: 100% (all 40 properties tested)
- Integration coverage: All critical paths tested
