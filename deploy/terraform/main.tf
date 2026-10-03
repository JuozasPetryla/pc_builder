resource "random_id" "suffix" {
  byte_length = 3
}

locals {
  service_name = "${var.app_name}-${random_id.suffix.hex}"
}

resource "neon_project" "database" {
  name                      = local.service_name
  org_id                    = var.neon_org_id
  region_id                 = "aws-eu-central-1"
  pg_version                = 17
  history_retention_seconds = 21600
  autoscaling_limit_min_cu  = 0.25
  autoscaling_limit_max_cu  = 0.25
  suspend_timeout_seconds   = 300

  branch {
    name          = "production"
    database_name = "pc_builder"
    role_name     = "pc_builder"
  }

  primary_compute {
    autoscaling_limit_min_cu = 0.25
    autoscaling_limit_max_cu = 0.25
    suspend_timeout_seconds  = 300
  }

  lifecycle {
    prevent_destroy = true
  }
}
