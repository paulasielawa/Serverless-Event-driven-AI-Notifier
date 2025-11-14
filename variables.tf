variable "event_pattern" {
  description = "EventBridge pattern as JSON string"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to be applied to AWS resources"
  type        = map(string)
  default     = {}
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

variable "timeout_in_seconds" {
    description = "Timeout for the Lambda function in seconds"
    type        = number
    default     = 30
}

variable "subscriptions" {
  description = "List of notification endpoints (protocol + endpoint) for SNS topics."
  type        = map(list(object({
    protocol = string
    endpoint = string
  })))
  default = {
    security = []
    cost     = []
    infra    = []
  }
}

variable "memory_size_in_mb" {
  description = "Memory size for the Lambda function in MB"
  type        = number
  default     = 128
}