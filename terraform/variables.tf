# AWS Region - Region where all resources will be created
variable "aws_region" {
  description = "AWS region"
  default     = "ap-south-1"
}

# Project Name - Used as prefix for all resource names
variable "project_name" {
  description = "Project name used for resource naming"
  default     = "pokemission"
}

# EKS Cluster Name - Name of the Kubernetes cluster
variable "cluster_name" {
  description = "EKS cluster name"
  default     = "pokemission"
}

# Database Username - Master username for RDS PostgreSQL
variable "db_username" {
  description = "RDS PostgreSQL username"
  default     = "pokemissionadmin"
}

# Database Name - Initial database created in RDS instance
variable "db_name" {
  description = "RDS PostgreSQL database name"
  default     = "pokemissiondb"
}

# EKS public endpoint allowlist - restrict to operator IPs (override via tfvars)
variable "eks_public_access_cidrs" {
  description = "CIDR blocks allowed to reach the EKS public endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"] # TODO: restrict to operator IPs, e.g. ["203.0.113.10/32"]
}
