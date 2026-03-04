# Requirements Document

## Introduction

Agri-Nexus V1 is a comprehensive agricultural application platform that empowers farmers with AI-powered crop diagnosis, voice-based assistance, and proactive market price alerts. The platform integrates computer vision for disease detection, natural language processing for voice interaction, and real-time market intelligence to help farmers make informed decisions. Built using Python and Streamlit, the application provides a vernacular-first user interface that connects to AWS serverless backend services including Bedrock AI, DynamoDB, Lambda, and SNS.

## Glossary

- **Streamlit_App**: The Python-based web application frontend built using the Streamlit framework
- **Dr_Crop_Service**: The AI-powered crop disease diagnosis service using computer vision
- **Sahayak_Service**: The voice-based assistant service for farmer queries and guidance
- **Alert_Service**: The proactive notification system for market price changes
- **Bedrock_Client**: The AWS Bedrock API client using Claude 3.5 Sonnet model
- **DynamoDB_Repository**: The data persistence layer using AWS DynamoDB
- **SNS_Client**: The AWS Simple Notification Service client for SMS delivery
- **Lambda_Function**: AWS serverless compute functions for backend processing
- **Image_Validator**: Component that validates uploaded crop images for quality and format
- **Price_Threshold**: User-defined target price for a specific crop that triggers alerts
- **Diagnosis_Result**: Structured output containing disease name, confidence score, and treatment recommendation
- **Voice_Input**: Audio recording from farmer captured through the application
- **Market_Data**: Real-time or simulated crop price information by location
- **Notification_Trigger**: Event-driven mechanism that sends alerts when conditions are met
- **Happy_Path**: Complete end-to-end demonstration flow showing all core features working together

## Requirements

### Requirement 1: Streamlit Application Foundation

**User Story:** As a farmer, I want to access a simple web application with clear navigation, so that I can easily use different features without confusion.

#### Acceptance Criteria

1. THE Streamlit_App SHALL render a web interface with three primary navigation tabs
2. THE Streamlit_App SHALL label the tabs as "Dr. Crop", "Sahayak", and "Alerts"
3. WHEN a user clicks on any tab, THE Streamlit_App SHALL display the corresponding feature interface
4. THE Streamlit_App SHALL maintain navigation state across user interactions
5. THE Streamlit_App SHALL use vernacular-first language labels with English fallback

### Requirement 2: Crop Image Upload Interface

**User Story:** As a farmer, I want to upload photos of my crops, so that I can get disease diagnosis.

#### Acceptance Criteria

1. WHEN the "Dr. Crop" tab is active, THE Streamlit_App SHALL display an image upload widget
2. THE Streamlit_App SHALL accept image files in JPEG, PNG, and JPG formats
3. WHEN an image is uploaded, THE Streamlit_App SHALL display a preview of the uploaded image
4. THE Streamlit_App SHALL limit uploaded image file size to 10 megabytes
5. IF an invalid file format is uploaded, THEN THE Streamlit_App SHALL display an error message in the user's preferred language

### Requirement 3: Image Quality Validation

**User Story:** As a farmer, I want to know if my photo is good enough for analysis, so that I don't waste time on poor quality images.

#### Acceptance Criteria

1. WHEN an image is uploaded, THE Image_Validator SHALL check image resolution is at least 224x224 pixels
2. THE Image_Validator SHALL verify the image is not corrupted or unreadable
3. THE Image_Validator SHALL assess image brightness and contrast are within acceptable ranges
4. IF image quality is insufficient, THEN THE Image_Validator SHALL return a descriptive error message
5. WHEN image quality is acceptable, THE Image_Validator SHALL return a validation success indicator

### Requirement 4: Crop Disease Diagnosis

**User Story:** As a farmer, I want to receive accurate disease diagnosis from my crop photos, so that I can take appropriate treatment actions.

#### Acceptance Criteria

1. WHEN a validated image is submitted, THE Dr_Crop_Service SHALL send the image to the Bedrock_Client
2. THE Bedrock_Client SHALL analyze the image using Claude 3.5 Sonnet model
3. THE Dr_Crop_Service SHALL return a Diagnosis_Result containing disease name, confidence percentage, and treatment recommendation
4. THE Diagnosis_Result SHALL format confidence as a percentage between 0 and 100
5. WHEN diagnosis is complete, THE Streamlit_App SHALL display the disease name, confidence score, and recommended treatment in structured format
6. THE Dr_Crop_Service SHALL complete diagnosis within 30 seconds of image submission

### Requirement 5: Diagnosis Prompt Engineering

**User Story:** As a system operator, I want the AI to return consistent structured responses, so that the application can reliably parse and display results.

#### Acceptance Criteria

1. THE Dr_Crop_Service SHALL construct prompts that request disease name, confidence percentage, and treatment recommendation
2. THE Dr_Crop_Service SHALL instruct the Bedrock_Client to return responses in JSON format
3. THE Dr_Crop_Service SHALL include examples of expected output format in the prompt
4. WHEN the Bedrock_Client returns unstructured data, THE Dr_Crop_Service SHALL attempt to parse and structure the response
5. IF parsing fails after retry, THEN THE Dr_Crop_Service SHALL return an error indicating diagnosis could not be completed

### Requirement 6: Diagnosis History Persistence

**User Story:** As a farmer, I want my diagnosis history saved, so that I can review past diagnoses and track crop health over time.

#### Acceptance Criteria

1. WHEN a diagnosis is completed, THE Dr_Crop_Service SHALL store the Diagnosis_Result in the DynamoDB_Repository
2. THE DynamoDB_Repository SHALL store user ID, timestamp, image reference, disease name, confidence score, and treatment recommendation
3. THE DynamoDB_Repository SHALL use partition key "USER#<farmerId>" and sort key "DIAGNOSIS#<timestamp>"
4. THE Streamlit_App SHALL display a history section showing past diagnoses in reverse chronological order
5. WHEN a user views diagnosis history, THE Streamlit_App SHALL display the most recent 20 diagnoses

### Requirement 7: Voice Input Capture

**User Story:** As a farmer, I want to ask questions using my voice, so that I can get help without typing.

#### Acceptance Criteria

1. WHEN the "Sahayak" tab is active, THE Streamlit_App SHALL display a voice recording interface
2. THE Streamlit_App SHALL provide a button to start and stop voice recording
3. WHEN recording starts, THE Streamlit_App SHALL capture audio from the user's microphone
4. THE Streamlit_App SHALL support audio recording up to 60 seconds duration
5. WHEN recording stops, THE Streamlit_App SHALL display a playback control for the recorded audio

### Requirement 8: Voice Processing and Response

**User Story:** As a farmer, I want to receive spoken answers to my questions, so that I can understand guidance without reading.

#### Acceptance Criteria

1. WHEN a voice recording is submitted, THE Sahayak_Service SHALL send the audio to the Bedrock_Client for transcription
2. THE Sahayak_Service SHALL process the transcribed text to understand farmer intent
3. THE Sahayak_Service SHALL generate a contextual response using the Bedrock_Client
4. THE Sahayak_Service SHALL convert the text response to speech audio
5. WHEN processing is complete, THE Streamlit_App SHALL display the transcribed question, text response, and audio playback control
6. THE Sahayak_Service SHALL complete voice processing within 15 seconds

### Requirement 9: Price Alert Configuration

**User Story:** As a farmer, I want to set target prices for my crops, so that I get notified when market prices reach my desired levels.

#### Acceptance Criteria

1. WHEN the "Alerts" tab is active, THE Streamlit_App SHALL display a form to configure price alerts
2. THE Streamlit_App SHALL allow users to select a crop type from a predefined list
3. THE Streamlit_App SHALL allow users to enter a target price as a numeric value
4. THE Streamlit_App SHALL allow users to specify their location or market
5. WHEN a user submits the form, THE Alert_Service SHALL store the Price_Threshold in the DynamoDB_Repository
6. THE DynamoDB_Repository SHALL use partition key "USER#<farmerId>" and sort key "PRICE_TARGET#<cropType>"

### Requirement 10: Price Alert Storage and Retrieval

**User Story:** As a farmer, I want to view and manage my active price alerts, so that I can update or remove them as needed.

#### Acceptance Criteria

1. THE Streamlit_App SHALL display a list of all active Price_Threshold entries for the current user
2. THE Streamlit_App SHALL show crop type, target price, location, and creation date for each alert
3. THE Streamlit_App SHALL provide a delete button for each Price_Threshold entry
4. WHEN a user clicks delete, THE Alert_Service SHALL remove the Price_Threshold from the DynamoDB_Repository
5. THE Streamlit_App SHALL refresh the alert list after any modification

### Requirement 11: Market Price Simulation

**User Story:** As a system operator, I want to simulate market price changes, so that I can demonstrate the alert triggering mechanism.

#### Acceptance Criteria

1. THE Streamlit_App SHALL provide a simulation button in the "Alerts" tab for testing purposes
2. WHEN the simulation button is clicked, THE Alert_Service SHALL generate mock Market_Data with random price variations
3. THE Alert_Service SHALL compare simulated prices against all active Price_Threshold entries
4. THE Alert_Service SHALL identify Price_Threshold entries where the simulated price meets or exceeds the target
5. WHERE simulation mode is enabled, THE Alert_Service SHALL log all price comparisons for debugging

### Requirement 12: Alert Trigger Logic

**User Story:** As a farmer, I want to be automatically notified when crop prices reach my targets, so that I can make timely selling decisions.

#### Acceptance Criteria

1. WHEN Market_Data price meets or exceeds a Price_Threshold, THE Alert_Service SHALL create a Notification_Trigger event
2. THE Notification_Trigger SHALL include user ID, crop type, target price, current price, and timestamp
3. THE Alert_Service SHALL store the Notification_Trigger in the DynamoDB_Repository for audit purposes
4. THE Alert_Service SHALL use GSI3 index with "GSI3PK: ALERT#TRIGGERED" for efficient alert processing
5. THE Alert_Service SHALL process each Price_Threshold only once per price update to prevent duplicate notifications

### Requirement 13: SMS Notification Delivery

**User Story:** As a farmer, I want to receive SMS messages when price alerts trigger, so that I am notified even when not using the application.

#### Acceptance Criteria

1. WHEN a Notification_Trigger is created, THE Alert_Service SHALL send the event to the SNS_Client
2. THE SNS_Client SHALL format the message to include crop type, target price, and current price
3. THE SNS_Client SHALL send the SMS to the phone number associated with the user account
4. THE SNS_Client SHALL deliver the SMS within 60 seconds of the Notification_Trigger creation
5. IF SMS delivery fails, THEN THE Alert_Service SHALL log the failure and retry up to 3 times with exponential backoff

### Requirement 14: Lambda Function Integration

**User Story:** As a system architect, I want to use existing Lambda functions for backend processing, so that I can leverage the current serverless infrastructure.

#### Acceptance Criteria

1. THE Streamlit_App SHALL invoke Lambda_Function endpoints via HTTP API Gateway
2. THE Dr_Crop_Service SHALL use the existing "analyze_crop_image" Lambda_Function
3. THE Sahayak_Service SHALL use the existing "process_voice_input" and "generate_voice_response" Lambda_Function instances
4. THE Alert_Service SHALL use the existing "ingest_market_data" Lambda_Function for price updates
5. WHEN a Lambda_Function invocation fails, THE Streamlit_App SHALL display a user-friendly error message and log technical details

### Requirement 15: AWS Bedrock Configuration

**User Story:** As a system administrator, I want to configure AWS Bedrock with appropriate model settings, so that AI responses are accurate and cost-effective.

#### Acceptance Criteria

1. THE Bedrock_Client SHALL use the Claude 3.5 Sonnet model identifier "anthropic.claude-3-5-sonnet-20241022-v2:0"
2. THE Bedrock_Client SHALL set temperature parameter to 0.3 for consistent diagnostic outputs
3. THE Bedrock_Client SHALL set maximum tokens to 2048 for diagnosis responses
4. THE Bedrock_Client SHALL include system prompts that specify agricultural domain expertise
5. THE Bedrock_Client SHALL handle rate limiting errors with exponential backoff retry logic

### Requirement 16: DynamoDB Table Schema

**User Story:** As a system architect, I want to use a single-table design for all data storage, so that I can optimize query performance and reduce costs.

#### Acceptance Criteria

1. THE DynamoDB_Repository SHALL use a single table with partition key "PK" and sort key "SK"
2. THE DynamoDB_Repository SHALL implement three Global Secondary Indexes: GSI1, GSI2, and GSI3
3. THE DynamoDB_Repository SHALL use GSI1 for admin dashboard queries with "GSI1PK: entity_type" and "GSI1SK: status_or_timestamp"
4. THE DynamoDB_Repository SHALL use GSI2 for market data queries with "GSI2PK: crop_type" and "GSI2SK: location_timestamp"
5. THE DynamoDB_Repository SHALL use GSI3 for alert processing with "GSI3PK: alert_type_status" and "GSI3SK: target_price_timestamp"

### Requirement 17: Application Configuration Management

**User Story:** As a developer, I want to manage environment-specific configuration separately, so that I can deploy to different environments without code changes.

#### Acceptance Criteria

1. THE Streamlit_App SHALL load configuration from environment variables
2. THE Streamlit_App SHALL require AWS_REGION, TABLE_NAME, IMAGE_BUCKET, and API_GATEWAY_URL environment variables
3. WHERE environment variables are not set, THE Streamlit_App SHALL use default values for local development
4. THE Streamlit_App SHALL validate all required configuration values at startup
5. IF required configuration is missing, THEN THE Streamlit_App SHALL display an error message and refuse to start

### Requirement 18: Error Handling and User Feedback

**User Story:** As a farmer, I want to see clear error messages when something goes wrong, so that I understand what happened and what to do next.

#### Acceptance Criteria

1. WHEN any service encounters an error, THE Streamlit_App SHALL display a user-friendly error message in the user's preferred language
2. THE Streamlit_App SHALL avoid displaying technical stack traces or error codes to end users
3. THE Streamlit_App SHALL log detailed error information to CloudWatch for debugging
4. THE Streamlit_App SHALL provide actionable guidance in error messages when possible
5. IF a network error occurs, THEN THE Streamlit_App SHALL suggest checking internet connectivity

### Requirement 19: Multilingual Support

**User Story:** As a farmer, I want to use the application in my local language, so that I can understand all features and guidance.

#### Acceptance Criteria

1. THE Streamlit_App SHALL support English, Bengali, and Hindi languages
2. THE Streamlit_App SHALL provide a language selector in the application header
3. WHEN a user changes language, THE Streamlit_App SHALL update all interface labels and messages immediately
4. THE Dr_Crop_Service SHALL return diagnosis results in the user's selected language
5. THE Sahayak_Service SHALL process voice input and generate responses in the user's selected language

### Requirement 20: Happy Path Demonstration

**User Story:** As a product stakeholder, I want to see a complete end-to-end demonstration, so that I can validate all core features are working together.

#### Acceptance Criteria

1. THE Happy_Path SHALL demonstrate uploading a crop image and receiving a diagnosis with disease name, confidence, and treatment
2. THE Happy_Path SHALL demonstrate recording a voice question and receiving a spoken response
3. THE Happy_Path SHALL demonstrate setting a price alert, simulating a price change, and triggering an SMS notification
4. THE Happy_Path SHALL complete all three demonstrations within 5 minutes
5. THE Happy_Path SHALL execute without manual intervention beyond initial user inputs

### Requirement 21: Application Performance

**User Story:** As a farmer with limited internet connectivity, I want the application to load quickly and respond promptly, so that I can use it efficiently.

#### Acceptance Criteria

1. THE Streamlit_App SHALL load the initial interface within 3 seconds on a 3G connection
2. THE Streamlit_App SHALL display loading indicators for all operations exceeding 2 seconds
3. THE Streamlit_App SHALL cache static resources to reduce repeated network requests
4. THE Streamlit_App SHALL compress images before uploading to reduce bandwidth usage
5. WHEN network latency exceeds 5 seconds, THE Streamlit_App SHALL display a timeout warning

### Requirement 22: Security and Authentication

**User Story:** As a farmer, I want my data to be secure and private, so that my farming information is protected.

#### Acceptance Criteria

1. THE Streamlit_App SHALL require user authentication before accessing any features
2. THE Streamlit_App SHALL use AWS Cognito for user identity management
3. THE Streamlit_App SHALL transmit all data over HTTPS encrypted connections
4. THE Streamlit_App SHALL store user credentials securely using AWS Secrets Manager
5. THE Streamlit_App SHALL automatically log out users after 30 minutes of inactivity

### Requirement 23: Deployment and Infrastructure

**User Story:** As a DevOps engineer, I want to deploy the application using infrastructure as code, so that deployments are repeatable and consistent.

#### Acceptance Criteria

1. THE Streamlit_App SHALL be deployable using a single command or script
2. THE deployment process SHALL provision all required AWS resources using AWS CDK or CloudFormation
3. THE deployment process SHALL configure all Lambda_Function instances with appropriate IAM roles and environment variables
4. THE deployment process SHALL create the DynamoDB table with all required indexes
5. THE deployment process SHALL output all necessary configuration values for the Streamlit_App

### Requirement 24: Monitoring and Observability

**User Story:** As a system operator, I want to monitor application health and performance, so that I can identify and resolve issues proactively.

#### Acceptance Criteria

1. THE Streamlit_App SHALL send application metrics to CloudWatch
2. THE Streamlit_App SHALL track metrics for page views, feature usage, error rates, and response times
3. THE Lambda_Function instances SHALL log all invocations with request ID, duration, and status
4. THE Alert_Service SHALL track metrics for alerts created, triggered, and delivered
5. THE system SHALL provide a CloudWatch dashboard showing all key metrics in a single view
