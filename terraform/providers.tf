# Terraform configuration and provider version constraints
# Ensures compatible provider versions are used across the project
terraform {
  required_version = ">= 1.5"

  # Encrypted remote state (critical #7): no local tfstate with secrets.
  backend "s3" {
    bucket         = "pokemission-tfstate-<ACCOUNT_ID>"
    key            = "pokemission/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "pokemission-tfstate-locks"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

# AWS provider configuration - main provider for all AWS resources
provider "aws" {
  region = var.aws_region
}

# Data source to fetch authentication token for EKS cluster
# Required by Kubernetes and Helm providers to authenticate with the cluster
data "aws_eks_cluster_auth" "main" {
  name = aws_eks_cluster.main.name
}

# Kubernetes provider - enables management of Kubernetes resources
# Uses EKS cluster endpoint and authentication token for connection
provider "kubernetes" {
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.main.token
}

# Helm provider - enables deployment of Helm charts to the EKS cluster
# Used to deploy AWS Load Balancer Controller and other Kubernetes add-ons
provider "helm" {
  kubernetes {
    host                   = aws_eks_cluster.main.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.main.token
  }
}
