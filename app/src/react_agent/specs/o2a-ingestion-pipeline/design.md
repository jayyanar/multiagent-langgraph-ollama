# Design Document: O2A Ingestion Pipeline

## Overview

The O2A Ingestion Pipeline is a distributed video processing system that transforms manual quality control observations into automated process understanding. The system captures video streams from 4000+ QA agent machines, processes them using Google Gemini 3 Vision Language Model (VLM), and generates structured outputs including text responses and process maps.

The architecture follows a pipeline pattern with distinct stages: ingestion, segmentation, AI processing, extraction, mapping, and output generation. Each stage is designed for horizontal scalability to handle high-volume concurrent processing while maintaining low latency.

Key design principles:
- **Scalability**: Support 4000+ concurrent video streams with auto-scaling
- **Reliability**: Robust error handling with retry logic and fallback mechanisms
- **Experimentation**: Built-in A/B testing framework for prompt optimization
- **Observability**: Comprehensive logging and metrics at each pipeline stage
- **Modularity**: Loosely coupled components for independent scaling and updates

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│  QA Agent       │
│  Machines       │
│  (4000+)        │
└────────┬────────┘
         │ Video Streams
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    O2A Ingestion Pipeline                    │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Ingestion  │───▶│ Segmentation │───▶│ VLM Process  │  │
│  │   Service    │    │   Service    │    │   Service    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Video & Segment Storage                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Extraction  │───▶│  SOP Mapping │───▶│ Process Map  │  │
│  │   Service    │    │   Service    │    │  Generator   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Structured Data & Process Map Storage         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Prompt Engineering & Experimentation          │  │
│  │         (A/B Testing, Metrics, Versioning)            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Downstream     │
│  Systems        │
│  (Analytics,    │
│   Automation)   │
└─────────────────┘
```

### Component Interaction Flow

1. **SKAN Agents** on QA machines capture video streams and send them to the Ingestion Service
2. **Ingestion Service** receives streams, timestamps frames, handles buffering, and stores raw video
3. **Segmentation Service** analyzes video for activity changes and creates discrete segments
4. **VLM Processing Service** submits segments to Gemini 3 VLM with prompt templates
5. **Extraction Service** parses VLM responses, validates schema, and extracts structured data
6. **SOP Mapping Service** matches extracted actions to SOP questionnaire items
7. **Process Map Generator** constructs workflow graphs from mapped actions
8. **Storage Layer** persists all artifacts with queryable metadata
9. **Experimentation Framework** manages prompt versions and tracks performance metrics

## Components and Interfaces

### 1. Ingestion Service

**Responsibilities:**
- Accept video stream connections from SKAN agents
- Timestamp incoming frames with millisecond precision
- Handle network interruptions with local buffering
- Store raw video in VLM-compatible format
- Manage connection pool for 4000+ concurrent streams

**Interfaces:**

```python
class IngestionService:
    def accept_stream(self, agent_id: str, stream: VideoStream) -> StreamHandle:
        """
        Establish connection to receive video stream from agent.
        Returns handle for stream management.
        """
        pass
    
    def buffer_frames(self, handle: StreamHandle, frames: List[Frame]) -> None:
        """
        Buffer frames locally during network interruption.
        Automatically resumes transmission when connectivity restored.
        """
        pass
    
    def store_video(self, handle: StreamHandle, video_data: bytes) -> VideoReference:
        """
        Store raw video in format compatible with Gemini VLM.
        Returns reference for downstream processing.
        """
        pass
    
    def get_stream_status(self, agent_id: str) -> StreamStatus:
        """
        Query current status of agent's video stream.
        """
        pass
```

**Data Models:**

```python
@dataclass
class Frame:
    timestamp: datetime  # Millisecond precision
    data: bytes
    agent_id: str
    sequence_number: int

@dataclass
class StreamHandle:
    agent_id: str
    connection_id: str
    start_time: datetime
    buffer_size: int

@dataclass
class StreamStatus:
    agent_id: str
    is_active: bool
    frames_received: int
    last_frame_time: datetime
    buffer_utilization: float
```

### 2. Segmentation Service

**Responsibilities:**
- Detect activity changes in video streams
- Create discrete segments with temporal boundaries
- Maintain frame continuity between segments
- Apply maximum segment duration limits

**Interfaces:**

```python
class SegmentationService:
    def segment_video(self, video_ref: VideoReference) -> List[VideoSegment]:
        """
        Segment video into discrete units based on activity detection.
        Returns list of segments with temporal metadata.
        """
        pass
    
    def detect_activity_change(self, frames: List[Frame], threshold: float = 0.85) -> bool:
        """
        Analyze frames for visual changes indicating new activity.
        Returns True if change detected above confidence threshold.
        """
        pass
    
    def create_segment(self, frames: List[Frame], start: datetime, end: datetime) -> VideoSegment:
        """
        Create segment from frame sequence with temporal boundaries.
        """
        pass
```

**Data Models:**

```python
@dataclass
class VideoSegment:
    segment_id: str
    video_ref: VideoReference
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    frame_count: int
    confidence_score: float  # Activity detection confidence
```

### 3. VLM Processing Service

**Responsibilities:**
- Submit video segments to Gemini 3 VLM API
- Apply configured prompt templates
- Handle API rate limiting and quotas
- Implement retry logic with exponential backoff
- Validate response schemas

**Interfaces:**

```python
class VLMProcessingService:
    def process_segment(self, segment: VideoSegment, prompt: PromptTemplate) -> VLMResponse:
        """
        Submit segment to Gemini VLM with prompt template.
        Returns structured response with extracted data.
        """
        pass
    
    def retry_with_backoff(self, segment: VideoSegment, prompt: PromptTemplate, 
                          max_attempts: int = 3) -> VLMResponse:
        """
        Retry processing with exponential backoff on failure.
        """
        pass
    
    def validate_response(self, response: VLMResponse) -> bool:
        """
        Validate VLM response against expected schema.
        """
        pass
    
    def apply_rate_limiting(self) -> None:
        """
        Enforce API quota limits while maximizing throughput.
        """
        pass
```

**Data Models:**

```python
@dataclass
class PromptTemplate:
    template_id: str
    version: str
    task_description: str
    output_format: Dict[str, Any]
    examples: List[str]
    parameters: Dict[str, Any]

@dataclass
class VLMResponse:
    segment_id: str
    prompt_version: str
    extracted_data: Dict[str, Any]
    confidence_scores: Dict[str, float]
    processing_time_ms: int
    timestamp: datetime
```

### 4. Extraction Service

**Responsibilities:**
- Parse VLM responses into structured data
- Extract actions, text, form fields, and decisions
- Classify actions into predefined categories
- Tag extracted elements with data sources
- Maintain temporal ordering of actions

**Interfaces:**

```python
class ExtractionService:
    def extract_actions(self, vlm_response: VLMResponse) -> List[Action]:
        """
        Extract and classify user actions from VLM response.
        Returns ordered list of actions with metadata.
        """
        pass
    
    def extract_data_values(self, vlm_response: VLMResponse) -> Dict[str, DataValue]:
        """
        Extract form fields, screen text, and entered values.
        Returns dictionary mapping field names to values with source tags.
        """
        pass
    
    def classify_action(self, action_data: Dict[str, Any]) -> ActionCategory:
        """
        Classify action into predefined category.
        """
        pass
    
    def tag_data_source(self, element: Any, source_info: Dict[str, Any]) -> DataSourceTag:
        """
        Create data source tag indicating element origin.
        """
        pass
```

**Data Models:**

```python
@dataclass
class Action:
    action_id: str
    segment_id: str
    timestamp: datetime
    category: ActionCategory
    target: str  # Form field, button, menu item
    value: Optional[str]  # For data entry actions
    confidence: float
    data_source_tag: DataSourceTag

@dataclass
class ActionCategory(Enum):
    DATA_ENTRY = "data_entry"
    VALIDATION_CHECK = "validation_check"
    NAVIGATION = "navigation"
    ERROR_HANDLING = "error_handling"
    APPROVAL = "approval"

@dataclass
class DataValue:
    field_name: str
    value: str
    data_type: str
    source_tag: DataSourceTag
    confidence: float

@dataclass
class DataSourceTag:
    source_type: str  # "screen_region", "form_field", "button_click"
    coordinates: Optional[Tuple[int, int, int, int]]
    element_id: Optional[str]
```

### 5. SOP Mapping Service

**Responsibilities:**
- Match extracted actions to SOP questionnaire items
- Identify validation points and decision paths
- Track questionnaire sequence numbers
- Flag unmapped actions for review
- Maintain hierarchical relationships

**Interfaces:**

```python
class SOPMappingService:
    def map_to_sop(self, actions: List[Action], sop_definition: SOPDefinition) -> SOPMapping:
        """
        Map actions to SOP questionnaire items.
        Returns mapping with matched items and unmapped actions.
        """
        pass
    
    def identify_validation_point(self, action: Action, sop_definition: SOPDefinition) -> Optional[ValidationPoint]:
        """
        Identify if action corresponds to SOP validation checkpoint.
        """
        pass
    
    def extract_decision_path(self, validation: ValidationPoint, subsequent_actions: List[Action]) -> DecisionPath:
        """
        Extract yes/no decision and subsequent instruction path.
        """
        pass
    
    def flag_unmapped_action(self, action: Action) -> UnmappedAction:
        """
        Flag action that doesn't match any SOP item for review.
        """
        pass
```

**Data Models:**

```python
@dataclass
class SOPDefinition:
    sop_id: str
    questionnaire_items: List[QuestionnaireItem]
    validation_rules: Dict[str, Any]

@dataclass
class QuestionnaireItem:
    sequence_number: str  # S.No
    question: str
    validation_type: str  # "yes_no", "data_entry", "check"
    instructions: Dict[str, str]  # Maps answer to instruction

@dataclass
class ValidationPoint:
    item_sequence: str
    question: str
    decision: bool  # True for Yes, False for No
    instruction_followed: str
    timestamp: datetime

@dataclass
class SOPMapping:
    actions: List[Action]
    mapped_items: List[Tuple[Action, QuestionnaireItem]]
    unmapped_actions: List[UnmappedAction]
    validation_points: List[ValidationPoint]
    decision_paths: List[DecisionPath]

@dataclass
class DecisionPath:
    validation_point: ValidationPoint
    decision: bool
    subsequent_actions: List[Action]
    instruction_text: str

@dataclass
class UnmappedAction:
    action: Action
    reason: str
    flagged_for_review: bool
```

### 6. Process Map Generator

**Responsibilities:**
- Construct workflow graphs from mapped actions
- Create nodes for actions, decisions, and validations
- Define edges representing flow and conditions
- Include metadata for each node
- Output in machine-readable format (JSON/GraphML)

**Interfaces:**

```python
class ProcessMapGenerator:
    def generate_process_map(self, sop_mapping: SOPMapping) -> ProcessMap:
        """
        Generate process map from SOP-mapped actions.
        Returns graph structure with nodes and edges.
        """
        pass
    
    def create_action_node(self, action: Action) -> ProcessNode:
        """
        Create node representing an action.
        """
        pass
    
    def create_decision_node(self, validation: ValidationPoint) -> ProcessNode:
        """
        Create node representing a decision point.
        """
        pass
    
    def create_edge(self, from_node: ProcessNode, to_node: ProcessNode, 
                   condition: Optional[str] = None) -> ProcessEdge:
        """
        Create edge connecting two nodes with optional condition.
        """
        pass
    
    def export_to_json(self, process_map: ProcessMap) -> str:
        """
        Export process map to JSON format.
        """
        pass
    
    def export_to_graphml(self, process_map: ProcessMap) -> str:
        """
        Export process map to GraphML format.
        """
        pass
```

**Data Models:**

```python
@dataclass
class ProcessMap:
    map_id: str
    agent_id: str
    control_id: str
    timestamp: datetime
    nodes: List[ProcessNode]
    edges: List[ProcessEdge]
    metadata: Dict[str, Any]

@dataclass
class ProcessNode:
    node_id: str
    node_type: str  # "action", "decision", "validation"
    label: str
    timestamp: datetime
    duration_seconds: Optional[float]
    data_values: Dict[str, Any]
    data_source_tags: List[DataSourceTag]
    confidence: float

@dataclass
class ProcessEdge:
    edge_id: str
    from_node: str  # node_id
    to_node: str    # node_id
    condition: Optional[str]  # "yes", "no", or other condition
    label: Optional[str]
```

### 7. Prompt Engineering Framework

**Responsibilities:**
- Manage prompt template versions
- Support A/B testing with configurable distributions
- Track extraction accuracy metrics per template
- Store performance data for comparison
- Validate template structure

**Interfaces:**

```python
class PromptEngineeringFramework:
    def create_template(self, template: PromptTemplate) -> str:
        """
        Create new prompt template with validation.
        Returns template ID.
        """
        pass
    
    def validate_template(self, template: PromptTemplate) -> bool:
        """
        Validate template structure against required fields.
        """
        pass
    
    def configure_ab_test(self, templates: List[str], distribution: Dict[str, float]) -> ABTestConfig:
        """
        Configure A/B test with template IDs and distribution ratios.
        """
        pass
    
    def assign_template(self, segment: VideoSegment, ab_config: ABTestConfig) -> PromptTemplate:
        """
        Randomly assign segment to template based on distribution.
        """
        pass
    
    def track_metrics(self, template_id: str, metrics: PerformanceMetrics) -> None:
        """
        Store performance metrics for template.
        """
        pass
    
    def compare_templates(self, template_ids: List[str]) -> ComparisonReport:
        """
        Generate comparison report for template performance.
        """
        pass
    
    def version_template(self, template_id: str, updates: Dict[str, Any]) -> str:
        """
        Create new version of template with updates.
        Returns new version ID.
        """
        pass
```

**Data Models:**

```python
@dataclass
class ABTestConfig:
    config_id: str
    templates: List[str]  # template IDs
    distribution: Dict[str, float]  # template_id -> probability
    start_time: datetime
    end_time: Optional[datetime]

@dataclass
class PerformanceMetrics:
    template_id: str
    template_version: str
    segments_processed: int
    field_extraction_rate: float  # % of expected fields extracted
    action_classification_accuracy: float
    avg_processing_time_ms: float
    avg_confidence_score: float
    error_rate: float
    timestamp: datetime

@dataclass
class ComparisonReport:
    templates: List[str]
    metrics: Dict[str, PerformanceMetrics]
    winner: Optional[str]  # Best performing template
    statistical_significance: float
```

### 8. Text Response Generator

**Responsibilities:**
- Generate structured text responses from extracted data
- Conform to predefined JSON schema
- Include confidence scores for elements
- Associate responses with source segments

**Interfaces:**

```python
class TextResponseGenerator:
    def generate_response(self, extracted_data: Dict[str, Any], 
                         sop_mapping: SOPMapping) -> TextResponse:
        """
        Generate structured text response from extracted data.
        """
        pass
    
    def validate_schema(self, response: TextResponse) -> bool:
        """
        Validate response against predefined JSON schema.
        """
        pass
    
    def add_confidence_scores(self, response: TextResponse, 
                             confidence_data: Dict[str, float]) -> TextResponse:
        """
        Add confidence scores to response elements.
        """
        pass
```

**Data Models:**

```python
@dataclass
class TextResponse:
    response_id: str
    agent_id: str
    control_id: str
    timestamp: datetime
    actions: List[Dict[str, Any]]
    data_values: Dict[str, Any]
    validation_outcomes: List[Dict[str, Any]]
    decision_paths: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    source_segments: List[str]  # segment IDs
    schema_version: str
```

## Data Models

### Core Domain Models

```python
@dataclass
class VideoReference:
    video_id: str
    agent_id: str
    control_id: str
    start_time: datetime
    end_time: datetime
    file_path: str
    format: str
    size_bytes: int
    frame_rate: float

@dataclass
class Control:
    control_id: str
    name: str
    description: str
    sop_definition: SOPDefinition
    assigned_agents: List[str]

@dataclass
class QAAgent:
    agent_id: str
    name: str
    machine_id: str
    assigned_controls: List[str]
    skan_agent_version: str
    status: str
```

### Storage Schema

The system uses a multi-tier storage approach:

1. **Hot Storage** (Recent data, < 30 days):
   - Raw video streams
   - Video segments
   - VLM responses
   - Extracted data
   - Process maps

2. **Warm Storage** (30-90 days):
   - Compressed video
   - Text responses
   - Process maps
   - Metrics

3. **Cold Storage** (> 90 days):
   - Archived video (compressed)
   - Historical metrics
   - Audit logs

**Query Indexes:**
- agent_id + timestamp
- control_id + timestamp
- sop_item_sequence + timestamp
- confidence_score (for quality filtering)
- prompt_template_version (for A/B test analysis)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified several areas where properties can be consolidated to eliminate redundancy:

1. **Metadata Completeness Properties**: Multiple properties check that different data structures have complete metadata (segments, nodes, responses). These can be consolidated into fewer, more comprehensive properties.

2. **Extraction Completeness Properties**: Properties 3.2, 3.6, 4.4, and 8.4 all verify that extracted data has required fields. These can be combined into a single comprehensive extraction completeness property.

3. **Format Compatibility Properties**: Properties 1.6 and 6.5 both deal with format compatibility and serialization. The round-trip property (6.5) subsumes the format compatibility check (1.6).

4. **Validation Properties**: Properties 3.5, 7.2, and 8.3 all validate data structures against schemas. These can be consolidated into a single schema validation property.

5. **Flagging Properties**: Properties 5.4, 9.1, and 9.2 all deal with flagging items for review based on different criteria. These can be combined into a comprehensive flagging property.

The following properties represent the consolidated, non-redundant set that provides comprehensive validation coverage.

### Core Properties

**Property 1: Connection Establishment**

*For any* SKAN agent configuration, when the agent is installed on a QA machine, the O2A Pipeline should successfully establish a connection to receive video streams.

**Validates: Requirements 1.1**

---

**Property 2: Frame Capture Rate**

*For any* active video stream, the O2A Pipeline should capture frames at a rate of at least 1 frame per second.

**Validates: Requirements 1.2**

---

**Property 3: Network Resilience**

*For any* video stream experiencing network interruption, the O2A Pipeline should buffer frames locally and successfully resume transmission when connectivity is restored, with no frame loss.

**Validates: Requirements 1.3**

---

**Property 4: Frame Timestamp Precision**

*For any* received video frame, the O2A Pipeline should assign a timestamp with millisecond precision (timestamp granularity ≤ 1ms).

**Validates: Requirements 1.5**

---

**Property 5: Segmentation Occurrence**

*For any* video stream, the O2A Pipeline should segment it into one or more video segments based on detected activity changes.

**Validates: Requirements 2.1**

---

**Property 6: Confidence Threshold Enforcement**

*For any* segment boundary detection, the O2A Pipeline should only create boundaries when visual change detection confidence is at least 0.85.

**Validates: Requirements 2.2**

---

**Property 7: Segment Metadata Completeness**

*For any* created video segment, it should include complete temporal metadata: start_time, end_time, and duration_seconds.

**Validates: Requirements 2.3**

---

**Property 8: Frame Continuity Invariant**

*For any* video that is segmented, the total number of frames across all segments should equal the number of frames in the original video (no frames lost or duplicated).

**Validates: Requirements 2.4**

---

**Property 9: Maximum Segment Duration**

*For any* video segment without detected activity change, if its duration reaches 60 seconds, the O2A Pipeline should create a new segment boundary.

**Validates: Requirements 2.5**

---

**Property 10: VLM Submission with Prompt**

*For any* video segment ready for processing, the O2A Pipeline should submit it to Gemini VLM with the configured prompt template.

**Validates: Requirements 3.1**

---

**Property 11: Retry with Exponential Backoff**

*For any* VLM processing failure, the O2A Pipeline should retry up to 3 times with exponential backoff (delays: 1s, 2s, 4s).

**Validates: Requirements 3.3**

---

**Property 12: Schema Validation**

*For any* data structure (VLM response, text response, prompt template), the O2A Pipeline should validate it against its predefined schema before storage or use.

**Validates: Requirements 3.5, 7.2, 8.3**

---

**Property 13: Extraction Completeness**

*For any* VLM response, the O2A Pipeline should extract all required data types (actions, screen text, form fields, decision outcomes) and tag each element with a data source tag, confidence score, and target information.

**Validates: Requirements 3.2, 3.6, 4.4, 8.4**

---

**Property 14: Action Type Identification**

*For any* video segment, the O2A Pipeline should identify all discrete user actions including mouse clicks, keyboard input, form submissions, and navigation events.

**Validates: Requirements 4.1**

---

**Property 15: Action Classification**

*For any* identified action, the O2A Pipeline should classify it into one of the predefined categories (data_entry, validation_check, navigation, error_handling, approval).

**Validates: Requirements 4.2**

---

**Property 16: Temporal Ordering Preservation**

*For any* sequence of actions occurring in rapid succession, the O2A Pipeline should maintain their temporal ordering with millisecond precision.

**Validates: Requirements 4.3**

---

**Property 17: Data Entry Value Extraction**

*For any* action classified as data_entry, the O2A Pipeline should extract the entered value and associate it with the target field.

**Validates: Requirements 4.5**

---

**Property 18: SOP Action Matching**

*For any* extracted action and SOP definition, the O2A Pipeline should attempt to match the action to a corresponding SOP questionnaire item based on action type and context.

**Validates: Requirements 5.1**

---

**Property 19: Validation Point Decision Extraction**

*For any* identified validation point, the O2A Pipeline should extract both the yes/no decision and the corresponding instruction path that was followed.

**Validates: Requirements 5.2**

---

**Property 20: Sequence Number Identification**

*For any* action matched to an SOP questionnaire item, the O2A Pipeline should identify and record the sequence number (S.No) of that item.

**Validates: Requirements 5.3**

---

**Property 21: Unmapped Action Flagging**

*For any* action that cannot be matched to a known SOP questionnaire item, the O2A Pipeline should flag it as unmapped for review.

**Validates: Requirements 5.4**

---

**Property 22: Hierarchical Relationship Preservation**

*For any* SOP mapping with parent-child questionnaire items, the O2A Pipeline should maintain the hierarchical relationships between items and their validation outcomes.

**Validates: Requirements 5.5**

---

**Property 23: Process Map Generation**

*For any* complete set of analyzed video segments representing a full process execution, the O2A Pipeline should generate a process map.

**Validates: Requirements 6.1**

---

**Property 24: Process Map Node Completeness**

*For any* generated process map, it should include nodes for all identified actions, decision points, and validation checks from the source data.

**Validates: Requirements 6.2**

---

**Property 25: Process Map Edge Completeness**

*For any* generated process map, it should include edges representing the flow between all consecutive steps, with labels indicating conditions or triggers where applicable.

**Validates: Requirements 6.3**

---

**Property 26: Decision Path Representation**

*For any* decision point in a process map, both the yes and no paths should be represented with their respective subsequent actions.

**Validates: Requirements 6.4**

---

**Property 27: Process Map Serialization Round-Trip**

*For any* generated process map, serializing it to JSON or GraphML and then deserializing should produce an equivalent process map structure.

**Validates: Requirements 6.5, 1.6**

---

**Property 28: Node Metadata Completeness**

*For any* node in a process map, it should include complete metadata: timestamp, duration, extracted data values, and data source tags.

**Validates: Requirements 6.6**

---

**Property 29: Prompt Template Configuration**

*For any* prompt template modification, the changes should take effect without requiring code changes or system restart.

**Validates: Requirements 7.1**

---

**Property 30: A/B Test Distribution**

*For any* A/B test configuration with multiple prompt templates and distribution ratios, when processing a large number of segments (n ≥ 1000), the actual assignment distribution should be within 5% of the configured distribution.

**Validates: Requirements 7.3**

---

**Property 31: Template Metrics Tracking**

*For any* video segment processed with a specific prompt template, the O2A Pipeline should track and store performance metrics (field extraction rate, accuracy, processing time) associated with that template version.

**Validates: Requirements 7.4, 7.5**

---

**Property 32: Template Versioning**

*For any* prompt template update, the O2A Pipeline should create a new version while preserving historical performance data for the previous version.

**Validates: Requirements 7.6**

---

**Property 33: Text Response Structure Completeness**

*For any* generated text response, it should include all required sections: identified actions, extracted data values, validation outcomes, decision paths, and timestamps.

**Validates: Requirements 8.1, 8.2**

---

**Property 34: Source Association**

*For any* generated text response, it should be associated with references to its source video segments and raw video files.

**Validates: Requirements 8.5**

---

**Property 35: Quality-Based Flagging**

*For any* video segment with insufficient quality (low resolution, excessive blur, poor lighting) or extraction with confidence below 0.7 for critical fields, the O2A Pipeline should flag it for manual review or human verification.

**Validates: Requirements 9.1, 9.2**

---

**Property 36: Failure Logging and Notification**

*For any* processing failure after all retry attempts, the O2A Pipeline should log the failure with diagnostic information and send a notification to system operators.

**Validates: Requirements 9.3**

---

**Property 37: Audit Log Completeness**

*For any* processing attempt, the O2A Pipeline should create an audit log entry containing timestamp, prompt version, and outcome.

**Validates: Requirements 9.4**

---

**Property 38: Anomaly Detection**

*For any* sequence of extracted actions that is inconsistent with the expected SOP flow, the O2A Pipeline should generate an anomaly alert.

**Validates: Requirements 9.5**

---

**Property 39: Rate Limiting Compliance**

*For any* sequence of Gemini VLM API calls, the O2A Pipeline should enforce rate limiting to stay within configured quota limits.

**Validates: Requirements 10.3**

---

**Property 40: Queue Prioritization**

*For any* processing queue that exceeds capacity thresholds, the O2A Pipeline should prioritize video segments according to configured business rules.

**Validates: Requirements 10.4**

---

**Property 41: Multi-Type Storage**

*For any* data artifact (raw video, segment, text response, process map), the O2A Pipeline should store it in the queryable data store and make it retrievable.

**Validates: Requirements 11.1**

---

**Property 42: Retention Policy Enforcement**

*For any* video data older than 90 days, the O2A Pipeline should archive it to cold storage according to retention policies.

**Validates: Requirements 11.2**

---

**Property 43: Query Support**

*For any* stored data, the O2A Pipeline should support querying by agent_id, control_id, timestamp range, SOP questionnaire item, and extraction confidence.

**Validates: Requirements 11.3**

---

**Property 44: Compression Effectiveness**

*For any* raw video stored, the O2A Pipeline should compress it to achieve at least 60% size reduction.

**Validates: Requirements 11.5**

---

**Property 45: Agent Registration**

*For any* newly provisioned QA agent machine, the O2A Pipeline should automatically register it with Google ADK.

**Validates: Requirements 12.2**

---

**Property 46: Authentication Usage**

*For any* Google ADK API interaction, the O2A Pipeline should use Google ADK authentication and authorization mechanisms.

**Validates: Requirements 12.3**

---

**Property 47: Configuration Synchronization**

*For any* agent configuration change in Google ADK, the O2A Pipeline should synchronize the change within 60 seconds.

**Validates: Requirements 12.4**

---

**Property 48: Health Status Reporting**

*For any* change in agent health status or video stream availability, the O2A Pipeline should report it to Google ADK monitoring dashboards.

**Validates: Requirements 12.5**

## Error Handling

### Error Categories

The O2A Pipeline handles errors across multiple categories:

1. **Network Errors**
   - Connection failures to SKAN agents
   - Network interruptions during video streaming
   - API connectivity issues with Gemini VLM or Google ADK
   - **Handling**: Automatic retry with exponential backoff, local buffering, circuit breaker pattern

2. **Data Quality Errors**
   - Insufficient video quality for analysis
   - Low confidence scores in VLM extraction
   - Missing or corrupted video frames
   - **Handling**: Flag for manual review, log quality metrics, alert operators

3. **Processing Errors**
   - VLM API failures or timeouts
   - Schema validation failures
   - Segmentation algorithm failures
   - **Handling**: Retry up to 3 times, log diagnostic information, fallback to manual processing queue

4. **Resource Errors**
   - Storage capacity exceeded
   - Processing queue overflow
   - API quota limits reached
   - **Handling**: Apply prioritization rules, scale resources, throttle ingestion, alert operators

5. **Integration Errors**
   - Google ADK API failures
   - Authentication/authorization failures
   - Configuration synchronization failures
   - **Handling**: Retry with backoff, use cached configuration, alert operators

### Error Recovery Strategies

**Retry Logic**:
```python
def retry_with_exponential_backoff(operation, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return operation()
        except RetryableError as e:
            if attempt == max_attempts - 1:
                raise
            delay = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(delay)
            log_retry(operation, attempt, delay)
```

**Circuit Breaker**:
- Open circuit after 5 consecutive failures
- Half-open state after 30 seconds
- Close circuit after 3 successful calls
- Prevents cascading failures to downstream services

**Graceful Degradation**:
- Continue processing other segments when one fails
- Use cached SOP definitions if mapping service unavailable
- Generate partial process maps when some data is missing
- Maintain service availability even with component failures

### Monitoring and Alerting

**Critical Alerts** (immediate operator notification):
- VLM API failure rate > 10%
- Processing queue depth > 10,000 segments
- Storage capacity > 90%
- Agent connection failure rate > 5%

**Warning Alerts** (logged for review):
- Low confidence extractions > 20% of segments
- Unmapped actions > 15% of total actions
- Segmentation quality degradation
- Anomaly detection rate increase

## Testing Strategy

The O2A Ingestion Pipeline requires comprehensive testing across multiple dimensions to ensure correctness, reliability, and performance. We employ a dual testing approach combining unit tests for specific scenarios and property-based tests for universal correctness guarantees.

### Testing Approach

**Unit Tests**: Validate specific examples, edge cases, and error conditions
- Specific video formats and resolutions
- Known SOP questionnaire structures
- Error scenarios (network failures, API errors)
- Integration points between components
- Edge cases (empty videos, single-frame segments, malformed data)

**Property-Based Tests**: Verify universal properties across all inputs
- Generate random video streams, segments, and actions
- Test properties hold for all valid inputs
- Minimum 100 iterations per property test
- Each test references its design document property

### Property-Based Testing Configuration

**Framework**: Use Hypothesis (Python) for property-based testing

**Test Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(video_stream=st.video_streams(), agent_config=st.agent_configs())
def test_connection_establishment(video_stream, agent_config):
    """
    Feature: o2a-ingestion-pipeline, Property 1: Connection Establishment
    For any SKAN agent configuration, when the agent is installed on a QA machine,
    the O2A Pipeline should successfully establish a connection to receive video streams.
    """
    pipeline = O2APipeline()
    handle = pipeline.accept_stream(agent_config.agent_id, video_stream)
    assert handle is not None
    assert handle.agent_id == agent_config.agent_id
    assert pipeline.get_stream_status(agent_config.agent_id).is_active
```

**Custom Generators**:
```python
# Strategy for generating video streams
@st.composite
def video_streams(draw):
    frame_rate = draw(st.floats(min_value=1.0, max_value=60.0))
    duration = draw(st.integers(min_value=1, max_value=300))
    resolution = draw(st.sampled_from([(640, 480), (1280, 720), (1920, 1080)]))
    return VideoStream(frame_rate=frame_rate, duration=duration, resolution=resolution)

# Strategy for generating actions
@st.composite
def actions(draw):
    category = draw(st.sampled_from(list(ActionCategory)))
    target = draw(st.text(min_size=1, max_size=50))
    value = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    timestamp = draw(st.datetimes())
    return Action(category=category, target=target, value=value, timestamp=timestamp)

# Strategy for generating SOP definitions
@st.composite
def sop_definitions(draw):
    num_items = draw(st.integers(min_value=1, max_value=20))
    items = [draw(questionnaire_items()) for _ in range(num_items)]
    return SOPDefinition(sop_id=draw(st.uuids()), questionnaire_items=items)
```

### Test Coverage Requirements

**Component-Level Tests**:
- Ingestion Service: Connection handling, buffering, storage
- Segmentation Service: Activity detection, boundary creation, continuity
- VLM Processing Service: API interaction, retry logic, validation
- Extraction Service: Action identification, classification, data extraction
- SOP Mapping Service: Action matching, validation point extraction, flagging
- Process Map Generator: Graph construction, serialization, metadata
- Prompt Engineering Framework: Template management, A/B testing, metrics

**Integration Tests**:
- End-to-end pipeline flow from video ingestion to process map generation
- Google ADK integration for agent management
- Gemini VLM API integration for video processing
- Storage layer integration for data persistence and retrieval

**Performance Tests**:
- Concurrent stream handling (4000+ agents)
- Processing throughput (800+ segments/minute)
- Query latency (< 2 seconds for 30-day queries)
- Compression effectiveness (≥ 60% reduction)

### Test Data Management

**Synthetic Data Generation**:
- Generate realistic video streams with known actions
- Create SOP definitions with various complexity levels
- Produce VLM responses with controlled confidence scores
- Build process execution scenarios with decision paths

**Test Fixtures**:
- Sample video files in multiple formats
- Reference SOP questionnaires from production
- Known-good process maps for validation
- Error scenarios and edge cases

### Continuous Testing

**Pre-commit Tests**:
- Unit tests for modified components
- Fast property tests (10 iterations)
- Linting and type checking

**CI/CD Pipeline Tests**:
- Full unit test suite
- Property tests (100 iterations)
- Integration tests
- Performance regression tests

**Production Monitoring**:
- Continuous validation of extraction accuracy
- A/B test metric collection
- Anomaly detection validation
- SLA compliance monitoring
