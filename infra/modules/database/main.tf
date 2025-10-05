# Database module for AI Knowledge Agent infrastructure

# Random password for database
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Secrets Manager secret for database credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.project_name}-${var.environment}-db-credentials"
  description             = "Database credentials for ${var.project_name}-${var.environment}"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-db-secret"
  })
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.database_username
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
    dbname   = aws_db_instance.main.db_name
  })
  
  depends_on = [aws_db_instance.main]
}

    # DB Subnet Group (using public subnets for public access)
    resource "aws_db_subnet_group" "main" {
      name       = "${var.project_name}-${var.environment}-db-subnet-group"
      subnet_ids = var.public_subnet_ids

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  })
}

    # DB Parameter Group
    resource "aws_db_parameter_group" "main" {
      family = "postgres17"
      name   = "${var.project_name}-${var.environment}-db-params"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-db-params"
  })
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-db"

      # Engine
      engine         = "postgres"
      engine_version = "17.4"
      instance_class = var.instance_class

      # Storage - Free tier settings
      allocated_storage     = 20
      max_allocated_storage = 20
      storage_type          = "gp2"
      storage_encrypted     = false

  # Database
  db_name  = var.database_name
  username = var.database_username
  password = random_password.db_password.result

      # Network
      db_subnet_group_name   = aws_db_subnet_group.main.name
      vpc_security_group_ids = [var.database_security_group_id]
      publicly_accessible    = true
      
      # Single AZ deployment
      multi_az = false

      # Backup - 7 day retention
      backup_retention_period = 7
      backup_window          = "03:00-04:00"
      maintenance_window     = "sun:04:00-sun:05:00"

  # Monitoring
  monitoring_interval = var.enable_monitoring ? 60 : 0
  monitoring_role_arn = var.enable_monitoring ? aws_iam_role.rds_enhanced_monitoring[0].arn : null

  # Security
  deletion_protection = var.enable_deletion_protection
  skip_final_snapshot = !var.enable_deletion_protection
  final_snapshot_identifier = var.enable_deletion_protection ? "${var.project_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  # Parameter Group
  parameter_group_name = aws_db_parameter_group.main.name

      # Performance Insights - Disabled for free tier
      performance_insights_enabled = false

      tags = merge(var.tags, {
        Name = "${var.project_name}-${var.environment}-db"
      })
}

# IAM Role for RDS Enhanced Monitoring (if enabled)
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.enable_monitoring ? 1 : 0
  name  = "${var.project_name}-${var.environment}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-rds-monitoring-role"
  })
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count = var.enable_monitoring ? 1 : 0
  role  = aws_iam_role.rds_enhanced_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}
