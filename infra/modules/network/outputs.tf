# Outputs for network module

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

# NAT Gateway outputs disabled (resource commented out)
# output "nat_gateway_ids" {
#   description = "IDs of the NAT Gateways"
#   value       = aws_nat_gateway.main[*].id
# }

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = data.aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = data.aws_subnet.private[*].id
}

output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

# Private route table outputs disabled (resource commented out)
# output "private_route_table_ids" {
#   description = "IDs of the private route tables"
#   value       = aws_route_table.private[*].id
# }

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "backend_security_group_id" {
  description = "ID of the backend security group"
  value       = aws_security_group.backend.id
}

output "database_security_group_id" {
  description = "ID of the database security group"
  value       = aws_security_group.database.id
}
