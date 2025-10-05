variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "ragie_api_key" {
  description = "Ragie API key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "frontegg_api_key" {
  description = "Frontegg API key"
  type        = string
  sensitive   = true
}

variable "aws_access_key_id" {
  description = "AWS access key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS secret access key"
  type        = string
  sensitive   = true
}

variable "frontegg_encryption_password" {
  description = "Frontegg encryption password"
  type        = string
  sensitive   = true
}

variable "frontegg_client_id" {
  description = "Frontegg client ID"
  type        = string
}

variable "frontegg_app_id" {
  description = "Frontegg app ID"
  type        = string
}

variable "s3_bucket" {
  description = "S3 bucket name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "ragie_s3_bucket_prefix" {
  description = "Ragie S3 bucket prefix"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
