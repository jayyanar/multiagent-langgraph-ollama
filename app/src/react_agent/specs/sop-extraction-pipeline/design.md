# Design Document: SOP Extraction Pipeline

## Overview

The SOP Extraction Pipeline is a multi-stage data processing system that transforms raw Standard Operating Procedure documents into standardized, machine-readable formats optimized for LLM and agent consumption. The system processes unstructured SOP data from the O2A Ingestion Pipeline, extracting questionnaire structures, validation rules, and decision logic, then enriching and formatting this data for downstream automation systems.

### Design Philosophy

The pipeline follows a modular, pipeline-based architecture where each stage performs a specific transformation:
1. **Parsing**: Extract structured data from raw inputs
2. **Normalization**: Enforce consistent schema
3. **Enrichment**: Add metadata and confidence scores
4. **Validation**: Verify completeness and consistency
5. **Formatting**: Optimize for LLM consumption
6. **Versioning**: Track changes and maintain history

This separation of concerns enables independent optimization of each stage and supports experimentation with different formatting approaches without affecting upstream processing.

### Key Design Decisions

**Schema-First Approach**: We define a canonical SOP schema that all processing stages target, ensuring consistency across the pipeline.

**Multi-Format Support**: The system generates multiple output formats (JSON, YAML, Markdown) from a single internal representation, allowing different downstream consumers to use their preferred format.

**Confidence Scoring**: Each extracted element receives a confidence score based on extraction quality, enabling downstream systems to make risk-based decisions.

**Version Immutability**: Once created, SOP versions are immutable. Changes create new versions with full lineage tracking.

## Architecture

### System Context

```
┌─────────────────────┐
│ O2A Ingestion       │
│ Pipeline            │
│ (Text + Process     │
│  Maps)              │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│         SOP Extraction Pipeline                     │
│                                                     │
│  ┌──────┐  ┌────────┐  ┌──────────┐  ┌─────────┐ │
│  │Parser├─►│Normaliz├─►│Enrichment├─►│Validator│ │
│  └──────┘  │er      │  │Engine    │  └────┬────┘ │
│            └────────┘  └──────────┘       │      │
│                                            ▼      │
│            ┌──────────┐  ┌──────────────────┐    │
│            │Version   │◄─┤Format Optimizer  │    │
│            │Manager   │  └──────────────────┘    │
│            └────┬─────┘                           │
└─────────────────┼─────────────────────────────────┘
                  │
                  ▼
       ┌──────────────────────────────┐
       │  Downstream Systems          │
       │  - LLM Agents (Google ADK)   │
       │  - Automation Systems        │
       │  - Training Systems          │
       └──────────────────────────────┘
```

### Component Architecture

The pipeline consists of six primary components that process SOP data sequentially:

**1. Parser**
- Receives raw SOP documents from O2A Ingestion Pipeline
- Extracts structured elements using pattern matching and NLP
- Handles both text-based responses and process map data
- Outputs: Raw structured data with source attribution

**2. Normalizer (Schema_Validator - Normalization Mode)**
- Enforces canonical SOP schema
- Converts extracted data into standard format
- Resolves format variations and inconsistencies
- Outputs: Schema-compliant SOP structure

**3. Enrichment Engine**
- Adds metadata (timestamps, version IDs, lineage)
- Calculates confidence scores for extracted elements
- Identifies and links dependencies between questionnaire items
- Normalizes data source tags to standard taxonomy
- Outputs: Enriched SOP with metadata

**4. Validator (Schema_Validator - Validation Mode)**
- Verifies completeness of questionnaire items
- Checks consistency of validation rules and decision trees
- Validates data source references against registry
- Generates quality reports with metrics
- Outputs: Validated SOP + validation report

**5. Format Optimizer**
- Generates multiple output formats (JSON, YAML, Markdown)
- Creates LLM-optimized prompt templates
- Supports A/B testing with format variations
- Calculates format metrics (token count, complexity)
- Outputs: Multi-format SOP representations

**6. Version Manager**
- Assigns unique version identifiers
- Stores immutable SOP versions
- Maintains version lineage and change history
- Supports version retrieval and comparison
- Outputs: Versioned SOP + change metadata

### Data Flow

```
Raw SOP Document
    ↓
[Parser] → Extract questionnaire items, validation rules, instructions
    ↓
Raw Structured Data
    ↓
[Normalizer] → Apply canonical schema, resolve inconsistencies
    ↓
Schema-Compliant SOP
    ↓
[Enrichment Engine] → Add metadata, confidence scores, dependencies
    ↓
Enriched SOP
    ↓
[Validator] → Check completeness, consistency, data sources
    ↓
Validated SOP + Report
    ↓
[Format Optimizer] → Generate JSON, YAML, Markdown, prompt templates
    ↓
Multi-Format Output
    ↓
[Version Manager] → Assign version, store immutably
    ↓
Versioned SOP → Downstream Systems
```

## Components and Interfaces

### Parser Component

**Responsibilities:**
- Extract structured data from raw SOP documents
- Handle multiple input formats (text responses, process maps)
- Preserve source attribution for traceability
- Log extraction issues with location references

**Interface:**
```python
class Parser:
    def parse_document(self, raw_document: RawSOPDocument) -> ParsedSOP:
        """
        Parse raw SOP document into structured format.
        
        Args:
            raw_document: Raw SOP from O2A Ingestion Pipeline
            
        Returns:
            ParsedSOP with extracted elements and source attribution
        """
        pass
    
    def parse_text_response(self, text: str) -> List[QuestionnaireItem]:
        """Extract questionnaire items from text-based SOP."""
        pass
    
    def parse_process_map(self, process_map: ProcessMapData) -> DecisionTree:
        """Convert process map into decision tree structure."""
        pass
    
    def extract_data_source_tags(self, text: str) -> List[DataSourceTag]:
        """Extract and normalize data source references."""
        pass
```

**Key Algorithms:**
- Pattern matching for questionnaire structure (S.No, Question, Validation, Instructions)
- NLP-based extraction for unstructured text sections
- Graph traversal for process map conversion to decision trees
- Regex-based extraction for data source tags (🔎 Data Sources: SystemName)

### Schema Validator Component

**Responsibilities:**
- Enforce canonical SOP schema (normalization mode)
- Validate completeness and consistency (validation mode)
- Generate validation reports with quality metrics
- Check data source references against registry

**Interface:**
```python
class SchemaValidator:
    def normalize(self, parsed_sop: ParsedSOP) -> NormalizedSOP:
        """
        Apply canonical schema to parsed SOP data.
        
        Args:
            parsed_sop: Raw structured data from Parser
            
        Returns:
            NormalizedSOP conforming to canonical schema
        """
        pass
    
    def validate_completeness(self, sop: NormalizedSOP) -> ValidationReport:
        """Check that all required fields are present."""
        pass
    
    def validate_consistency(self, sop: NormalizedSOP) -> ValidationReport:
        """Check for logical conflicts in validation rules."""
        pass
    
    def validate_data_sources(self, sop: NormalizedSOP, 
                             registry: DataSourceRegistry) -> ValidationReport:
        """Verify data source references exist and are accessible."""
        pass
```

**Canonical SOP Schema:**
```python
@dataclass
class QuestionnaireItem:
    s_no: str  # Sequential number (e.g., "1", "2.1")
    question: str  # Question text
    validation_type: str  # "Yes/No", "Multiple Choice", etc.
    instructions: Dict[str, Instruction]  # Keyed by validation outcome
    data_sources: List[DataSourceTag]
    confidence_score: float
    metadata: ItemMetadata

@dataclass
class Instruction:
    text: str
    data_sources: List[DataSourceTag]
    next_item: Optional[str]  # S.No of next question (for branching)

@dataclass
class DecisionTree:
    root_node: DecisionNode
    nodes: Dict[str, DecisionNode]

@dataclass
class DecisionNode:
    node_id: str
    question_ref: str  # References QuestionnaireItem.s_no
    branches: Dict[str, str]  # Outcome → next node_id
    is_terminal: bool

@dataclass
class SOPDocument:
    document_id: str
    version: str
    questionnaire_items: List[QuestionnaireItem]
    decision_tree: DecisionTree
    metadata: DocumentMetadata
```

### Enrichment Engine Component

**Responsibilities:**
- Calculate confidence scores for extracted elements
- Add metadata (timestamps, version IDs, processing lineage)
- Identify dependencies between questionnaire items
- Normalize data source tags to standard taxonomy

**Interface:**
```python
class EnrichmentEngine:
    def enrich(self, normalized_sop: NormalizedSOP) -> EnrichedSOP:
        """
        Add metadata and confidence scores to normalized SOP.
        
        Args:
            normalized_sop: Schema-compliant SOP from Normalizer
            
        Returns:
            EnrichedSOP with metadata and confidence scores
        """
        pass
    
    def calculate_confidence_score(self, item: QuestionnaireItem) -> float:
        """
        Calculate confidence score based on extraction quality.
        
        Factors:
        - Completeness of fields
        - Clarity of validation rules
        - Availability of data sources
        - Consistency with related items
        """
        pass
    
    def identify_dependencies(self, items: List[QuestionnaireItem]) -> DependencyGraph:
        """Identify which items reference or depend on others."""
        pass
    
    def normalize_data_source_tags(self, tags: List[DataSourceTag], 
                                   taxonomy: DataSourceTaxonomy) -> List[DataSourceTag]:
        """Map data source names to standard taxonomy."""
        pass
```

**Confidence Score Calculation:**
```
confidence_score = weighted_average([
    completeness_score,  # All required fields present
    clarity_score,       # Validation rules are unambiguous
    data_source_score,   # Data sources identified and accessible
    consistency_score    # No conflicts with related items
])

Weights: [0.3, 0.3, 0.2, 0.2]
```

### Format Optimizer Component

**Responsibilities:**
- Generate multiple output formats from single internal representation
- Create LLM-optimized prompt templates
- Support A/B testing with format variations
- Calculate format metrics (token count, structural complexity)

**Interface:**
```python
class FormatOptimizer:
    def generate_json(self, sop: EnrichedSOP) -> str:
        """Generate JSON representation."""
        pass
    
    def generate_yaml(self, sop: EnrichedSOP) -> str:
        """Generate YAML representation."""
        pass
    
    def generate_markdown(self, sop: EnrichedSOP) -> str:
        """Generate human-readable Markdown."""
        pass
    
    def generate_llm_prompt(self, sop: EnrichedSOP, 
                           template: PromptTemplate) -> str:
        """Generate LLM-optimized prompt using template."""
        pass
    
    def apply_format_template(self, sop: EnrichedSOP, 
                             template: FormatTemplate) -> FormattedSOP:
        """Apply custom format template for experimentation."""
        pass
    
    def calculate_format_metrics(self, formatted_sop: FormattedSOP) -> FormatMetrics:
        """Calculate token count, complexity, readability scores."""
        pass
```

**LLM Prompt Template Structure:**
```
System Context:
- Role definition for LLM agent
- SOP purpose and scope

Questionnaire Items:
For each item:
  - Question number and text
  - Validation type and options
  - Instructions for each outcome
  - Data sources required
  - Confidence level

Decision Logic:
- Conditional branching rules
- Terminal conditions
- Error handling paths

Output Format:
- Expected response structure
- Validation criteria
```

### Version Manager Component

**Responsibilities:**
- Assign unique version identifiers with timestamps
- Store immutable SOP versions
- Maintain version lineage and change history
- Support version retrieval, comparison, and rollback

**Interface:**
```python
class VersionManager:
    def create_version(self, sop: FormattedSOP, 
                      change_description: str) -> VersionedSOP:
        """
        Create new immutable version of SOP.
        
        Args:
            sop: Formatted SOP from Format Optimizer
            change_description: Human-readable description of changes
            
        Returns:
            VersionedSOP with unique identifier and lineage
        """
        pass
    
    def get_version(self, version_id: str) -> VersionedSOP:
        """Retrieve specific version by ID."""
        pass
    
    def get_latest_version(self, document_id: str) -> VersionedSOP:
        """Retrieve most recent version of document."""
        pass
    
    def compare_versions(self, version_id_1: str, 
                        version_id_2: str) -> VersionDiff:
        """Generate diff report between two versions."""
        pass
    
    def apply_incremental_update(self, version_id: str, 
                                update: PartialUpdate) -> VersionedSOP:
        """Apply partial update to create new version."""
        pass
```

**Version Identifier Format:**
```
{document_id}-v{major}.{minor}.{patch}-{timestamp}

Example: sop-qa-claims-v1.2.3-20250119T143022Z
```

## Data Models

### Core Data Structures

**RawSOPDocument** (Input from O2A Ingestion Pipeline)
```python
@dataclass
class RawSOPDocument:
    document_id: str
    source_type: str  # "text_response" or "process_map"
    content: Union[str, ProcessMapData]
    metadata: Dict[str, Any]
    timestamp: datetime
```

**ParsedSOP** (Output from Parser)
```python
@dataclass
class ParsedSOP:
    document_id: str
    raw_items: List[RawQuestionnaireItem]
    raw_decision_tree: Optional[RawDecisionTree]
    extraction_log: List[ExtractionIssue]
    source_attribution: Dict[str, str]  # Element ID → source location
```

**NormalizedSOP** (Output from Schema Validator - Normalization)
```python
@dataclass
class NormalizedSOP:
    document_id: str
    questionnaire_items: List[QuestionnaireItem]
    decision_tree: DecisionTree
    schema_version: str
    normalization_log: List[str]
```

**EnrichedSOP** (Output from Enrichment Engine)
```python
@dataclass
class EnrichedSOP:
    document_id: str
    questionnaire_items: List[QuestionnaireItem]  # With confidence scores
    decision_tree: DecisionTree
    dependency_graph: DependencyGraph
    metadata: DocumentMetadata
    enrichment_timestamp: datetime
```

**ValidationReport** (Output from Schema Validator - Validation)
```python
@dataclass
class ValidationReport:
    document_id: str
    completeness_score: float  # 0.0 to 1.0
    consistency_score: float
    data_source_score: float
    overall_quality: float
    issues: List[ValidationIssue]
    recommendations: List[str]
```

**FormattedSOP** (Output from Format Optimizer)
```python
@dataclass
class FormattedSOP:
    document_id: str
    format_type: str  # "json", "yaml", "markdown", "llm_prompt"
    content: str
    format_metrics: FormatMetrics
    template_id: Optional[str]
```

**VersionedSOP** (Output from Version Manager)
```python
@dataclass
class VersionedSOP:
    version_id: str
    document_id: str
    formatted_sop: FormattedSOP
    parent_version_id: Optional[str]
    change_description: str
    created_at: datetime
    created_by: str
```

### Supporting Data Structures

**QuestionnaireItem**
```python
@dataclass
class QuestionnaireItem:
    s_no: str
    question: str
    validation_type: str
    instructions: Dict[str, Instruction]
    data_sources: List[DataSourceTag]
    confidence_score: float
    dependencies: List[str]  # S.No of dependent items
    metadata: ItemMetadata

@dataclass
class Instruction:
    text: str
    data_sources: List[DataSourceTag]
    next_item: Optional[str]
    action_type: str  # "continue", "terminate", "branch"

@dataclass
class ItemMetadata:
    extraction_method: str
    source_location: str
    last_updated: datetime
    update_count: int
```

**DecisionTree**
```python
@dataclass
class DecisionTree:
    root_node_id: str
    nodes: Dict[str, DecisionNode]
    terminal_nodes: List[str]

@dataclass
class DecisionNode:
    node_id: str
    question_ref: str
    branches: Dict[str, str]  # Outcome → next node_id
    is_terminal: bool
    terminal_action: Optional[str]
```

**DataSourceTag**
```python
@dataclass
class DataSourceTag:
    system_name: str  # Normalized name (e.g., "Claim2", "Pega_Call_Notes")
    original_name: str  # As extracted from source
    access_method: str  # "api", "database", "file"
    is_accessible: bool
    confidence: float
```

**DependencyGraph**
```python
@dataclass
class DependencyGraph:
    nodes: Dict[str, DependencyNode]
    edges: List[DependencyEdge]

@dataclass
class DependencyNode:
    item_s_no: str
    depends_on: List[str]
    depended_by: List[str]

@dataclass
class DependencyEdge:
    from_item: str
    to_item: str
    dependency_type: str  # "data", "logic", "sequence"
```

**FormatMetrics**
```python
@dataclass
class FormatMetrics:
    token_count: int
    structural_complexity: float  # Based on nesting depth
    readability_score: float  # Based on text analysis
    llm_compatibility_score: float  # Based on format best practices
```

**PromptTemplate**
```python
@dataclass
class PromptTemplate:
    template_id: str
    name: str
    system_context: str
    item_format: str  # Template for formatting each questionnaire item
    decision_logic_format: str
    output_format: str
    metadata: Dict[str, Any]
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Extraction Completeness

*For any* raw SOP document from O2A Ingestion Pipeline, when the Parser processes it, all questionnaire items with their S.No, question text, validation type, and instructions should be present in the parsed output.

**Validates: Requirements 1.1, 1.2, 8.1**

### Property 2: Process Map Conversion Preserves Logic

*For any* process map with workflow nodes and decision points, when the Parser converts it to a decision tree, all conditional branches and transition conditions should be preserved in the tree structure.

**Validates: Requirements 1.3, 8.2**

### Property 3: Data Source Tag Extraction

*For any* SOP document containing data source tags (e.g., 🔎 Data Sources: Claim2), when the Parser extracts them, all tags should be identified and normalized to standard format.

**Validates: Requirements 1.4**

### Property 4: Parser Error Resilience

*For any* raw SOP document with malformed sections, when the Parser processes it, the Parser should log all issues with location references and continue processing valid sections without crashing.

**Validates: Requirements 1.5**

### Property 5: Schema Enforcement

*For any* parsed SOP, when the Schema_Validator normalizes it, the output should conform to the canonical schema with all required fields (questionnaire items, validation rules, decision trees, metadata) present and properly structured.

**Validates: Requirements 2.1, 2.2**

### Property 6: Decision Path Completeness

*For any* validation rule in a normalized SOP, each possible outcome (Yes/No or multiple choice options) should have associated instructions defining the next action.

**Validates: Requirements 2.3**

### Property 7: Decision Tree Logic Preservation

*For any* decision tree before and after normalization, the conditional logic and branching paths should be equivalent (same reachable outcomes from same inputs).

**Validates: Requirements 2.4**

### Property 8: Validation Error Reporting

*For any* SOP with schema violations, when the Schema_Validator detects them, the validation report should contain specific error locations and suggested corrections for each violation.

**Validates: Requirements 2.5**

### Property 9: Metadata Enrichment Completeness

*For any* normalized SOP, when the Enrichment_Engine processes it, the output should contain all required metadata fields: data source tags, timestamps, version identifiers, processing lineage, and source attribution for each element.

**Validates: Requirements 3.1, 3.5, 8.5**

### Property 10: Confidence Score Calculation

*For any* questionnaire item, when the Enrichment_Engine calculates its confidence score, the score should reflect extraction completeness, data source availability, validation rule clarity, and consistency with related items according to the weighted formula.

**Validates: Requirements 3.2**

### Property 11: Dependency Graph Accuracy

*For any* set of questionnaire items with references between them, when the Enrichment_Engine identifies dependencies, the dependency graph should correctly represent all "depends on" and "depended by" relationships.

**Validates: Requirements 3.3**

### Property 12: Data Source Name Normalization

*For any* data source reference with variations in naming (e.g., "Claim 2", "claim2", "Claim2"), when the Enrichment_Engine normalizes it, the output should use the standard taxonomy name consistently.

**Validates: Requirements 3.4**

### Property 13: Completeness Validation Detection

*For any* SOP with missing elements (questionnaire items without validation rules, decision branches without outcomes, or items referencing external data without source tags), when the Schema_Validator checks completeness, all missing elements should be detected and reported.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 14: Consistency Conflict Detection

*For any* SOP with logically inconsistent validation rules between related questionnaire items, when the Schema_Validator checks consistency, all conflicts should be identified and reported.

**Validates: Requirements 4.4**

### Property 15: Quality Report Structure

*For any* validated SOP, the completeness report should contain percentage scores for each section, overall quality metrics, and lists of issues and recommendations.

**Validates: Requirements 4.5, 10.4, 11.5**

### Property 16: Output Format Validity

*For any* enriched SOP, when the Format_Optimizer generates output, the JSON and YAML formats should be syntactically valid and parseable by standard libraries.

**Validates: Requirements 5.1**

### Property 17: Prompt Template Completeness

*For any* enriched SOP, when the Format_Optimizer creates an LLM prompt template, the template should include system context, questionnaire items with all fields, decision logic, and output format specifications.

**Validates: Requirements 5.2**

### Property 18: Linear Formatting

*For any* questionnaire item, when the Format_Optimizer formats it for LLM consumption, the output should present question, validation rules, and instructions in a sequential order without ambiguous references.

**Validates: Requirements 5.3**

### Property 19: Explicit Conditional Representation

*For any* decision tree, when the Format_Optimizer formats it for LLM consumption, all conditional branches should be represented using explicit if-then-else structures.

**Validates: Requirements 5.4**

### Property 20: Multi-Format Generation

*For any* enriched SOP, when the Format_Optimizer processes it, outputs should be generated in JSON, YAML, and Markdown formats.

**Validates: Requirements 5.5, 11.4**

### Property 21: Template Application Correctness

*For any* format template and enriched SOP, when the Format_Optimizer applies the template, the output should follow the template structure while including all SOP data.

**Validates: Requirements 6.1**

### Property 22: Semantic Preservation During Formatting

*For any* enriched SOP and any format template, when the Format_Optimizer applies the template, all semantic information (questionnaire items, validation rules, decision logic, metadata) should be preserved in the formatted output, even if presentation structure varies.

**Validates: Requirements 6.2**

### Property 23: Format Variation Generation

*For any* enriched SOP, when the Format_Optimizer generates variations for A/B testing, multiple distinct format variations should be produced from the same source data.

**Validates: Requirements 6.3**

### Property 24: Format Metrics Calculation

*For any* formatted SOP, when the Format_Optimizer calculates metrics, the output should include token count, structural complexity, and readability scores.

**Validates: Requirements 6.4**

### Property 25: Format Rule Validation

*For any* custom formatting rule, when the Format_Optimizer validates it, incompatible rules (those that violate the SOP schema) should be rejected before application.

**Validates: Requirements 6.5**

### Property 26: Version Uniqueness and Metadata

*For any* formatted SOP, when the Version_Manager creates a version, the version should have a unique identifier, timestamp, and change description.

**Validates: Requirements 7.1, 12.3**

### Property 27: Version Storage Round-Trip

*For any* formatted SOP, when the Version_Manager stores it as a version and then retrieves it, the retrieved version should be identical to the original (complete document state, metadata, formatting templates).

**Validates: Requirements 7.2**

### Property 28: Version Lineage Preservation

*For any* SOP update, when the Version_Manager detects changes and creates a new version, the new version should maintain a link to its parent version, preserving the complete version history chain.

**Validates: Requirements 7.3**

### Property 29: Version Retrieval Correctness

*For any* stored SOP version, retrieval by version identifier or timestamp should return the correct version with all its data.

**Validates: Requirements 7.4**

### Property 30: Version Diff Accuracy

*For any* two SOP versions, when the Version_Manager compares them, the diff report should correctly identify all changes in questionnaire items, validation rules, and metadata.

**Validates: Requirements 7.5**

### Property 31: Multi-Source Merging with Attribution

*For any* SOP with multiple input sources (text responses and process maps), when the Parser merges them, all information should be preserved with source attribution for each element.

**Validates: Requirements 8.3**

### Property 32: Conflict Detection and Resolution

*For any* SOP with conflicting information between sources, when the Parser processes it, conflicts should be flagged and resolved according to configurable rules.

**Validates: Requirements 8.4**

### Property 33: Data Source Registry Validation

*For any* data source tag, when the Schema_Validator validates it, the validator should correctly identify whether the referenced system exists in the registry and is accessible.

**Validates: Requirements 9.1, 9.2, 9.3**

### Property 34: Data Source Dependency Report Completeness

*For any* SOP, when the Schema_Validator generates a data source dependency report, the report should list all external systems referenced in the SOP.

**Validates: Requirements 9.4**

### Property 35: Data Source Tag Format Validation

*For any* data source tag, when the Schema_Validator validates its format, tags not following the standard pattern (🔎 Data Sources: SystemName) should be flagged.

**Validates: Requirements 9.5**

### Property 36: Batch Processing Independence

*For any* batch of SOP documents, when the Parser processes them, each document should be processed independently (errors in one document should not affect processing of others).

**Validates: Requirements 10.1**

### Property 37: Batch Error Isolation

*For any* batch of SOP documents with some failing documents, when the Parser processes the batch, processing should continue for all documents and all errors should be logged in a consolidated error log.

**Validates: Requirements 10.3**

### Property 38: Batch Completion Notification

*For any* batch of SOP documents, when the Parser completes processing, downstream systems should be notified of available processed documents.

**Validates: Requirements 10.5**

### Property 39: Human-Readable Report Structure

*For any* enriched SOP, when the Format_Optimizer generates a human-readable report, the report should have clear section headings, visual hierarchy, and structured presentation of questionnaire items and decision trees.

**Validates: Requirements 11.1, 11.2, 11.3**

### Property 40: Incremental Update Section Identification

*For any* incremental update request with a section identifier, when the Version_Manager processes it, the correct target section should be identified.

**Validates: Requirements 12.1**

### Property 41: Incremental Update Consistency

*For any* incremental update to an SOP section, when the Version_Manager applies it, the updated section should maintain schema consistency with unchanged sections.

**Validates: Requirements 12.2**

### Property 42: Incremental Update Isolation

*For any* partial update to specific SOP sections (questionnaire items, validation rules, or metadata), when the Version_Manager applies it, unchanged sections should remain identical to the previous version.

**Validates: Requirements 12.4**

### Property 43: Incremental Update Conflict Detection

*For any* incremental update that creates inconsistencies, when the Version_Manager validates it, the update should be rejected with detailed conflict information.

**Validates: Requirements 12.5**


## Error Handling

### Error Categories

The SOP Extraction Pipeline handles four categories of errors:

1. **Input Errors**: Malformed or incomplete raw SOP documents
2. **Processing Errors**: Failures during parsing, normalization, or enrichment
3. **Validation Errors**: Schema violations or consistency issues
4. **System Errors**: External system failures (data source unavailability, storage failures)

### Error Handling Strategy

**Fail-Safe Processing**: The pipeline continues processing valid sections even when encountering errors in specific sections. This ensures maximum data extraction from partially valid inputs.

**Detailed Error Logging**: All errors are logged with:
- Error type and severity level
- Specific location in source document
- Context information (surrounding data)
- Suggested corrections when applicable
- Timestamp and processing stage

**Error Propagation**: Errors are accumulated and reported at the end of each processing stage rather than failing immediately. This provides complete error visibility.

### Error Handling by Component

**Parser Error Handling:**
```python
class ParsingError(Exception):
    error_type: str  # "malformed_structure", "missing_field", "invalid_format"
    location: str    # Line number or section identifier
    context: str     # Surrounding text or data
    severity: str    # "critical", "warning", "info"
    suggestion: Optional[str]

# Parser continues processing and accumulates errors
def parse_document(raw_doc: RawSOPDocument) -> Tuple[ParsedSOP, List[ParsingError]]:
    errors = []
    parsed_items = []
    
    for section in raw_doc.sections:
        try:
            item = parse_section(section)
            parsed_items.append(item)
        except ParsingError as e:
            errors.append(e)
            # Continue with next section
    
    return ParsedSOP(items=parsed_items), errors
```

**Schema Validator Error Handling:**
```python
class ValidationError(Exception):
    error_type: str  # "schema_violation", "missing_field", "inconsistency"
    item_id: str     # Questionnaire item S.No or section ID
    field: str       # Specific field with issue
    expected: Any    # Expected value or format
    actual: Any      # Actual value found
    severity: str

# Validator accumulates all violations before reporting
def validate(sop: NormalizedSOP) -> ValidationReport:
    errors = []
    
    for item in sop.questionnaire_items:
        errors.extend(validate_item_completeness(item))
        errors.extend(validate_item_consistency(item, sop))
    
    errors.extend(validate_decision_tree(sop.decision_tree))
    errors.extend(validate_data_sources(sop, data_source_registry))
    
    return ValidationReport(
        errors=errors,
        completeness_score=calculate_completeness(errors),
        overall_quality=calculate_quality(errors)
    )
```

**Enrichment Engine Error Handling:**
```python
class EnrichmentError(Exception):
    error_type: str  # "metadata_failure", "confidence_calculation_error"
    item_id: str
    details: str

# Enrichment uses default values when calculations fail
def enrich(sop: NormalizedSOP) -> Tuple[EnrichedSOP, List[EnrichmentError]]:
    errors = []
    
    for item in sop.questionnaire_items:
        try:
            item.confidence_score = calculate_confidence_score(item)
        except Exception as e:
            errors.append(EnrichmentError(
                error_type="confidence_calculation_error",
                item_id=item.s_no,
                details=str(e)
            ))
            item.confidence_score = 0.5  # Default medium confidence
    
    return EnrichedSOP(...), errors
```

**Format Optimizer Error Handling:**
```python
class FormattingError(Exception):
    error_type: str  # "template_error", "format_generation_failure"
    format_type: str  # "json", "yaml", "markdown"
    details: str

# Format Optimizer attempts all formats independently
def generate_formats(sop: EnrichedSOP) -> Dict[str, FormattedSOP]:
    results = {}
    errors = []
    
    for format_type in ["json", "yaml", "markdown"]:
        try:
            results[format_type] = generate_format(sop, format_type)
        except FormattingError as e:
            errors.append(e)
            # Continue with other formats
    
    return results, errors
```

**Version Manager Error Handling:**
```python
class VersioningError(Exception):
    error_type: str  # "storage_failure", "retrieval_failure", "conflict"
    version_id: Optional[str]
    details: str

# Version Manager ensures atomicity - either full success or rollback
def create_version(sop: FormattedSOP) -> VersionedSOP:
    try:
        version_id = generate_version_id()
        versioned_sop = VersionedSOP(version_id=version_id, ...)
        
        # Atomic storage operation
        storage.store(versioned_sop)
        
        return versioned_sop
    except Exception as e:
        # Rollback any partial changes
        storage.rollback()
        raise VersioningError(
            error_type="storage_failure",
            version_id=version_id,
            details=str(e)
        )
```

### Error Recovery Strategies

**Automatic Recovery:**
- Use default values for missing optional fields
- Apply fallback templates when custom templates fail
- Use cached data source information when registry is unavailable

**Manual Intervention Required:**
- Critical schema violations that prevent processing
- Conflicting information between sources with no resolution rule
- Storage system failures

**Error Notification:**
- Real-time alerts for critical errors
- Daily summary reports for warnings
- Weekly quality metrics for informational issues

## Testing Strategy

### Dual Testing Approach

The SOP Extraction Pipeline requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests**: Verify specific examples, edge cases, and error conditions
- Specific SOP document formats
- Known edge cases (empty documents, maximum size documents)
- Error conditions (malformed input, missing fields)
- Integration points between components

**Property Tests**: Verify universal properties across all inputs
- Extraction completeness for any valid SOP
- Schema compliance for any parsed data
- Round-trip consistency for versioning
- Format validity for any enriched SOP

Both approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across the input space.

### Property-Based Testing Configuration

**Testing Library**: Use Hypothesis (Python) for property-based testing

**Test Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test references its design document property
- Tag format: **Feature: sop-extraction-pipeline, Property {number}: {property_text}**

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st
import pytest

# Feature: sop-extraction-pipeline, Property 1: Extraction Completeness
@given(raw_sop=st.builds(generate_random_raw_sop))
@pytest.mark.property_test
def test_extraction_completeness(raw_sop):
    """
    For any raw SOP document, all questionnaire items should be extracted.
    Validates: Requirements 1.1, 1.2, 8.1
    """
    parser = Parser()
    parsed_sop, errors = parser.parse_document(raw_sop)
    
    # Verify all questionnaire items are present
    assert len(parsed_sop.questionnaire_items) > 0
    
    # Verify all items have required fields
    for item in parsed_sop.questionnaire_items:
        assert item.s_no is not None
        assert item.question is not None
        assert item.validation_type is not None
        assert len(item.instructions) > 0

# Feature: sop-extraction-pipeline, Property 27: Version Storage Round-Trip
@given(formatted_sop=st.builds(generate_random_formatted_sop))
@pytest.mark.property_test
def test_version_storage_round_trip(formatted_sop):
    """
    For any formatted SOP, storing and retrieving should return identical data.
    Validates: Requirements 7.2
    """
    version_manager = VersionManager()
    
    # Store version
    versioned_sop = version_manager.create_version(
        formatted_sop, 
        "Test version"
    )
    
    # Retrieve version
    retrieved_sop = version_manager.get_version(versioned_sop.version_id)
    
    # Verify identical
    assert retrieved_sop.formatted_sop == formatted_sop
    assert retrieved_sop.version_id == versioned_sop.version_id
```

### Unit Testing Strategy

**Component-Level Unit Tests**:
- Test each component (Parser, Schema Validator, Enrichment Engine, etc.) independently
- Use mock objects for dependencies
- Focus on specific examples and edge cases

**Integration Tests**:
- Test end-to-end pipeline flow
- Verify component interactions
- Test with realistic SOP documents

**Edge Case Tests**:
- Empty SOP documents
- Maximum size documents (stress testing)
- Documents with all optional fields missing
- Documents with special characters and encoding issues
- Malformed JSON/YAML in process maps

**Error Condition Tests**:
- Invalid input formats
- Missing required fields
- Conflicting information between sources
- Data source registry unavailable
- Storage system failures

### Test Data Generation

**Synthetic SOP Generation**:
```python
def generate_random_raw_sop() -> RawSOPDocument:
    """Generate random but valid raw SOP document for testing."""
    num_items = random.randint(1, 50)
    items = []
    
    for i in range(num_items):
        item = {
            "s_no": f"{i+1}",
            "question": generate_random_question(),
            "validation": random.choice(["Yes/No", "Multiple Choice"]),
            "instructions": generate_random_instructions(),
            "data_sources": generate_random_data_sources()
        }
        items.append(item)
    
    return RawSOPDocument(
        document_id=generate_uuid(),
        source_type="text_response",
        content=json.dumps(items),
        metadata={},
        timestamp=datetime.now()
    )
```

**Real-World Test Data**:
- Collect anonymized SOP documents from production
- Create test suite with representative examples
- Include documents that previously caused issues

### Testing Metrics

**Coverage Targets**:
- Line coverage: >90%
- Branch coverage: >85%
- Property test coverage: All 43 properties implemented

**Quality Metrics**:
- All property tests pass with 100 iterations
- All unit tests pass
- No critical or high-severity static analysis warnings
- Performance benchmarks met (see below)

### Performance Testing

**Throughput Benchmarks**:
- Single document processing: <5 seconds for typical SOP (10-20 items)
- Batch processing: >100 documents per minute
- Version retrieval: <100ms for any version

**Resource Limits**:
- Memory usage: <500MB for single document processing
- Memory usage: <2GB for batch processing (100 documents)
- Storage: <1MB per versioned SOP document

**Load Testing**:
- Test with batches of 1000+ documents
- Test with documents containing 100+ questionnaire items
- Test concurrent processing (multiple batches simultaneously)

### Continuous Integration

**CI Pipeline**:
1. Run all unit tests
2. Run all property tests (100 iterations each)
3. Run integration tests
4. Run static analysis (type checking, linting)
5. Generate coverage reports
6. Run performance benchmarks
7. Build and package artifacts

**Quality Gates**:
- All tests must pass
- Coverage targets must be met
- No high-severity static analysis warnings
- Performance benchmarks must be met

**Test Execution Time**:
- Unit tests: <2 minutes
- Property tests: <10 minutes (43 properties × 100 iterations)
- Integration tests: <5 minutes
- Total CI pipeline: <20 minutes
