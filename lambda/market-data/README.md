# Market Data Integration Lambda Functions

This directory contains Lambda functions for the Market Data Integration Service.

## Functions

### ingest-market-data.ts
Scheduled Lambda function that runs every 15 minutes to:
- Fetch commodity price data from external APIs
- Validate price data for anomalies
- Store historical price trends in DynamoDB
- Trigger alerts when data source failures occur

**Trigger**: EventBridge scheduled rule (every 15 minutes)
**Requirements**: 6.1, 6.3, 6.4

### handle-data-source-failure.ts
Lambda function that handles fallback scenarios when external APIs fail:
- Uses cached data when external APIs are unavailable
- Sends administrator alerts for data source failures
- Implements automatic reconnection logic

**Trigger**: EventBridge event from ingest-market-data failures
**Requirements**: 6.2, 4.4

## Environment Variables

- `TABLE_NAME`: DynamoDB table name for storing market data
- `AWS_REGION`: AWS region for services
- `CACHE_ENDPOINT`: ElastiCache Redis endpoint for caching
- `ADMIN_SNS_TOPIC_ARN`: SNS topic ARN for administrator alerts
- `MARKET_DATA_API_KEY`: API key for external market data service
- `MARKET_DATA_API_URL`: Base URL for external market data API

## External API Integration

The service integrates with commodity price APIs to fetch real-time market data. The API should provide:
- Crop/commodity prices by location
- Market names and quality grades
- Timestamp information
- Regional price variations

## Anomaly Detection

Price data is validated for anomalies using:
- Historical price comparison (>50% deviation triggers alert)
- Sudden price spikes or drops
- Missing or invalid data fields
- Stale data detection (>24 hours old)

## Circuit Breaker Pattern

The service implements circuit breaker pattern for external API calls:
- **Closed**: Normal operation, requests pass through
- **Open**: After threshold failures, requests fail fast
- **Half-Open**: After timeout, test requests to check recovery
