# Outputs for database module

output "endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
}

output "port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "name" {
  description = "RDS instance database name"
  value       = aws_db_instance.main.db_name
}

output "username" {
  description = "RDS instance username"
  value       = aws_db_instance.main.username
}

output "instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "instance_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.main.arn
}

output "secret_arn" {
  description = "ARN of the database secret in Secrets Manager"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "secret_name" {
  description = "Name of the database secret in Secrets Manager"
  value       = aws_secretsmanager_secret.db_credentials.name
}

output "subnet_group_id" {
  description = "DB subnet group ID"
  value       = aws_db_subnet_group.main.id
}

output "parameter_group_id" {
  description = "DB parameter group ID"
  value       = aws_db_parameter_group.main.id
}
