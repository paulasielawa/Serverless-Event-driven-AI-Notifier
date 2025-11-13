import boto3, json, os, re

bedrock_client = boto3.client('bedrock-runtime', region_name=os.environ['BEDROCK_REGION'])
sns = boto3.client("sns")


def parse_json_from_text(text):
    cleaned = re.sub(r"```[\w-]*\n", "", text)
    cleaned = cleaned.replace("```", "").strip()

    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None

def classify_event(event):
    prompt = f"""
    You are an AWS event analyst.
    Analyze the following AWS EventBridge event and classify it into one of:
    - "security": relates to IAM, policies, unauthorized access, keys, permissions
    - "cost": relates to starting/stopping/terminating instances, data transfers
    - "infra": other infrastructure operations

    Return your response as **valid JSON** with the following structure:
    {{
      "category": "<one of: security|cost|infra>",
      "confidence": "<0-1 float>",
      "reason": "<short explanation why you categorized it>"
    }}

    Example events:
    {{"eventName": "RunInstances"}} → category: "cost"
    {{"eventName": "CreateUser"}} → category: "security"
    {{"eventName": "CreateBucket"}} → category: "infra"

    Event JSON:
    {json.dumps(event)}
    """
    
    response = bedrock_client.invoke_model(
        modelId="amazon.titan-text-lite-v1",
        body=json.dumps({
            "inputText": prompt
        })
    )
    output = json.loads(response['body'].read())
    classification_text = output["results"][0]["outputText"].strip()

    parsed = parse_json_from_text(classification_text)
    if parsed and "category" in parsed:
        return parsed

    lower_text = classification_text.lower()
    if "security" in lower_text:
        category = "security"
    elif "cost" in lower_text:
        category = "cost"
    else:
        category = "infra"

    return {
        "category": category,
        "confidence": 0.5,
        "reason": classification_text[:500]
    }

def lambda_handler(event, context):
    result = classify_event(event)
    category = result.get("category", "infra")
    message = {
        "ai-result": {
            "category": category,
            "confidence": result.get("confidence"),
            "reason": result.get("reason"),
            "original_event": event
        },
        "event-details": event 
    }

    topic_arns = {
        "security": os.environ['SNS_SECURITY_TOPIC_ARN'],
        "cost": os.environ['SNS_COST_TOPIC_ARN'],
        "infra": os.environ['SNS_INFRA_TOPIC_ARN']
    }

    topic_arn = topic_arns.get(category)

    sns.publish(
        TopicArn=topic_arn,
        Message=json.dumps(message),
        Subject=f"AI Notifier Event: {category.upper()}"
    )

    return {
        "statusCode": 200,
        "category": category,
        "ai_reason": result.get("reason"),
        "ai_confidence": result.get("confidence"),
        "event_summary": event
    }