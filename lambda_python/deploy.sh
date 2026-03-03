#!/bin/bash

# Package and deploy Lambda functions to AWS

FUNCTIONS=(
    "dr_crop/analyze_crop_image"
    "dr_crop/validate_image_quality"
    "dr_crop/get_diagnosis_history"
    "market_agent/get_market_intelligence"
    "market_agent/analyze_portfolio"
    "market_agent/get_government_schemes"
    "market_data/ingest_market_data"
    "voice_interface/process_voice_input"
    "voice_interface/generate_voice_response"
)

for func in "${FUNCTIONS[@]}"; do
    echo "Packaging $func..."
    cd $(dirname $func)
    zip -r ../$(basename $func).zip $(basename $func).py ../lib/
    cd -
    
    echo "Deploying $func..."
    aws lambda update-function-code \
        --function-name agri-nexus-$(basename $func) \
        --zip-file fileb://$(basename $func).zip
done

echo "Deployment complete!"
