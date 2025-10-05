# Staging environment configuration

# Project configuration
project_name = "get-convinced"
environment  = "staging"
aws_region   = "ap-south-1"

# Network configuration
availability_zones     = ["ap-south-1a", "ap-south-1b"]
vpc_cidr              = "10.0.0.0/16"
private_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnet_cidrs   = ["10.0.10.0/24", "10.0.20.0/24"]

# Database configuration
db_instance_class              = "db.t3.micro"
db_allocated_storage           = 20
db_storage_type               = "gp2"
db_backup_retention_period    = 7
enable_deletion_protection    = false
enable_backup                 = true
enable_monitoring             = false

# ECS configuration
ecs_cluster_name = "get-convinced-staging-cluster"
ecs_service_name = "backend"
ecs_task_cpu     = 512
ecs_task_memory  = 1024
ecs_desired_count = 1
ecs_min_capacity = 1
ecs_max_capacity = 2

# Application configuration
backend_port = 8001
redis_port   = 6379

# Domain configuration (optional)
# domain_name     = "staging-api.get-convinced.com"
# certificate_arn = "arn:aws:acm:ap-south-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
