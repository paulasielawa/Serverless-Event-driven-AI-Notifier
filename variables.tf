variable "event_pattern" {
  description = "EventBridge pattern as JSON string"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to be applied to AWS resources"
  type        = map(string)
}

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "ai_notifier"
}

variable "retention_in_days" {
    description = "Number of days to retain CloudWatch logs"
    type        = number
    default     = 1
}

variable "bedrock_region" {
  description = "AWS Region for Bedrock service"
  type        = string
}

