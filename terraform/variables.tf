variable "aws_region" {
  description = "AWS region"
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  default     = "pokemission"
}

variable "cluster_name" {
  description = "EKS cluster name"
  default     = "pokemission"
}

variable "db_username" {
  description = "RDS PostgreSQL username"
  default     = "pokemissionadmin"
}

variable "db_name" {
  description = "RDS PostgreSQL database name"
  default     = "pokemissiondb"
}
