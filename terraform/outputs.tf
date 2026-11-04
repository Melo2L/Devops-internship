output "frontend_url" {
  description = "SecureScan frontend URL"
  value       = "http://localhost:${var.frontend_port}"
}

output "backend_health_url" {
  description = "SecureScan backend health endpoint"
  value       = "http://localhost:${var.backend_port}/health"
}

output "frontend_container_name" {
  description = "Frontend Docker container name"
  value       = docker_container.frontend.name
}

output "backend_container_name" {
  description = "Backend Docker container name"
  value       = docker_container.backend.name
}

output "docker_network_name" {
  description = "SecureScan Docker network"
  value       = docker_network.securescan.name
}
