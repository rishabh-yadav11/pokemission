# ECR Repository for Frontend application
# Stores Docker images with automatic vulnerability scanning enabled
resource "aws_ecr_repository" "frontend" {
  name                 = "${local.project}-frontend"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

# ECR Repository for Mission Service (backend microservice)
resource "aws_ecr_repository" "mission_service" {
  name                 = "${local.project}-mission-service"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

# ECR Repository for Subscriber Service (backend microservice)
resource "aws_ecr_repository" "subscriber_service" {
  name                 = "${local.project}-subscriber-service"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}
