# Random password generator for database credentials
# Creates a secure 24-character password without special characters
resource "random_password" "db" {
  length  = 24
  special = false
}

# Random ID for unique secret naming - prevents naming conflicts
resource "random_id" "secret_suffix" {
  byte_length = 4
}

# Secrets Manager secret container for database credentials
resource "aws_secretsmanager_secret" "db" {
  name = "${local.project}-db-credentials-${random_id.secret_suffix.hex}"
  tags = local.tags
}

# Secrets Manager secret version - Stores actual credentials JSON
# Contains: username, password, dbname, host, port, and full database_url
resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id

  secret_string = jsonencode({
    username     = var.db_username
    password     = random_password.db.result
    dbname       = var.db_name
    host         = aws_db_instance.main.address
    port         = aws_db_instance.main.port
    database_url = "postgresql+asyncpg://${var.db_username}:${random_password.db.result}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${var.db_name}"
  })
}
