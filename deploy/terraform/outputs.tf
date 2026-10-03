output "neon_project_id" {
  value = neon_project.database.id
}

output "database_url" {
  description = "Paste into DATABASE_URL in the Render Blueprint prompt; Terraform state also contains this secret."
  value = format(
    "postgresql+psycopg://%s:%s@%s/%s?sslmode=require&connect_timeout=15",
    urlencode(neon_project.database.database_user),
    urlencode(neon_project.database.database_password),
    neon_project.database.database_host,
    urlencode(neon_project.database.database_name),
  )
  sensitive = true
}
