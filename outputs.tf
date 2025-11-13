output "archive_checksum" {
  value = data.archive_file.lambda_zip.output_base64sha256
}

output "eventbridge_rule_arn" {    
  description = "The ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.ai_notifier_event_rule.arn
}

output "lambda_function_arn" {
    description = "The ARN of the Lambda function"
    value       = aws_lambda_function.ai_notifier.arn
}

output "lambda_function_name" {
    description = "The name of the Lambda function"
    value       = aws_lambda_function.ai_notifier.function_name
}