# Requirements Document: O2A Ingestion Pipeline

## Introduction

The O2A (Observation to Automation) Ingestion Pipeline transforms manual quality control processes into automated workflows by capturing video streams from QA agent machines, processing them using AI vision models, and generating structured process maps. This system supports 1000+ Controls and 4000 QA Agents performing quality control operations, enabling the transition from manual observation to automated process understanding.

## Glossary

- **O2A_Pipeline**: The complete system that ingests video streams and produces text responses and process maps
- **Video_Stream**: Real-time or recorded video capture from QA agent machines showing manual quality control processes
- **SKAN_Agent**: Software agent installed on QA agent machines to capture video streams and process data
- **Gemini_VLM**: Google Gemini 3 Vision Language Model used for video analysis and text extraction
- **Process_Map**: Structured representation of the workflow steps, decision points, and actions extracted from video analysis
- **QA_Agent**: Human quality assurance agent performing manual control processes
- **Control**: A specific quality control checkpoint or validation procedure
- **SOP**: Standard Operating Procedure defining the questionnaire-based validation workflow
- **Prompt_Template**: Configurable instruction set for the Gemini VLM to optimize extraction accuracy
- **Video_Segment**: A discrete portion of video corresponding to a specific action or decision point
- **Action_Extraction**: The process of identifying and classifying user actions from video frames
- **Text_Response**: Structured text output from video analysis including actions, decisions, and data values
- **Validation_Point**: A specific checkpoint in the SOP where yes/no validation occurs
- **Data_Source_Tag**: Metadata indicating where information was obtained (e.g., system screen, form field)

## Requirements

### Requirement 1: Video Stream Capture

**User Story:** As a system administrator, I want to capture video streams from QA agent machines, so that I can record manual quality control processes for analysis.

#### Acceptance Criteria

1. WHEN a SKAN_Agent is installed on a QA agent machine, THE O2A_Pipeline SHALL establish a connection to receive video streams
2. WHEN a video stream is active, THE O2A_Pipeline SHALL capture frames at a minimum rate of 1 frame per second
3. WHEN network connectivity is interrupted, THE O2A_Pipeline SHALL buffer video data locally and resume transmission when connectivity is restored
4. THE O2A_Pipeline SHALL support simultaneous video streams from at least 4000 QA agent machines
5. WHEN a video stream is received, THE O2A_Pipeline SHALL timestamp each frame with millisecond precision
6. THE O2A_Pipeline SHALL store raw video streams in a format compatible with Gemini_VLM processing requirements

### Requirement 2: Video Segmentation

**User Story:** As a data engineer, I want to segment video streams into meaningful units, so that I can process discrete actions and decision points independently.

#### Acceptance Criteria

1. WHEN a video stream is received, THE O2A_Pipeline SHALL segment it into Video_Segments based on detected activity changes
2. WHEN segmenting video, THE O2A_Pipeline SHALL identify segment boundaries using visual change detection with a minimum confidence threshold of 0.85
3. WHEN a Video_Segment is created, THE O2A_Pipeline SHALL associate it with temporal metadata including start time, end time, and duration
4. THE O2A_Pipeline SHALL maintain segment continuity such that no frames are lost between consecutive segments
5. WHEN a Video_Segment duration exceeds 60 seconds without detected activity change, THE O2A_Pipeline SHALL create a new segment boundary

### Requirement 3: Vision Language Model Processing

**User Story:** As a machine learning engineer, I want to process video segments using Gemini 3 VLM, so that I can extract text, actions, and decision points from visual data.

#### Acceptance Criteria

1. WHEN a Video_Segment is ready for processing, THE O2A_Pipeline SHALL submit it to Gemini_VLM with the configured Prompt_Template
2. WHEN Gemini_VLM processes a segment, THE O2A_Pipeline SHALL extract structured data including user actions, screen text, form fields, and decision outcomes
3. WHEN extraction fails with an error, THE O2A_Pipeline SHALL retry processing up to 3 times with exponential backoff
4. THE O2A_Pipeline SHALL process Video_Segments with a maximum latency of 5 seconds per segment under normal load
5. WHEN Gemini_VLM returns results, THE O2A_Pipeline SHALL validate the response schema before storing the extracted data
6. THE O2A_Pipeline SHALL tag each extracted element with a Data_Source_Tag indicating its origin (screen region, form field, button click, etc.)

### Requirement 4: Action Extraction and Classification

**User Story:** As a process analyst, I want to identify and classify user actions from video analysis, so that I can understand the steps QA agents perform.

#### Acceptance Criteria

1. WHEN processing a Video_Segment, THE O2A_Pipeline SHALL identify discrete user actions including mouse clicks, keyboard input, form submissions, and navigation events
2. WHEN an action is identified, THE O2A_Pipeline SHALL classify it into predefined categories (data entry, validation check, navigation, error handling, approval)
3. WHEN multiple actions occur in rapid succession, THE O2A_Pipeline SHALL maintain temporal ordering with millisecond precision
4. THE O2A_Pipeline SHALL extract the target of each action (e.g., specific form field, button label, menu item)
5. WHEN an action involves data entry, THE O2A_Pipeline SHALL extract the entered value and associate it with the target field

### Requirement 5: SOP Questionnaire Mapping

**User Story:** As a quality control manager, I want to map extracted actions to SOP questionnaire steps, so that I can validate process compliance.

#### Acceptance Criteria

1. WHEN processing extracted actions, THE O2A_Pipeline SHALL match them to corresponding SOP questionnaire items based on action type and context
2. WHEN a Validation_Point is identified, THE O2A_Pipeline SHALL extract the yes/no decision and the corresponding instruction path followed
3. THE O2A_Pipeline SHALL identify the sequence number (S.No) of each questionnaire item addressed in the video
4. WHEN an action does not match any known SOP questionnaire item, THE O2A_Pipeline SHALL flag it as an unmapped action for review
5. THE O2A_Pipeline SHALL maintain the hierarchical relationship between questionnaire items and their validation outcomes

### Requirement 6: Process Map Generation

**User Story:** As a process improvement specialist, I want to generate process maps from video analysis, so that I can visualize and optimize quality control workflows.

#### Acceptance Criteria

1. WHEN all Video_Segments for a complete process execution are analyzed, THE O2A_Pipeline SHALL generate a Process_Map representing the workflow
2. THE Process_Map SHALL include nodes for each identified action, decision point, and validation check
3. THE Process_Map SHALL include edges representing the flow between steps, with labels indicating conditions or triggers
4. WHEN a decision point is encountered, THE Process_Map SHALL represent both the yes and no paths with their respective subsequent actions
5. THE O2A_Pipeline SHALL output Process_Maps in a machine-readable format (JSON or GraphML)
6. THE Process_Map SHALL include metadata for each node including timestamp, duration, extracted data values, and Data_Source_Tags

### Requirement 7: Prompt Engineering and Experimentation

**User Story:** As a machine learning engineer, I want to experiment with different prompt templates, so that I can optimize extraction accuracy and completeness.

#### Acceptance Criteria

1. THE O2A_Pipeline SHALL support configurable Prompt_Templates that can be modified without code changes
2. WHEN a new Prompt_Template is created, THE O2A_Pipeline SHALL validate its structure against required fields (task description, output format, examples)
3. THE O2A_Pipeline SHALL support A/B testing by randomly assigning Video_Segments to different Prompt_Templates based on configured distribution ratios
4. WHEN processing with multiple Prompt_Templates, THE O2A_Pipeline SHALL track extraction accuracy metrics for each template including field extraction rate, action classification accuracy, and processing time
5. THE O2A_Pipeline SHALL store Prompt_Template performance metrics to enable comparison and optimization
6. WHEN a Prompt_Template is updated, THE O2A_Pipeline SHALL version it and maintain historical performance data

### Requirement 8: Text Response Generation

**User Story:** As a data consumer, I want structured text responses from video analysis, so that I can integrate extracted information with downstream systems.

#### Acceptance Criteria

1. WHEN video processing is complete, THE O2A_Pipeline SHALL generate a Text_Response containing all extracted information in structured format
2. THE Text_Response SHALL include sections for: identified actions, extracted data values, validation outcomes, decision paths, and timestamps
3. THE Text_Response SHALL conform to a predefined JSON schema that can be validated programmatically
4. WHEN generating Text_Responses, THE O2A_Pipeline SHALL include confidence scores for each extracted element
5. THE O2A_Pipeline SHALL associate each Text_Response with its source Video_Segments and raw video references

### Requirement 9: Error Handling and Quality Assurance

**User Story:** As a system operator, I want robust error handling and quality checks, so that I can ensure reliable pipeline operation.

#### Acceptance Criteria

1. WHEN video quality is insufficient for analysis (low resolution, excessive blur, poor lighting), THE O2A_Pipeline SHALL flag the Video_Segment for manual review
2. WHEN Gemini_VLM extraction confidence falls below 0.7 for critical fields, THE O2A_Pipeline SHALL flag the extraction for human verification
3. WHEN processing fails after all retry attempts, THE O2A_Pipeline SHALL log the failure with diagnostic information and notify system operators
4. THE O2A_Pipeline SHALL maintain an audit log of all processing attempts including timestamps, prompt versions, and outcomes
5. WHEN inconsistencies are detected between extracted actions and expected SOP flow, THE O2A_Pipeline SHALL generate an anomaly alert

### Requirement 10: Scalability and Performance

**User Story:** As a system architect, I want the pipeline to scale efficiently, so that I can support 4000+ concurrent QA agents.

#### Acceptance Criteria

1. THE O2A_Pipeline SHALL process video streams from at least 4000 QA agent machines concurrently
2. WHEN system load increases, THE O2A_Pipeline SHALL automatically scale processing resources to maintain target latency of 5 seconds per Video_Segment
3. THE O2A_Pipeline SHALL implement rate limiting for Gemini_VLM API calls to stay within quota limits while maximizing throughput
4. WHEN processing queues exceed capacity thresholds, THE O2A_Pipeline SHALL prioritize Video_Segments based on configurable business rules
5. THE O2A_Pipeline SHALL maintain processing throughput of at least 800 Video_Segments per minute under normal load

### Requirement 11: Data Storage and Retrieval

**User Story:** As a data analyst, I want efficient storage and retrieval of processed data, so that I can analyze historical process executions.

#### Acceptance Criteria

1. THE O2A_Pipeline SHALL store raw video streams, Video_Segments, Text_Responses, and Process_Maps in a queryable data store
2. WHEN storing data, THE O2A_Pipeline SHALL implement retention policies that archive video data older than 90 days to cold storage
3. THE O2A_Pipeline SHALL support querying by QA agent ID, Control ID, timestamp range, SOP questionnaire item, and extraction confidence
4. WHEN retrieving historical data, THE O2A_Pipeline SHALL return results within 2 seconds for queries spanning up to 30 days
5. THE O2A_Pipeline SHALL implement data compression for stored video to reduce storage costs by at least 60%

### Requirement 12: Integration with Google ADK

**User Story:** As a developer, I want seamless integration with Google ADK, so that I can leverage agent creation capabilities.

#### Acceptance Criteria

1. THE O2A_Pipeline SHALL integrate with Google ADK APIs for agent lifecycle management
2. WHEN a new QA agent machine is provisioned, THE O2A_Pipeline SHALL automatically register it with Google ADK
3. THE O2A_Pipeline SHALL use Google ADK authentication and authorization mechanisms for all API interactions
4. WHEN agent configuration changes in Google ADK, THE O2A_Pipeline SHALL synchronize the changes within 60 seconds
5. THE O2A_Pipeline SHALL report agent health status and video stream availability to Google ADK monitoring dashboards
