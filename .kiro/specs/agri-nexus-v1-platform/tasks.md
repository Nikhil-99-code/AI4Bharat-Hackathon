# Implementation Plan: Agri-Nexus V1 Platform

## Overview

This implementation plan breaks down the Agri-Nexus V1 Platform into discrete coding tasks for a 24-hour hackathon MVP. The platform combines AI-powered crop disease diagnosis (Dr. Crop), voice-based farmer assistance (Sahayak), and proactive market price alerts into a single Streamlit application backed by AWS serverless services.

The implementation follows a layered approach: infrastructure setup, shared utilities, backend Lambda functions, frontend Streamlit application, and integration testing. Each task builds incrementally toward a working demonstration of all three core features.

## Tasks

- [x] 1. Project setup and infrastructure foundation
  - Create project directory structure with folders for `frontend/`, `backend/`, `shared/`, `tests/`, and `infrastructure/`
  - Set up Python virtual environment and install dependencies: `streamlit`, `boto3`, `pillow`, `hypothesis`, `pytest`
  - Create `.env.template` file with required environment variables: `AWS_REGION`, `TABLE_NAME`, `IMAGE_BUCKET`, `API_GATEWAY_URL`, `BEDROCK_MODEL_ID`
  - Create `requirements.txt` with all Python dependencies and version pins
  - _Requirements: 17.1, 17.2, 17.3, 23.1_

- [ ] 2. AWS infrastructure and DynamoDB setup
  - [x] 2.1 Create DynamoDB table schema with single-table design
    - Write Python script or AWS CDK code to create DynamoDB table with PK, SK, and three GSIs (GSI1, GSI2, GSI3)
    - Configure GSI1 for admin queries (GSI1PK: entity_type, GSI1SK: status_or_timestamp)
    - Configure GSI2 for market data queries (GSI2PK: crop_type, GSI2SK: location_timestamp)
    - Configure GSI3 for alert processing (GSI3PK: alert_type_status, GSI3SK: target_price_timestamp)
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 23.4_
  
  - [ ]* 2.2 Write property test for DynamoDB key structure
    - **Property 8: DynamoDB Key Structure**
    - **Validates: Requirements 6.3, 9.6, 16.3, 16.4, 16.5**
  
  - [x] 2.3 Create S3 bucket for image and audio storage
    - Write script to create S3 bucket with appropriate permissions and lifecycle policies
    - Configure CORS for Streamlit frontend access
    - _Requirements: 23.2_

- [ ] 3. Shared utilities and configuration
  - [x] 3.1 Implement application configuration loader
    - Create `shared/config.py` with `AppConfig` dataclass
    - Load configuration from environment variables with validation
    - Provide default values for local development mode
    - Raise errors for missing required configuration in production mode
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_
  
  - [ ]* 3.2 Write property test for configuration validation
    - **Property 24: Configuration Validation**
    - **Validates: Requirements 17.2, 17.3, 17.4, 17.5**
  
  - [x] 3.3 Implement DynamoDB repository layer
    - Create `shared/dynamodb_repository.py` with methods for storing and retrieving entities
    - Implement `store_diagnosis()`, `get_diagnosis_history()`, `store_interaction()`, `store_price_threshold()`, `get_active_thresholds()`, `store_market_data()`, `get_latest_price()`, `store_notification_trigger()`
    - Handle pagination for large result sets
    - _Requirements: 6.1, 6.2, 6.3, 9.5, 9.6, 12.3, 16.1_
  
  - [ ]* 3.4 Write unit tests for DynamoDB repository
    - Test entity storage and retrieval with specific examples
    - Test GSI queries for market data and alerts
    - Test pagination logic
    - _Requirements: 6.1, 6.2, 9.5, 12.3_
  
  - [x] 3.5 Implement Bedrock client wrapper
    - Create `shared/bedrock_client.py` with methods for image analysis, transcription, text generation, and TTS
    - Implement `analyze_image()`, `transcribe_audio()`, `generate_response()`, `text_to_speech()`
    - Configure model ID, temperature (0.3), and max tokens (2048)
    - Implement retry logic with exponential backoff for rate limiting
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_
  
  - [ ]* 3.6 Write property test for Bedrock rate limit handling
    - **Property 23: Bedrock Rate Limit Handling**
    - **Validates: Requirements 15.5**
  
  - [x] 3.7 Implement SNS client for SMS notifications
    - Create `shared/sns_client.py` with methods for sending SMS
    - Implement `send_sms()` and `format_alert_message()` with multilingual templates
    - Implement retry logic with exponential backoff for failed deliveries
    - _Requirements: 13.1, 13.2, 13.3, 13.5_
  
  - [ ]* 3.8 Write property test for SMS retry logic
    - **Property 21: SMS Retry Logic**
    - **Validates: Requirements 13.5**
  
  - [ ]* 3.9 Write property test for SMS message format
    - **Property 20: SMS Message Format**
    - **Validates: Requirements 13.2, 13.3**

- [ ] 4. Image validation component
  - [x] 4.1 Implement image validator
    - Create `shared/image_validator.py` with `ImageValidator` class
    - Implement `validate_image()` to check format (JPEG, PNG, JPG), resolution (min 224x224), brightness, contrast, and file integrity
    - Implement `compress_image()` to reduce file size while maintaining quality
    - Return validation results with descriptive error messages
    - _Requirements: 2.2, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 21.4_
  
  - [ ]* 4.2 Write property test for image format validation
    - **Property 2: Image Format Validation**
    - **Validates: Requirements 2.2, 2.5**
  
  - [ ]* 4.3 Write property test for image size validation
    - **Property 3: Image Size Validation**
    - **Validates: Requirements 2.4**
  
  - [ ]* 4.4 Write property test for image quality validation
    - **Property 4: Image Quality Validation**
    - **Validates: Requirements 3.1, 3.3, 3.4, 3.5**
  
  - [ ]* 4.5 Write unit tests for image validator edge cases
    - Test corrupted images, boundary values (exactly 10MB, exactly 224x224), empty files
    - _Requirements: 2.2, 2.4, 3.1, 3.2_
  
  - [ ]* 4.6 Write property test for image compression
    - **Property 29: Image Compression**
    - **Validates: Requirements 21.4**

- [ ] 5. Checkpoint - Verify shared utilities
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Dr. Crop Lambda function (analyze_crop_image)
  - [x] 6.1 Implement analyze_crop_image Lambda handler
    - Create `backend/analyze_crop_image/handler.py` with `lambda_handler()` function
    - Parse input event for user_id, image_data (base64), and language
    - Store image in S3 bucket
    - Construct structured prompt for Bedrock with JSON format instructions
    - Invoke Bedrock client to analyze image
    - Parse JSON response and validate required fields (disease_name, confidence, treatment)
    - Store diagnosis result in DynamoDB
    - Return structured response with diagnosis_id, disease_name, confidence, treatment, timestamp
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 5.1, 5.2, 5.3, 6.1, 6.2, 14.2_
  
  - [ ]* 6.2 Write property test for diagnosis result structure
    - **Property 6: Diagnosis Result Structure**
    - **Validates: Requirements 4.3, 4.4, 4.5**
  
  - [ ]* 6.3 Write property test for diagnosis persistence
    - **Property 7: Diagnosis Persistence**
    - **Validates: Requirements 6.1, 6.2**
  
  - [ ]* 6.4 Write property test for unstructured response parsing
    - **Property 35: Unstructured Response Parsing**
    - **Validates: Requirements 5.4**
  
  - [ ]* 6.5 Write unit tests for Lambda error handling
    - Test Bedrock failures, S3 upload failures, DynamoDB write failures
    - _Requirements: 14.5, 18.1, 18.3_

- [ ] 7. Sahayak Lambda functions (voice processing)
  - [x] 7.1 Implement process_voice_input Lambda handler
    - Create `backend/process_voice_input/handler.py` with `lambda_handler()` function
    - Parse input event for user_id, audio_data (base64), and language
    - Invoke Bedrock client to transcribe audio
    - Generate contextual response using Bedrock with agricultural domain expertise
    - Store interaction in DynamoDB
    - Return interaction_id, transcript, response_text, timestamp
    - _Requirements: 8.1, 8.2, 8.3, 8.6, 14.3_
  
  - [x] 7.2 Implement generate_voice_response Lambda handler
    - Create `backend/generate_voice_response/handler.py` with `lambda_handler()` function
    - Parse input event for text and language
    - Invoke Bedrock client to convert text to speech
    - Return audio_data (base64) and duration_seconds
    - _Requirements: 8.4, 14.3_
  
  - [ ]* 7.3 Write property test for voice processing pipeline
    - **Property 13: Voice Processing Pipeline**
    - **Validates: Requirements 8.1, 8.3, 8.4, 8.5**
  
  - [ ]* 7.4 Write unit tests for voice Lambda functions
    - Test transcription with sample audio, TTS with sample text, error handling
    - _Requirements: 8.1, 8.4, 14.5_

- [ ] 8. Alert Lambda functions (market data and triggers)
  - [x] 8.1 Implement ingest_market_data Lambda handler
    - Create `backend/ingest_market_data/handler.py` with `lambda_handler()` function
    - Parse input event for crop_type, location, price, timestamp, simulation flag
    - Store market data in DynamoDB with GSI2 index
    - Trigger alert checking process by invoking trigger_alerts Lambda
    - Return market_data_id and alerts_triggered count
    - _Requirements: 11.2, 14.4_
  
  - [x] 8.2 Implement trigger_alerts Lambda handler
    - Create `backend/trigger_alerts/handler.py` with `lambda_handler()` function
    - Query active price thresholds using GSI3 index
    - Compare current price against each threshold
    - For thresholds where price >= target, create notification trigger and store in DynamoDB
    - Send SMS via SNS client with formatted message
    - Implement deduplication to prevent duplicate alerts for same price update
    - Return alerts_triggered, notifications_sent, and failures list
    - _Requirements: 11.3, 11.4, 12.1, 12.2, 12.3, 12.4, 12.5, 13.1, 13.4_
  
  - [ ]* 8.3 Write property test for price comparison logic
    - **Property 17: Price Comparison Logic**
    - **Validates: Requirements 11.3, 11.4**
  
  - [ ]* 8.4 Write property test for alert trigger and notification pipeline
    - **Property 19: Alert Trigger and Notification Pipeline**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 13.1**
  
  - [ ]* 8.5 Write property test for simulation logging
    - **Property 18: Simulation Logging**
    - **Validates: Requirements 11.5**
  
  - [ ]* 8.6 Write unit tests for alert Lambda functions
    - Test GSI3 queries, deduplication logic, SMS delivery failures
    - _Requirements: 11.3, 12.3, 12.5, 13.5_

- [ ] 9. Checkpoint - Verify all Lambda functions
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Streamlit application foundation
  - [x] 10.1 Create main Streamlit application structure
    - Create `frontend/streamlit_app.py` with `main()` function
    - Implement session state management
    - Create three-tab navigation (Dr. Crop, Sahayak, Alerts)
    - Implement language selector in header with English, Bengali, Hindi options
    - Load configuration from environment variables
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 17.1, 19.1, 19.2_
  
  - [ ]* 10.2 Write property test for tab navigation consistency
    - **Property 1: Tab Navigation Consistency**
    - **Validates: Requirements 1.3, 1.4**
  
  - [ ]* 10.3 Write property test for language switching
    - **Property 26: Language Switching**
    - **Validates: Requirements 19.3**
  
  - [ ] 10.2 Implement authentication with AWS Cognito
    - Add Cognito user pool integration
    - Implement login/logout functionality
    - Enforce authentication before accessing features
    - Implement 30-minute session timeout
    - _Requirements: 22.1, 22.2, 22.5_
  
  - [ ]* 10.3 Write property test for authentication enforcement
    - **Property 31: Authentication Enforcement**
    - **Validates: Requirements 22.1**
  
  - [ ]* 10.4 Write property test for session timeout
    - **Property 33: Session Timeout**
    - **Validates: Requirements 22.5**
  
  - [x] 10.4 Implement error handling and user feedback
    - Create error message localization dictionary for all supported languages
    - Implement error display function that shows user-friendly messages without stack traces
    - Add CloudWatch logging for detailed error information
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_
  
  - [ ]* 10.5 Write property test for error message localization
    - **Property 25: Error Message Localization**
    - **Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5**
  
  - [ ]* 10.6 Write property test for Lambda error handling
    - **Property 22: Lambda Error Handling**
    - **Validates: Requirements 14.5**

- [ ] 11. Dr. Crop tab implementation
  - [x] 11.1 Implement Dr. Crop image upload interface
    - Create `render_dr_crop_tab()` function in streamlit_app.py
    - Add file uploader widget accepting JPEG, PNG, JPG formats with 10MB limit
    - Display image preview after upload
    - Validate image using ImageValidator before submission
    - Display validation errors in user's language
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ]* 11.2 Write property test for image preview display
    - **Property 5: Image Preview Display**
    - **Validates: Requirements 2.3**
  
  - [x] 11.2 Implement diagnosis request and display
    - Add "Analyze" button to submit validated image
    - Display loading indicator during diagnosis (expected 30 seconds)
    - Call analyze_crop_image Lambda via API Gateway
    - Parse and display diagnosis result: disease name, confidence percentage, treatment recommendation
    - Handle errors and display user-friendly messages
    - _Requirements: 4.1, 4.3, 4.4, 4.5, 4.6, 14.1, 14.2, 21.2_
  
  - [ ]* 11.3 Write property test for loading indicator display
    - **Property 28: Loading Indicator Display**
    - **Validates: Requirements 21.2**
  
  - [ ]* 11.4 Write property test for timeout warning
    - **Property 30: Timeout Warning**
    - **Validates: Requirements 21.5**
  
  - [x] 11.3 Implement diagnosis history display
    - Query diagnosis history from DynamoDB via API Gateway
    - Display most recent 20 diagnoses in reverse chronological order
    - Show disease name, confidence, treatment, and timestamp for each entry
    - _Requirements: 6.4, 6.5_
  
  - [ ]* 11.4 Write property test for diagnosis history ordering
    - **Property 9: Diagnosis History Ordering**
    - **Validates: Requirements 6.4**
  
  - [ ]* 11.5 Write property test for diagnosis history pagination
    - **Property 10: Diagnosis History Pagination**
    - **Validates: Requirements 6.5**
  
  - [ ]* 11.6 Write property test for service response localization
    - **Property 27: Service Response Localization**
    - **Validates: Requirements 19.4, 19.5**

- [ ] 12. Sahayak tab implementation
  - [x] 12.1 Implement voice recording interface
    - Create `render_sahayak_tab()` function in streamlit_app.py
    - Add audio recorder widget with start/stop buttons
    - Limit recording duration to 60 seconds
    - Display playback control for recorded audio
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ]* 12.2 Write property test for audio duration limit
    - **Property 11: Audio Duration Limit**
    - **Validates: Requirements 7.4**
  
  - [ ]* 12.3 Write property test for audio playback control
    - **Property 12: Audio Playback Control**
    - **Validates: Requirements 7.5**
  
  - [x] 12.2 Implement voice processing and response display
    - Add "Submit" button to send recorded audio
    - Display loading indicator during processing (expected 15 seconds)
    - Call process_voice_input Lambda via API Gateway
    - Display transcribed question text
    - Call generate_voice_response Lambda to get audio response
    - Display text response and audio playback control
    - Handle errors and display user-friendly messages
    - _Requirements: 8.1, 8.3, 8.4, 8.5, 8.6, 14.1, 14.3, 21.2_

- [ ] 13. Alerts tab implementation
  - [x] 13.1 Implement price alert configuration form
    - Create `render_alerts_tab()` function in streamlit_app.py
    - Add form with crop type dropdown, target price input, location input
    - Add "Create Alert" button to submit form
    - Validate inputs and display errors
    - Call Alert_Service to store price threshold in DynamoDB
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ]* 13.2 Write property test for price alert persistence
    - **Property 14: Price Alert Persistence**
    - **Validates: Requirements 9.5, 9.6**
  
  - [ ] 13.2 Implement active alerts display and management
    - Query and display all active price thresholds for current user
    - Show crop type, target price, location, creation date for each alert
    - Add delete button for each alert
    - Refresh alert list after modifications
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 13.3 Write property test for active alerts display
    - **Property 15: Active Alerts Display**
    - **Validates: Requirements 10.1, 10.2, 10.3**
  
  - [ ]* 13.4 Write property test for alert deletion
    - **Property 16: Alert Deletion**
    - **Validates: Requirements 10.4, 10.5**
  
  - [ ] 13.3 Implement market price simulation for testing
    - Add "Simulate Price Change" button for demonstration
    - Generate mock market data with random price variations
    - Call ingest_market_data Lambda with simulation flag
    - Display simulation results and triggered alerts
    - _Requirements: 11.1, 11.2, 11.5_

- [ ] 14. Checkpoint - Verify Streamlit application
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. API Gateway and Lambda deployment
  - [x] 15.1 Create API Gateway REST API
    - Define API Gateway with endpoints for all Lambda functions
    - Configure CORS for Streamlit frontend
    - Set up request/response transformations
    - _Requirements: 14.1, 23.2_
  
  - [x] 15.2 Deploy Lambda functions with IAM roles
    - Package Lambda functions with dependencies
    - Create IAM roles with appropriate permissions (DynamoDB, S3, Bedrock, SNS, CloudWatch)
    - Deploy all Lambda functions with environment variables
    - Configure timeouts: 30s for diagnosis, 15s for voice, 60s for alerts
    - _Requirements: 14.2, 14.3, 14.4, 23.3_
  
  - [x] 15.3 Configure CloudWatch monitoring
    - Set up CloudWatch log groups for all Lambda functions
    - Create CloudWatch dashboard with key metrics
    - Configure alarms for error rates and latency
    - _Requirements: 24.1, 24.2, 24.3, 24.4_
  
  - [ ]* 15.4 Write property test for metrics emission
    - **Property 34: Metrics Emission**
    - **Validates: Requirements 24.1, 24.2, 24.3, 24.4**
  
  - [ ]* 15.5 Write property test for HTTPS transmission
    - **Property 32: HTTPS Transmission**
    - **Validates: Requirements 22.3**

- [x] 16. Integration testing and happy path demonstration
  - [ ]* 16.1 Write integration test for complete Dr. Crop flow
    - Test upload image → validate → diagnose → store → display
    - Verify all components work together end-to-end
    - _Requirements: 20.1_
  
  - [ ]* 16.2 Write integration test for complete Sahayak flow
    - Test record audio → transcribe → generate response → TTS → display
    - Verify all components work together end-to-end
    - _Requirements: 20.2_
  
  - [ ]* 16.3 Write integration test for complete Alert flow
    - Test configure alert → update price → trigger → send SMS → verify delivery
    - Verify all components work together end-to-end
    - _Requirements: 20.3_
  
  - [x] 16.4 Create happy path demonstration script
    - Create automated script that demonstrates all three features sequentially
    - Use sample crop image, voice recording, and price alert configuration
    - Verify execution completes within 5 minutes
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

- [ ] 17. Performance optimization and final polish
  - [ ] 17.1 Optimize application performance
    - Implement caching for static resources
    - Compress images before upload
    - Add loading indicators for all long operations
    - Test initial page load time on 3G connection
    - _Requirements: 21.1, 21.2, 21.3, 21.4_
  
  - [ ] 17.2 Create deployment script
    - Write single-command deployment script
    - Output all configuration values needed for Streamlit app
    - Verify deployment is repeatable
    - _Requirements: 23.1, 23.5_
  
  - [ ] 17.3 Create README with setup instructions
    - Document prerequisites, installation steps, configuration, and usage
    - Include troubleshooting guide
    - Add screenshots of all three features
    - _Requirements: 23.1_

- [ ] 18. Final checkpoint - Complete system verification
  - Run all tests (unit, property, integration)
  - Verify happy path demonstration works end-to-end
  - Confirm all 24 requirements are met
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Checkpoints ensure incremental validation at key milestones
- Focus on getting a working demonstration of all three core features within 24 hours
- Authentication can be simplified for hackathon demo (mock Cognito if needed)
- Use simulation mode for market price alerts to demonstrate functionality without real data feeds
