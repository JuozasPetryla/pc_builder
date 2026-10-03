variable "neon_org_id" {
  description = "Neon organization ID. Select an organization on the Free plan."
  type        = string

  validation {
    condition     = can(regex("^org-[a-z0-9-]+$", var.neon_org_id))
    error_message = "Set a real Neon organization ID starting with org-."
  }
}

variable "app_name" {
  description = "Neon project name prefix."
  type        = string
  default     = "pc-builder"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.app_name))
    error_message = "Use 3–31 lowercase letters, digits or hyphens; begin with a letter."
  }
}
