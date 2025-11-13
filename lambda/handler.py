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
    You are an expert AWS EventBridge analyst. Your task is to classify the event below into exactly one of these categories.

    ### Categories and rules

    1. **security**
    - Use this if the event deals with *access control*, *authentication*, *authorization*, or *key and policy management*.
    - Typical eventSources: iam.amazonaws.com, sts.amazonaws.com, kms.amazonaws.com.
    - Typical eventNames: CreateUser, DeleteUser, AttachUserPolicy, CreateAccessKey.
    - If an event could fit multiple categories, prefer "security".

    2. **cost**
    - Use this if the event **directly changes AWS billing or compute/storage usage**.
    - Examples: EC2 RunInstances, StopInstances, TerminateInstances, RDS CreateDBInstance, S3 CreateBucket, or scaling operations.
    - Only classify as "cost" if there is a clear start/stop/create/delete of a paid resource.
    - DO NOT classify simple log or metadata operations as cost.

    3. **infra**
    - Use this for infrastructure-level or operational events that **don’t affect billing directly** and **aren’t related to IAM or access**.
    - Examples: CreateLogStream, PutMetricData, CreateLoadBalancer, CreateSubnet, ModifyInstanceAttribute.
    - This is the default for events about configuration, networking, or monitoring.

    ### Decision priority
    If an event fits multiple categories:
    security > cost > infra

    ### Output format
    Return valid JSON in the exact format below:
    {{
    "category": "<one of: security|cost|infra>",
    "confidence": <float between 0 and 1>,
    "reason": "<brief explanation>"
    }}

    Now analyze the event:
    {json.dumps(event, indent=2)}
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