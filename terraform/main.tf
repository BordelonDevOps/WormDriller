terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.50" }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = var.default_tags
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "apprunner_role_arn" {
  description = "IAM role ARN for App Runner access"
  type        = string
}

variable "default_tags" {
  type = map(string)
  default = {
    Project             = "WormDriller-AI"
    Environment         = "dev"
    Application         = "hybrid-suite"
    Owner               = "chris@bordelon.io"
    CostCenter          = "506-DrillingAnalytics"
    ManagedBy           = "terraform"
    DataClassification  = "Operational"
    Compliance          = "None"
  }
}

resource "aws_ecr_repository" "api" {
  name = "wormdriller-api"
}

resource "aws_apprunner_service" "api" {
  service_name = "wormdriller-api"
  source_configuration {
    image_repository {
      image_identifier      = "${aws_ecr_repository.api.repository_url}:latest"
      image_repository_type = "ECR"
      image_configuration { port = "8000" }
    }
    authentication_configuration {
      access_role_arn = var.apprunner_role_arn
    }
    auto_deployments_enabled = true
  }
}
