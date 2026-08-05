# Local values for consistent naming and tagging across all resources
# These locals are referenced throughout the project to maintain naming consistency
locals {
  project = var.project_name
  tags = {
    Project = var.project_name
    Managed = "Terraform"
  }
}
