locals {
  project = var.project_name
  tags = {
    Project = var.project_name
    Managed = "Terraform"
  }
}
