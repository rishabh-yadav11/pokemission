# DB Subnet Group - Defines which subnets RDS can use
# Places RDS in private subnets for security
resource "aws_db_subnet_group" "main" {
  name       = "${local.project}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  tags       = local.tags
}

# RDS Security Group - Controls network access to the database
# Allows PostgreSQL port 5432 from anywhere within the VPC
resource "aws_security_group" "rds" {
  name        = "${local.project}-rds-sg"
  description = "Allow PostgreSQL from VPC CIDR"
  vpc_id      = aws_vpc.main.id

  # Inbound rule - PostgreSQL access from VPC
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  # Outbound rule - Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

# RDS PostgreSQL Instance - Managed relational database
# PostgreSQL 16.14 on t4g.micro (cost-effective for dev/test)
resource "aws_db_instance" "main" {
  identifier     = "${local.project}-db"
  engine         = "postgres"
  engine_version = "16.14"

  instance_class    = "db.t4g.micro"
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  # Database credentials from variables and random password
  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Backup and maintenance windows
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  skip_final_snapshot = true
  publicly_accessible = false

  tags = local.tags
}
