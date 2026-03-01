# EventBridge Rules for Market Data Integration

## Rule 1: Market Data Ingestion Schedule

**Rule Name**: `market-data-ingestion-schedule`

**Description**: Triggers market data ingestion every 15 minutes during market hours

**Schedule Expression**: `cron(*/15 * * * ? *)`

**Target**: Lambda function `ingest-market-data`

**Event Pattern**: N/A (scheduled rule)

**State**: ENABLED

### Configuration

```json
{
  "Name": "market-data-ingestion-schedule",
  "Description": "Triggers market data ingestion every 15 minutes",
  "ScheduleExpression": "cron(*/15 * * * ? *)",
  "State": "ENABLED",
  "Targets": [
    {
      "Arn": "arn:aws:lambda:REGION:ACCOUNT:function:ingest-market-data",
      "Id": "1",
      "RetryPolicy": {
        "MaximumRetryAttempts": 2,
        "MaximumEventAge": 3600
      },
      "DeadLetterConfig": {
        "Arn": "arn:aws:sqs:REGION:ACCOUNT:market-data-dlq"
      }
    }
  ]
}
```

## Rule 2: Data Source Failure Handler

**Rule Name**: `market-data-source-failure`

**Description**: Triggers fallback handler when market data ingestion fails

**Event Pattern**:

```json
{
  "source": ["agri-nexus.market-data"],
  "detail-type": ["Data Source Failure"],
  "detail": {
    "errorType": ["API_UNAVAILABLE", "CIRCUIT_BREAKER_OPEN", "TIMEOUT"]
  }
}
```

**Target**: Lambda function `handle-data-source-failure`

**State**: ENABLED

### Configuration

```json
{
  "Name": "market-data-source-failure",
  "Description": "Handles market data source failures",
  "EventPattern": "{\"source\":[\"agri-nexus.market-data\"],\"detail-type\":[\"Data Source Failure\"]}",
  "State": "ENABLED",
  "Targets": [
    {
      "Arn": "arn:aws:lambda:REGION:ACCOUNT:function:handle-data-source-failure",
      "Id": "1",
      "RetryPolicy": {
        "MaximumRetryAttempts": 3,
        "MaximumEventAge": 7200
      }
    }
  ]
}
```

## Rule 3: Price Anomaly Detection

**Rule Name**: `market-data-price-anomaly`

**Description**: Triggers alerts when price anomalies are detected

**Event Pattern**:

```json
{
  "source": ["agri-nexus.market-data"],
  "detail-type": ["Price Anomaly Detected"],
  "detail": {
    "deviationPercent": [{ "numeric": [">", 50] }]
  }
}
```

**Target**: SNS topic for administrator alerts

**State**: ENABLED

## Event Publishing

The `ingest-market-data` Lambda function publishes events to EventBridge:

### Data Source Failure Event

```typescript
{
  "source": "agri-nexus.market-data",
  "detail-type": "Data Source Failure",
  "detail": {
    "source": "external_api",
    "errorType": "API_UNAVAILABLE",
    "errorMessage": "Connection timeout",
    "timestamp": "2024-01-15T10:30:00Z",
    "affectedCommodities": [
      { "cropType": "Potato", "location": "Kolkata" },
      { "cropType": "Rice", "location": "Delhi" }
    ]
  }
}
```

### Price Anomaly Event

```typescript
{
  "source": "agri-nexus.market-data",
  "detail-type": "Price Anomaly Detected",
  "detail": {
    "cropType": "Potato",
    "location": "Kolkata",
    "currentPrice": 2500,
    "averagePrice": 1500,
    "deviationPercent": 66.7,
    "anomalyReason": "Price deviation of 66.7% from 30-day average",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## CDK Configuration Example

```typescript
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as lambda from 'aws-cdk-lib/aws-lambda';

// Create scheduled rule for market data ingestion
const ingestionRule = new events.Rule(this, 'MarketDataIngestionSchedule', {
  schedule: events.Schedule.cron({
    minute: '*/15', // Every 15 minutes
  }),
  description: 'Triggers market data ingestion every 15 minutes',
});

ingestionRule.addTarget(new targets.LambdaFunction(ingestMarketDataFunction, {
  retryAttempts: 2,
  maxEventAge: Duration.hours(1),
  deadLetterQueue: marketDataDLQ,
}));

// Create event pattern rule for data source failures
const failureRule = new events.Rule(this, 'MarketDataSourceFailure', {
  eventPattern: {
    source: ['agri-nexus.market-data'],
    detailType: ['Data Source Failure'],
  },
  description: 'Handles market data source failures',
});

failureRule.addTarget(new targets.LambdaFunction(handleFailureFunction, {
  retryAttempts: 3,
  maxEventAge: Duration.hours(2),
}));
```
