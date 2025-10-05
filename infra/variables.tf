# Variables for AI Knowledge Agent infrastructure

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "get-convinced"
}

variable "environment" {
  description = "Environment name (staging, prod)"
  type        = string
  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "Environment must be either 'staging' or 'prod'."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "availability_zones" {
  description = "Availability zones for the region"
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

# Network variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

# Database variables
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_storage_type" {
  description = "RDS storage type"
  type        = string
  default     = "gp2"
}

variable "db_backup_retention_period" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 7
}

variable "db_backup_window" {
  description = "RDS backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "RDS maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

# ECS variables
variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = ""
}

variable "ecs_service_name" {
  description = "Name of the ECS service"
  type        = string
  default     = "backend"
}

variable "ecs_task_cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory for ECS task in MB"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "ecs_min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 3
}

# Application variables
variable "backend_image" {
  description = "Backend Docker image URI"
  type        = string
  default     = ""
}

variable "backend_port" {
  description = "Backend application port"
  type        = number
  default     = 8001
}

variable "redis_port" {
  description = "Redis port"
  type        = number
  default     = 6379
}

# Domain and SSL
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "SSL certificate ARN"
  type        = string
  default     = ""
}

# Environment-specific overrides
variable "enable_deletion_protection" {
  description = "Enable deletion protection for RDS"
  type        = bool
  default     = false
}

variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable detailed monitoring"
  type        = bool
  default     = false
}

# Secrets variables
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

variable "ragie_s3_bucket_prefix" {
  description = "Ragie S3 bucket prefix"
  type        = string
}
