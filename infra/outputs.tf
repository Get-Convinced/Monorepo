# Outputs for AI Knowledge Agent infrastructure

# Network outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.network.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.network.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.network.public_subnet_ids
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = module.network.alb_security_group_id
}

output "backend_security_group_id" {
  description = "ID of the backend security group"
  value       = module.network.backend_security_group_id
}

output "database_security_group_id" {
  description = "ID of the database security group"
  value       = module.network.database_security_group_id
}

# Database outputs
output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = module.database.endpoint
  sensitive   = true
}

output "database_port" {
  description = "RDS instance port"
  value       = module.database.port
}

output "database_name" {
  description = "RDS instance database name"
  value       = module.database.name
}

output "database_username" {
  description = "RDS instance username"
  value       = module.database.username
  sensitive   = true
}

output "database_secret_arn" {
  description = "ARN of the database secret in Secrets Manager"
  value       = module.database.secret_arn
  sensitive   = true
}

# ECS outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = module.service.ecs_cluster_id
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.service.ecs_cluster_arn
}

output "ecs_service_id" {
  description = "ID of the ECS service"
  value       = module.service.ecs_service_id
}

output "ecs_service_arn" {
  description = "ARN of the ECS service"
  value       = module.service.ecs_service_arn
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = module.service.ecs_task_definition_arn
}

# Load Balancer outputs
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.service.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = module.service.alb_zone_id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = module.service.alb_arn
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = module.service.target_group_arn
}

# ECR outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.service.ecr_repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = module.service.ecr_repository_arn
}

# IAM outputs
output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = module.iam.ecs_task_role_arn
}

output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = module.iam.ecs_execution_role_arn
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions role"
  value       = module.iam.github_actions_role_arn
}

# Application URLs
output "backend_url" {
  description = "Backend API URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "http://${module.service.alb_dns_name}"
}

output "health_check_url" {
  description = "Health check URL"
  value       = "${var.domain_name != "" ? "https://${var.domain_name}" : "http://${module.service.alb_dns_name}"}/health"
}

# Environment information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "aws_account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}
