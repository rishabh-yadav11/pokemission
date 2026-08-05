# Output: kubectl configuration command
# Run this to connect kubectl to the EKS cluster
output "configure_kubectl" {
  description = "Run this to configure kubectl"
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.aws_region}"
}

# Output: Frontend ECR repository URL
# Use this URL to push Docker images for the frontend
output "ecr_frontend_url" {
  description = "ECR repository URL for frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}

# Output: Mission Service ECR repository URL
# Use this URL to push Docker images for the backend mission-service
output "ecr_mission_service_url" {
  description = "ECR repository URL for mission-service image"
  value       = aws_ecr_repository.mission_service.repository_url
}

# Output: Subscriber Service ECR repository URL
# Use this URL to push Docker images for the backend subscriber-service
output "ecr_subscriber_service_url" {
  description = "ECR repository URL for subscriber-service image"
  value       = aws_ecr_repository.subscriber_service.repository_url
}

# Output: RDS endpoint address
# Database connection host for applications
output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (host)"
  value       = aws_db_instance.main.address
}

# Output: Secrets Manager ARN
# Reference to retrieve database credentials programmatically
output "db_secret_arn" {
  description = "Secrets Manager ARN for DB credentials"
  value       = aws_secretsmanager_secret.db.arn
}

# Output: Kubernetes secret creation command
# Run this to create a K8s secret with database URL (marked as sensitive)
output "create_db_secret_command" {
  description = "Run this after terraform apply to create the K8s secret"
  value = "kubectl create secret generic db-secret -n pokemission --from-literal=DATABASE_URL=\"postgresql+asyncpg://${var.db_username}:${random_password.db.result}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${var.db_name}\""
  sensitive = true
}

# Output: ECR login command
# Run this to authenticate Docker with ECR before pushing images
output "login_to_ecr_command" {
  description = "Run this to authenticate Docker with ECR"
  value = "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

# Data source to fetch current AWS account ID for ECR login command
data "aws_caller_identity" "current" {}
