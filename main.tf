 /*
    AWS Lambda Function with IAM Role and Logging Permissions
*/
data "aws_iam_policy_document" "lambda_assume_role_policy" {
    statement {
        effect = "Allow"
        actions = ["sts:AssumeRole"]
        principals {
            type        = "Service"
            identifiers = ["lambda.amazonaws.com"]
        }
    }
}

resource "aws_iam_role" "lambda_iam_role" {
    name               = "iam_for_lambda"
    assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}

data "aws_iam_policy_document" "allow_logging" {
    statement {
        effect = "Allow"
        actions = [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents"
        ]
        resources = ["arn:aws:logs:*:*:*"]
    }
}

resource "aws_iam_policy" "lambda_logging" {
    name   = "lambda-logging-cloudwatch"
    policy = data.aws_iam_policy_document.allow_logging.json
}

resource "aws_iam_role_policy_attachment" "func_log_policy" {
    role       = aws_iam_role.lambda_iam_role.name
    policy_arn = aws_iam_policy.lambda_logging.arn
}

data "archive_file" "lambda_zip" {
    type        = "zip"
    source_dir  = "${path.module}/lambda"
    output_path = "${path.module}/lambda/lambda_payload.zip"
}

resource "aws_lambda_function" "ai_notifier" {
    function_name = var.function_name
    description   = "Lambda function to notify based on AI events"
    role          = aws_iam_role.lambda_iam_role.arn

    handler       = "handler.lambda_handler"
    runtime       = "python3.12"
    filename      = data.archive_file.lambda_zip.output_path
    source_code_hash = data.archive_file.lambda_zip.output_base64sha256

    environment {
      variables = {
        SNS_SECURITY_TOPIC_ARN = aws_sns_topic.security_alerts.arn
        SNS_COST_TOPIC_ARN     = aws_sns_topic.cost_optimization.arn
        SNS_INFRA_TOPIC_ARN    = aws_sns_topic.infra_events.arn 
        BEDROCK_REGION         = var.bedrock_region
      }
    }

    tags = var.tags
}

resource "aws_cloudwatch_log_group" "ai_notifier_log_group" {
    name              = "/aws/lambda/${aws_lambda_function.ai_notifier.function_name}"
    retention_in_days = var.retention_in_days
  
}

resource "aws_lambda_permission" "allow_eventbridge" {
    statement_id  = "AllowExecutionFromEventBridge"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.ai_notifier.function_name
    principal     = "events.amazonaws.com"
}

 /*
    EventBridge Rule to Trigger Lambda Function
*/
resource "aws_cloudwatch_event_rule" "ai_notifier_event_rule" {
    name        = "ai_notifier_event_rule"
    description = "EventBridge rule to trigger AI Notifier Lambda function"

    event_pattern = var.event_pattern != "" ? var.event_pattern : file("${path.module}/event_patterns/default.json")
    tags = var.tags
}

resource "aws_cloudwatch_event_target" "ai_notifier_target" {
    rule      = aws_cloudwatch_event_rule.ai_notifier_event_rule.name
    arn       = aws_lambda_function.ai_notifier.arn
    target_id = "ai_notifier_lambda_target"
}

 /*
    SNS topics for different AI categories
*/
resource "aws_sns_topic" "security_alerts" {
    name = "${var.function_name}-security_alerts"
    tags = var.tags
}

resource "aws_sns_topic" "cost_optimization" {
    name = "${var.function_name}-cost_optimization"
    tags = var.tags
}

resource "aws_sns_topic" "infra_events" {
    name = "${var.function_name}-infrastructure_events"
    tags = var.tags
}

resource "aws_iam_policy" "lambda_sns_publish_policy" {
    name = "lambda-sns-publish-policy"

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = "sns:Publish"
                Resource = [
                    aws_sns_topic.security_alerts.arn,
                    aws_sns_topic.cost_optimization.arn,
                    aws_sns_topic.infra_events.arn
                ]
            }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "lambda_sns_publish_attach" {
    role       = aws_iam_role.lambda_iam_role.name
    policy_arn = aws_iam_policy.lambda_sns_publish_policy.arn
}

/*
    Bedrock permissions for Lambda
*/

resource "aws_iam_policy" "lambda_bedrock_policy" {
    name = "lambda-bedrock-access-policy"

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "bedrock:InvokeModel",
                    "bedrock:ListModels"
                ]
                Resource = "*"
            }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "lambda_bedrock_attach" {
    role       = aws_iam_role.lambda_iam_role.name
    policy_arn = aws_iam_policy.lambda_bedrock_policy.arn
}