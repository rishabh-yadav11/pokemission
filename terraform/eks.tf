# IAM role for EKS cluster - Provides permissions for EKS control plane
# Allows EKS service to assume this role for managing cluster resources
resource "aws_iam_role" "eks_cluster" {
  name = "${local.project}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.tags
}

# Attach AmazonEKSClusterPolicy - Required for EKS cluster to manage AWS resources
resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

# Attach AmazonEKSVPCResourceController - Allows EKS to manage VPC resources (ENIs, security groups)
resource "aws_iam_role_policy_attachment" "eks_cluster_vpc_resource" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster.name
}

# EKS Cluster - The main Kubernetes control plane
# Uses version 1.30; private endpoint + restricted public access + audit logs + KMS
resource "aws_kms_key" "eks" {
  description             = "EKS cluster secret encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true
  tags                    = local.tags
}

resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.30"

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.key_arn
    }
    resources = ["secrets"]
  }

  # Network configuration - uses both public and private subnets
  vpc_config {
    subnet_ids              = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = var.eks_public_access_cidrs
  }

  tags = local.tags
}

# IAM role for EKS worker nodes - Provides permissions for EC2 instances in the node group
resource "aws_iam_role" "eks_nodes" {
  name = "${local.project}-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.tags
}

# Attach AmazonEKSWorkerNodePolicy - Required for worker nodes to join the cluster
resource "aws_iam_role_policy_attachment" "eks_nodes_worker" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

# Attach AmazonEKS_CNI_Policy - Required for Pod networking (CNI plugin)
resource "aws_iam_role_policy_attachment" "eks_nodes_cni" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

# Attach AmazonEC2ContainerRegistryReadOnly - Allows nodes to pull images from ECR
resource "aws_iam_role_policy_attachment" "eks_nodes_registry" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# Attach AmazonSSMManagedInstanceCore - Allows SSM Session Manager access to nodes
resource "aws_iam_role_policy_attachment" "eks_nodes_ssm" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = aws_iam_role.eks_nodes.name
}

# EKS Node Group - Manages worker nodes in the cluster
# Uses t3.small instances (cost-effective for dev); placed in private subnets
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${local.project}-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  instance_types = ["t3.small"]
  capacity_type  = "ON_DEMAND"

  # Auto-scaling configuration - fixed size of 2 nodes
  scaling_config {
    desired_size = 2
    max_size     = 2
    min_size     = 2
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_nodes_worker,
    aws_iam_role_policy_attachment.eks_nodes_cni,
    aws_iam_role_policy_attachment.eks_nodes_registry,
  ]

  tags = local.tags
}

# VPC CNI Addon - Amazon's native networking plugin for Kubernetes pods
resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "vpc-cni"
}

# CoreDNS Addon - Provides DNS resolution within the cluster
resource "aws_eks_addon" "coredns" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "coredns"
}

# kube-proxy Addon - Maintains network rules on each node for pod communication
resource "aws_eks_addon" "kube_proxy" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "kube-proxy"
}
