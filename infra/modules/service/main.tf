# Service module for AI Knowledge Agent infrastructure

# ECR Repository
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-${var.environment}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-backend-ecr"
  })
}

# ECR Repository Policy
resource "aws_ecr_repository_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowPushPull"
        Effect = "Allow"
        Principal = {
          AWS = var.github_actions_role_arn
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
      }
    ]
  })
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = var.ecs_cluster_name

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs.name
      }
    }
  }

  tags = merge(var.tags, {
    Name = var.ecs_cluster_name
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.project_name}-${var.environment}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-logs"
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-${var.environment}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn           = var.ecs_task_role_arn
  
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "migration"
      image     = var.backend_image != "" ? var.backend_image : "${aws_ecr_repository.backend.repository_url}:latest"
      essential = false
      cpu       = 256
      memory    = 512
      command   = ["uv", "run", "python", "-m", "alembic", "upgrade", "head"]
      workingDirectory = "/workspace/packages/database"
      environment = [
        {
          name  = "NODE_ENV"
          value = var.environment
        },
        {
          name  = "PORT"
          value = tostring(var.backend_port)
        },
        {
          name  = "REDIS_URL"
          value = "redis://localhost:6379"
        },
        {
          name  = "LOG_LEVEL"
          value = "warn"
        },
        {
          name  = "CORS_ORIGIN"
          value = "https://get-convinced.vercel.app"
        },
        {
          name  = "HEALTH_CHECK_PATH"
          value = "/health"
        },
        {
          name  = "MAX_REQUEST_SIZE"
          value = "10485760"
        },
        {
          name  = "REQUEST_TIMEOUT"
          value = "30000"
        },
        {
          name  = "FRONTEGG_APP_URL"
          value = "http://localhost:3000"
        },
        {
          name  = "FRONTEGG_BASE_URL"
          value = "https://app-griklxnnsxag.frontegg.com"
        },
        {
          name  = "FRONTEGG_CLIENT_ID"
          value = "843bbe93-eb8d-49cf-b53b-90bd60265c82"
        },
        {
          name  = "FRONTEGG_APP_ID"
          value = "fcdbcb06-7c9d-463d-9b04-c12e2f1b889a"
        },
        {
          name  = "FRONTEGG_COOKIE_NAME"
          value = "fe_session"
        },
        {
          name  = "FRONTEGG_HOSTED_LOGIN"
          value = "true"
        },
        {
          name  = "S3_BUCKET"
          value = "get-convinced-dev"
        },
        {
          name  = "AWS_REGION"
          value = "ap-south-1"
        },
        {
          name  = "RAGIE_S3_BUCKET_PREFIX"
          value = "ragie-docs"
        }
      ]
      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = var.database_secret_arn
        },
        {
          name      = "RAGIE_API_KEY"
          valueFrom = "${var.app_secrets_arn}:RAGIE_API_KEY::"
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = "${var.app_secrets_arn}:OPENAI_API_KEY::"
        },
        {
          name      = "FRONTEGG_API_KEY"
          valueFrom = "${var.app_secrets_arn}:FRONTEGG_API_KEY::"
        },
        {
          name      = "FRONTEGG_ENCRYPTION_PASSWORD"
          valueFrom = "${var.app_secrets_arn}:FRONTEGG_ENCRYPTION_PASSWORD::"
        },
        {
          name      = "AWS_ACCESS_KEY_ID"
          valueFrom = "${var.app_secrets_arn}:AWS_ACCESS_KEY_ID::"
        },
        {
          name      = "AWS_SECRET_ACCESS_KEY"
          valueFrom = "${var.app_secrets_arn}:AWS_SECRET_ACCESS_KEY::"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "migration"
        }
      }
    },
    {
      name  = "backend"
      image = var.backend_image != "" ? var.backend_image : "${aws_ecr_repository.backend.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = var.backend_port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "NODE_ENV"
          value = var.environment
        },
        {
          name  = "PORT"
          value = tostring(var.backend_port)
        },
        {
          name  = "REDIS_URL"
          value = "redis://localhost:6379"
        },
        {
          name  = "LOG_LEVEL"
          value = "warn"
        },
        {
          name  = "CORS_ORIGIN"
          value = "https://get-convinced.vercel.app"
        },
        {
          name  = "HEALTH_CHECK_PATH"
          value = "/health"
        },
        {
          name  = "MAX_REQUEST_SIZE"
          value = "10485760"
        },
        {
          name  = "REQUEST_TIMEOUT"
          value = "30000"
        },
        {
          name  = "FRONTEGG_APP_URL"
          value = "http://localhost:3000"
        },
        {
          name  = "FRONTEGG_BASE_URL"
          value = "https://app-griklxnnsxag.frontegg.com"
        },
        {
          name  = "FRONTEGG_CLIENT_ID"
          value = "843bbe93-eb8d-49cf-b53b-90bd60265c82"
        },
        {
          name  = "FRONTEGG_APP_ID"
          value = "fcdbcb06-7c9d-463d-9b04-c12e2f1b889a"
        },
        {
          name  = "FRONTEGG_COOKIE_NAME"
          value = "fe_session"
        },
        {
          name  = "FRONTEGG_HOSTED_LOGIN"
          value = "true"
        },
        {
          name  = "S3_BUCKET"
          value = "get-convinced-dev"
        },
        {
          name  = "AWS_REGION"
          value = "ap-south-1"
        },
        {
          name  = "RAGIE_S3_BUCKET_PREFIX"
          value = "ragie-docs"
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = var.database_secret_arn
        },
        {
          name      = "RAGIE_API_KEY"
          valueFrom = "${var.app_secrets_arn}:RAGIE_API_KEY::"
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = "${var.app_secrets_arn}:OPENAI_API_KEY::"
        },
        {
          name      = "FRONTEGG_API_KEY"
          valueFrom = "${var.app_secrets_arn}:FRONTEGG_API_KEY::"
        },
        {
          name      = "FRONTEGG_ENCRYPTION_PASSWORD"
          valueFrom = "${var.app_secrets_arn}:FRONTEGG_ENCRYPTION_PASSWORD::"
        },
        {
          name      = "AWS_ACCESS_KEY_ID"
          valueFrom = "${var.app_secrets_arn}:AWS_ACCESS_KEY_ID::"
        },
        {
          name      = "AWS_SECRET_ACCESS_KEY"
          valueFrom = "${var.app_secrets_arn}:AWS_SECRET_ACCESS_KEY::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "backend"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "curl -f http://localhost:${var.backend_port}/health || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      dependsOn = [
        {
          containerName = "migration"
          condition     = "SUCCESS"
        },
        {
          containerName = "redis"
          condition     = "START"
        }
      ]
    },
    {
      name  = "redis"
      image = "redis:7-alpine"

      portMappings = [
        {
          containerPort = var.redis_port
          protocol      = "tcp"
        }
      ]

      command = [
        "redis-server",
        "--appendonly",
        "no",
        "--maxmemory",
        "256mb",
        "--maxmemory-policy",
        "allkeys-lru"
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "redis"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "redis-cli ping"
        ]
        interval = 30
        timeout  = 5
        retries  = 3
      }
    }
  ])

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-backend-task"
  })
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb"
  })
}

# Target Group
resource "aws_lb_target_group" "backend" {
  name        = "${var.project_name}-${var.environment}-tg"
  port        = var.backend_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-tg"
  })
}

# ACM Certificate for HTTPS
resource "aws_acm_certificate" "backend" {
  domain_name       = "*.getconvinced.ai"
  validation_method = "DNS"

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-certificate"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# ALB Listener for HTTPS
resource "aws_lb_listener" "backend_https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.backend.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb-listener-https"
  })
}

# ALB Listener for HTTP (redirect to HTTPS)
resource "aws_lb_listener" "backend_http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb-listener-http"
  })
}


# ECS Service
resource "aws_ecs_service" "backend" {
  name            = var.ecs_service_name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [var.backend_security_group_id]
    subnets          = var.private_subnet_ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = var.backend_port
  }

  depends_on = [aws_lb_listener.backend_https]

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-backend-service"
  })

  lifecycle {
    ignore_changes = [task_definition]
  }
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "backend" {
  max_capacity       = var.ecs_max_capacity
  min_capacity       = var.ecs_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-autoscaling-target"
  })
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "${var.project_name}-${var.environment}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

# Auto Scaling Policy - Memory
resource "aws_appautoscaling_policy" "backend_memory" {
  name               = "${var.project_name}-${var.environment}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

# Data sources
data "aws_region" "current" {}
