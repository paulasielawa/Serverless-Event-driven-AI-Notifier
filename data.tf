#Fetch information about the current AWS caller identity and region
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

