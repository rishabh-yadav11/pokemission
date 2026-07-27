output "configure_kubectl" {
  description = "Run this to configure kubectl"
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.aws_region}"
}

output "ecr_frontend_url" {
  description = "ECR repository URL for frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecr_mission_service_url" {
  description = "ECR repository URL for mission-service image"
  value       = aws_ecr_repository.mission_service.repository_url
}

output "ecr_subscriber_service_url" {
  description = "ECR repository URL for subscriber-service image"
  value       = aws_ecr_repository.subscriber_service.repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (host)"
  value       = aws_db_instance.main.address
}

output "db_secret_arn" {
  description = "Secrets Manager ARN for DB credentials"
  value       = aws_secretsmanager_secret.db.arn
}

output "create_db_secret_command" {
  description = "Run this after terraform apply to create the K8s secret"
  value = "kubectl create secret generic db-secret -n pokemission --from-literal=DATABASE_URL=\"postgresql+asyncpg://${var.db_username}:${random_password.db.result}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${var.db_name}\""
  sensitive = true
}

output "login_to_ecr_command" {
  description = "Run this to authenticate Docker with ECR"
  value = "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

data "aws_caller_identity" "current" {}
