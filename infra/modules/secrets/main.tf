# Application secrets for backend
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${var.project_name}-${var.environment}-app-secrets"
  description             = "Application secrets for ${var.project_name}-${var.environment}"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-app-secrets"
  })
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    # API Keys
    RAGIE_API_KEY      = var.ragie_api_key
    OPENAI_API_KEY     = var.openai_api_key
    FRONTEGG_API_KEY   = var.frontegg_api_key
    
    # AWS Credentials
    AWS_ACCESS_KEY_ID     = var.aws_access_key_id
    AWS_SECRET_ACCESS_KEY = var.aws_secret_access_key
    
    # Other secrets
    FRONTEGG_ENCRYPTION_PASSWORD = var.frontegg_encryption_password
    FRONTEGG_CLIENT_ID           = var.frontegg_client_id
    FRONTEGG_APP_ID              = var.frontegg_app_id
    
    # Configuration
    S3_BUCKET                = var.s3_bucket
    AWS_REGION               = var.aws_region
    RAGIE_S3_BUCKET_PREFIX   = var.ragie_s3_bucket_prefix
  })
}
