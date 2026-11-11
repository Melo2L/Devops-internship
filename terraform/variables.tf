variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "sha-7cf3299"
}

variable "frontend_image" {
  description = "SecureScan frontend image in GHCR"
  type        = string
  default     = "ghcr.io/melo2l/devops-internship-frontend"
}

variable "backend_image" {
  description = "SecureScan backend image in GHCR"
  type        = string
  default     = "ghcr.io/melo2l/devops-internship-backend"
}

variable "frontend_port" {
  description = "Host port exposed by the frontend"
  type        = number
  default     = 3100
}

variable "backend_port" {
  description = "Host port exposed by the backend"
  type        = number
  default     = 8100
}

variable "network_name" {
  description = "Dedicated Docker network for SecureScan"
  type        = string
  default     = "securescan-network"
}
