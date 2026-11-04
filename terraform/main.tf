resource "docker_network" "securescan" {
  name   = var.network_name
  driver = "bridge"
}

resource "docker_volume" "securescan_data" {
  name = "securescan-terraform-data"
}

resource "docker_image" "backend" {
  name         = "${var.backend_image}:${var.image_tag}"
  keep_locally = true
}

resource "docker_image" "frontend" {
  name         = "${var.frontend_image}:${var.image_tag}"
  keep_locally = true
}

resource "docker_container" "backend" {
  name  = "securescan-terraform-backend"
  image = docker_image.backend.image_id

  restart = "unless-stopped"

  ports {
    internal = 8000
    external = var.backend_port
  }

  volumes {
    volume_name    = docker_volume.securescan_data.name
    container_path = "/data"
  }

  networks_advanced {
    name = docker_network.securescan.name
  }

  healthcheck {
    test         = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
    interval     = "10s"
    timeout      = "5s"
    retries      = 5
    start_period = "10s"
  }
}

resource "docker_container" "frontend" {
  name  = "securescan-terraform-frontend"
  image = docker_image.frontend.image_id

  restart = "unless-stopped"

  env = [
    "SECURESCAN_API_INTERNAL_URL=http://securescan-terraform-backend:8000/api"
  ]

  ports {
    internal = 3000
    external = var.frontend_port
  }

  networks_advanced {
    name = docker_network.securescan.name
  }

  depends_on = [
    docker_container.backend
  ]
}
