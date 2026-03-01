# Market Agent Service

The Market Agent Service provides autonomous market intelligence for farmers, including real-time pricing, trend analysis, portfolio optimization, and government scheme recommendations.

## Lambda Functions

### 1. Get Market Intelligence (`get-market-intelligence.ts`)

Provides comprehensive market intelligence for a specific crop and location.

**Requirements:** 2.1, 2.3

**Request:**
```json
{
  "farmerId": "uuid",
  "cropType": "rice",
  "location": "Murshidabad",
  "language": "en"
}
```

**Response:**
```json
{
  "cropType": "rice",
  "location": "Murshidabad",
  "currentPrice": {
    "price": 2500,
    "unit": "per quintal",
    "marketName": "Murshidabad Mandi",
    "quality": "Grade A",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "historicalTrends": {
    "period": "30 days",
    "average": 2400,
    "min": 2200,
    "max": 2600,
    "trend": "rising"
  },
  "forecast": {
    "shortTerm": "Prices expected to remain stable over next 1-2 weeks",
    "mediumTerm": "Seasonal demand may push prices higher in coming months",
    "seasonalFactors": ["Harvest season", "Festival demand", "Export opportunities"]
  },
  "marketInsights": [
    "Current prices are 4% above 30-day average",
    "Strong demand from neighboring districts",
    "Government procurement active in the region"
  ],
  "actionableRecommendations": [
    "Consider selling within next 2 weeks to capture current high prices",
    "Explore government procurement options for guaranteed prices",
    "Monitor export market developments"
  ],
  "governmentSchemes": [
    {
      "schemeName": "PM-KISAN",
      "eligibility": "All landholding farmers",
      "benefits": "₹6000 per year in three installments"
    }
  ]
}
```

**Features:**
- Real-time market price data with caching (ElastiCache)
- Historical trend analysis (30-day statistics)
- AI-powered market insights using Amazon Bedrock
- Personalized recommendations based on farmer portfolio
- Government scheme information
- Multilingual support (English, Bengali, Hindi)

---

### 2. Analyze Portfolio (`analyze-portfolio.ts`)

Analyzes farmer's crop portfolio and provides optimization suggestions.

**Requirements:** 2.3

**Request:**
```json
{
  "farmerId": "uuid",
  "language": "en"
}
```

**Response:**
```json
{
  "farmerId": "uuid",
  "totalLandArea": 10,
  "cropAnalysis": [
    {
      "cropType": "rice",
      "currentMarketPrice": 2500,
      "pricetrend": "rising",
      "profitPotential": "high",
      "riskLevel": "low",
      "recommendations": [
        "Consider increasing cultivation area for this crop next season",
        "Current market conditions are favorable for selling"
      ]
    },
    {
      "cropType": "potato",
      "currentMarketPrice": 1200,
      "pricetrend": "falling",
      "profitPotential": "low",
      "riskLevel": "high",
      "recommendations": [
        "Consider reducing cultivation area or switching to alternative crops",
        "Explore value-added processing to improve margins",
        "Consider crop insurance to mitigate price volatility risks"
      ]
    }
  ],
  "optimizationSuggestions": [
    "Focus on rice cultivation given strong market trends",
    "Consider diversifying into high-value vegetables",
    "Explore contract farming for price stability"
  ],
  "profitScenarios": [
    {
      "scenario": "optimistic",
      "estimatedRevenue": 240000,
      "assumptions": [
        "Favorable weather conditions",
        "Strong market demand",
        "Minimal crop losses",
        "Prices 20% above current levels"
      ]
    },
    {
      "scenario": "realistic",
      "estimatedRevenue": 200000,
      "assumptions": [
        "Normal weather conditions",
        "Stable market demand",
        "Average crop yield",
        "Current market prices maintained"
      ]
    },
    {
      "scenario": "pessimistic",
      "estimatedRevenue": 160000,
      "assumptions": [
        "Adverse weather conditions",
        "Weak market demand",
        "Some crop losses",
        "Prices 20% below current levels"
      ]
    }
  ],
  "diversificationRecommendations": [
    "Add high-value crops like vegetables to portfolio",
    "Consider intercropping to maximize land utilization",
    "Explore organic farming for premium pricing"
  ],
  "overallRiskAssessment": "Portfolio shows moderate risk with heavy dependence on rice. Diversification into 2-3 additional crops recommended to reduce market volatility exposure."
}
```

**Features:**
- Individual crop performance analysis
- Market trend-based profit potential assessment
- Risk level evaluation for each crop
- Three profit scenarios (optimistic, realistic, pessimistic)
- AI-powered optimization suggestions
- Crop diversification recommendations
- Overall portfolio risk assessment

---

### 3. Get Government Schemes (`get-government-schemes.ts`)

Matches government schemes to farmer's profile and provides application guidance.

**Requirements:** 2.4

**Request:**
```json
{
  "farmerId": "uuid",
  "cropTypes": ["rice", "wheat"],
  "language": "en"
}
```

**Response:**
```json
{
  "farmerId": "uuid",
  "location": "Murshidabad, West Bengal",
  "cropTypes": ["rice", "wheat"],
  "schemes": [
    {
      "schemeId": "PM-KISAN",
      "schemeName": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
      "description": "Income support scheme providing direct financial assistance to farmers",
      "eligibilityCriteria": [
        "All landholding farmers",
        "Valid Aadhaar card",
        "Bank account linked to Aadhaar"
      ],
      "benefits": [
        "₹6,000 per year in three equal installments",
        "Direct bank transfer",
        "No upper limit on land holding"
      ],
      "applicationProcess": "Apply online at pmkisan.gov.in or through Common Service Centers",
      "documents": ["Aadhaar card", "Bank account details", "Land ownership documents"],
      "contactInfo": "PM-KISAN Helpline: 155261 / 011-24300606",
      "matchScore": 100,
      "matchReasons": [
        "Applicable to all crops",
        "Available in your state",
        "Universal income support for all farmers"
      ]
    },
    {
      "schemeId": "PMFBY",
      "schemeName": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
      "description": "Crop insurance scheme providing financial support against crop loss",
      "eligibilityCriteria": [
        "All farmers growing notified crops",
        "Sharecroppers and tenant farmers eligible",
        "Must enroll before sowing/planting"
      ],
      "benefits": [
        "Coverage against natural calamities, pests, and diseases",
        "Low premium rates (2% for Kharif, 1.5% for Rabi)",
        "Quick claim settlement"
      ],
      "applicationProcess": "Apply through banks, CSCs, or insurance company portals",
      "documents": ["Aadhaar card", "Bank account", "Land records", "Sowing certificate"],
      "contactInfo": "PMFBY Helpline: 011-23382012",
      "matchScore": 90,
      "matchReasons": [
        "Applicable to your crops: rice, wheat",
        "Available in your state",
        "Recommended for risk protection on your land size"
      ]
    }
  ],
  "totalPotentialBenefits": "₹6,000/year from PM-KISAN",
  "applicationGuidance": [
    "Start with PM-KISAN as it has universal eligibility and simple application process",
    "Ensure all documents (Aadhaar, land records, bank account) are ready before applying",
    "Apply for crop insurance (PMFBY) before sowing season begins",
    "Consider Kisan Credit Card for working capital needs",
    "Visit nearest Common Service Center (CSC) for application assistance",
    "Keep copies of all submitted documents and application receipts",
    "Follow up regularly on application status through helpline numbers"
  ]
}
```

**Features:**
- Intelligent scheme matching based on crops, location, and land area
- Match score (0-100) indicating relevance
- Detailed eligibility criteria and benefits
- Application process guidance
- Required documents checklist
- Contact information for each scheme
- AI-powered application guidance
- Total potential benefits calculation

**Supported Schemes:**
- PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)
- PMFBY (Pradhan Mantri Fasal Bima Yojana)
- KCC (Kisan Credit Card)
- PKVY (Paramparagat Krishi Vikas Yojana)
- MSP (Minimum Support Price)

---

## Environment Variables

All Lambda functions require the following environment variables:

- `TABLE_NAME`: DynamoDB table name for data storage
- `AWS_REGION`: AWS region (default: us-east-1)
- `CACHE_ENDPOINT`: ElastiCache Redis endpoint (optional, for caching)

## Dependencies

- `@aws-sdk/client-bedrock-runtime`: Amazon Bedrock integration
- `@aws-sdk/client-dynamodb`: DynamoDB operations
- `uuid`: Unique ID generation

## Integration with Bedrock

All Lambda functions use Amazon Bedrock with Claude 4.5 Sonnet for:
- Market trend analysis and forecasting
- Portfolio optimization suggestions
- Application guidance generation
- Multilingual content generation

## Caching Strategy

The market intelligence function implements caching using ElastiCache (Redis):
- Market data cached for 15 minutes (900 seconds)
- Cache key format: `market:<cropType>:<location>`
- Automatic fallback to DynamoDB on cache miss
- Reduces Bedrock API calls and improves response time

## Error Handling

All functions implement comprehensive error handling:
- Input validation with clear error messages
- Graceful degradation when external services fail
- Detailed error logging for debugging
- Circuit breaker pattern in Bedrock client
- Retry logic with exponential backoff

## Testing

See individual test files:
- Unit tests: Test individual functions and logic
- Property tests: Validate correctness properties across all inputs
- Integration tests: Test end-to-end workflows

## Related Services

- **Dr. Crop Service**: Crop disease diagnosis
- **Price Alert Service**: Proactive price notifications
- **User Service**: Farmer profile management
- **Market Data Service**: External market data integration
