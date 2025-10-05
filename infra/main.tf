# Main Terraform configuration for AI Knowledge Agent infrastructure

# Network module
module "network" {
  source = "./modules/network"

  project_name = var.project_name
  environment  = var.environment

  vpc_cidr               = var.vpc_cidr
  availability_zones     = var.availability_zones
  private_subnet_cidrs   = var.private_subnet_cidrs
  public_subnet_cidrs    = var.public_subnet_cidrs

  tags = local.common_tags
}

    # Database module
    module "database" {
      source = "./modules/database"

      project_name = var.project_name
      environment  = var.environment

      vpc_id                     = module.network.vpc_id
      private_subnet_ids         = module.network.private_subnet_ids
      public_subnet_ids          = module.network.public_subnet_ids
      database_security_group_id = module.network.database_security_group_id

  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage
  storage_type               = var.db_storage_type
  backup_retention_period    = var.db_backup_retention_period
  backup_window              = var.db_backup_window
  maintenance_window         = var.db_maintenance_window

  enable_deletion_protection = var.enable_deletion_protection
  enable_backup             = var.enable_backup
  enable_monitoring         = var.enable_monitoring

  tags = local.common_tags
}

# IAM module
# Secrets Module
module "secrets" {
  source = "./modules/secrets"
  
  project_name = var.project_name
  environment  = var.environment
  
  # Pass secrets as variables (you'll need to set these)
  ragie_api_key                = var.ragie_api_key
  openai_api_key              = var.openai_api_key
  frontegg_api_key            = var.frontegg_api_key
  aws_access_key_id           = var.aws_access_key_id
  aws_secret_access_key       = var.aws_secret_access_key
  frontegg_encryption_password = var.frontegg_encryption_password
  frontegg_client_id          = var.frontegg_client_id
  frontegg_app_id             = var.frontegg_app_id
  s3_bucket                   = var.s3_bucket
  aws_region                  = var.aws_region
  ragie_s3_bucket_prefix      = var.ragie_s3_bucket_prefix
  
  tags = local.common_tags
}

module "iam" {
  source = "./modules/iam"

  project_name = var.project_name
  environment  = var.environment

  tags = local.common_tags
}

# Service module
module "service" {
  source = "./modules/service"

  project_name = var.project_name
  environment  = var.environment

  vpc_id                     = module.network.vpc_id
  private_subnet_ids         = module.network.private_subnet_ids
  public_subnet_ids          = module.network.public_subnet_ids
  alb_security_group_id      = module.network.alb_security_group_id
  backend_security_group_id  = module.network.backend_security_group_id

  ecs_task_role_arn      = module.iam.ecs_task_role_arn
  ecs_execution_role_arn = module.iam.ecs_execution_role_arn
  github_actions_role_arn = module.iam.github_actions_role_arn

  backend_image = var.backend_image
  backend_port  = var.backend_port
  redis_port    = var.redis_port

  ecs_cluster_name = var.ecs_cluster_name != "" ? var.ecs_cluster_name : "${local.name_prefix}-cluster"
  ecs_service_name = var.ecs_service_name

  ecs_task_cpu    = var.ecs_task_cpu
  ecs_task_memory = var.ecs_task_memory

  ecs_desired_count = var.ecs_desired_count
  ecs_min_capacity  = var.ecs_min_capacity
  ecs_max_capacity  = var.ecs_max_capacity

  domain_name     = var.domain_name
  certificate_arn = var.certificate_arn

  database_secret_arn = module.database.secret_arn
  app_secrets_arn     = module.secrets.secret_arn

  tags = local.common_tags
}
