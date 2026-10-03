terraform {
  required_version = ">= 1.14, < 2.0"

  required_providers {
    neon = {
      source  = "kislerdm/neon"
      version = "0.18.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.9.1"
    }
  }
}

# API key is read from NEON_API_KEY, not tfvars.
provider "neon" {}
