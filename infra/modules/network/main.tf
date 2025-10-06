# Network module for AI Knowledge Agent infrastructure

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-igw"
  })
}

# NAT Gateway (for private subnet internet access)
# DISABLED: Not needed since ECS tasks are in public subnets with public IPs
# Saves ~$40/month per NAT Gateway
# resource "aws_eip" "nat" {
#   count  = length(var.availability_zones)
#   domain = "vpc"
# 
#   tags = merge(var.tags, {
#     Name = "${var.project_name}-${var.environment}-nat-eip-${count.index + 1}"
#   })
# 
#   depends_on = [aws_internet_gateway.main]
# }
# 
# resource "aws_nat_gateway" "main" {
#   count         = length(var.availability_zones)
#   allocation_id = aws_eip.nat[count.index].id
#   subnet_id     = data.aws_subnet.public[count.index].id
# 
#   tags = merge(var.tags, {
#     Name = "${var.project_name}-${var.environment}-nat-${count.index + 1}"
#   })
# 
#   depends_on = [aws_internet_gateway.main]
# }

# Data sources for existing subnets
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [aws_vpc.main.id]
  }
  
  filter {
    name   = "tag:Type"
    values = ["Public"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [aws_vpc.main.id]
  }
  
  filter {
    name   = "tag:Type"
    values = ["Private"]
  }
}

# Data sources for individual subnets
data "aws_subnet" "public" {
  count = length(data.aws_subnets.public.ids)
  id    = data.aws_subnets.public.ids[count.index]
}

data "aws_subnet" "private" {
  count = length(data.aws_subnets.private.ids)
  id    = data.aws_subnets.private.ids[count.index]
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-public-rt"
  })
}

# Route Table for Private Subnets
# DISABLED: Not needed since we're not using private subnets or NAT Gateway
# resource "aws_route_table" "private" {
#   count  = length(data.aws_subnet.private)
#   vpc_id = aws_vpc.main.id
# 
#   route {
#     cidr_block     = "0.0.0.0/0"
#     nat_gateway_id = aws_nat_gateway.main[count.index].id
#   }
# 
#   tags = merge(var.tags, {
#     Name = "${var.project_name}-${var.environment}-private-rt-${count.index + 1}"
#   })
# }

# Route Table Associations for Public Subnets
resource "aws_route_table_association" "public" {
  count = length(data.aws_subnet.public)

  subnet_id      = data.aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route Table Associations for Private Subnets
# DISABLED: Not needed since we're not using private subnets
# resource "aws_route_table_association" "private" {
#   count = length(data.aws_subnet.private)
# 
#   subnet_id      = data.aws_subnet.private[count.index].id
#   route_table_id = aws_route_table.private[count.index].id
# }

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-${var.environment}-alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "backend" {
  name_prefix = "${var.project_name}-${var.environment}-backend-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Backend port from ALB"
    from_port       = 8001
    to_port         = 8001
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-backend-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "database" {
  name_prefix = "${var.project_name}-${var.environment}-database-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "PostgreSQL from backend"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  ingress {
    description = "PostgreSQL from anywhere (for DBeaver/psql access)"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-database-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}
