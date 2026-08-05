# Data source to fetch available AZs in the region
# Used to distribute subnets across multiple availability zones for high availability
data "aws_availability_zones" "available" {
  state = "available"
}

# Main VPC - Creates the network foundation for all resources
# Enables DNS support for instance hostname resolution
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.tags, { Name = "${local.project}-vpc" })
}

# Public subnets - Subnets with internet gateway route for public-facing resources
# Auto-assigns public IPs to instances; tagged for Kubernetes ELB use
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.tags, {
    Name = "${local.project}-public-${count.index + 1}"
    "kubernetes.io/role/elb" = "1"
  })
}

# Private subnets - Isolated subnets for internal resources (EKS nodes, RDS)
# No direct internet access; uses NAT gateway for outbound traffic
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 2}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.tags, {
    Name = "${local.project}-private-${count.index + 1}"
    "kubernetes.io/role/internal-elb" = "1"
  })
}

# Internet Gateway - Provides internet access for public subnets
# Required for public subnet resources to communicate with the internet
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.tags, { Name = "${local.project}-igw" })
}

# Elastic IP - Static public IP for NAT Gateway
# Allows private subnet resources to access internet while remaining private
resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = merge(local.tags, { Name = "${local.project}-nat-eip" })
}

# NAT Gateway - Enables private subnet resources to access internet
# Placed in public subnet; routes outbound traffic from private subnets
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  tags          = merge(local.tags, { Name = "${local.project}-nat" })
}

# Public route table - Routes traffic from public subnets to internet gateway
# Enables resources in public subnets to reach the internet
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.tags, { Name = "${local.project}-public-rt" })
}

# Public subnet route associations - Links public subnets to public route table
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private route table - Routes traffic from private subnets to NAT Gateway
# Allows private resources to access internet without being directly exposed
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = merge(local.tags, { Name = "${local.project}-private-rt" })
}

# Private subnet route associations - Links private subnets to private route table
resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
