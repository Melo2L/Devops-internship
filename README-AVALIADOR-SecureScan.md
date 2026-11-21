## Requisitos

- Git instalado.
- Docker instalado.
- Docker Compose v2.
- Ligação à Internet.

Será necessário criar apenas uma password local para o Grafana.

## Passo a passo


### 1. Descarregar o projeto

Abra um terminal e execute:

```bash
git clone --branch main --single-branch https://github.com/Melo2L/Devops-internship.git
cd Devops-internship
```


### 2. Configurar o ambiente

```bash
mkdir -p secrets
cat > .env <<'EOF'
GRAFANA_ADMIN_PASSWORD=EscolhaUmaPasswordForte
SECURESCAN_IMAGE_TAG=latest
EOF
printf '%s\n' 'smtp-nao-configurado' > secrets/smtp_password
docker volume create securescan-trivy-cache
```


No ficheiro `.env`, substitua `EscolhaUmaPasswordForte` por uma password à sua escolha. Guarde-a: será usada para entrar no Grafana.

### 3. Iniciar a aplicação
cd ~/Downloads/securescan-melo-clean && \
git add README.md README-AVALIADOR-SecureScan.md && \
git diff --cached --check && \
echo "===== FICHEIROS PREPARADOS =====" && \
git diff --cached --stat && \
echo && \
git status --short


Execute:

```bash
docker compose pull
docker compose up -d --no-build
```


Aguarde até os contentores estarem iniciados. Para confirmar, execute:

```bash
docker compose ps
```


### 4. Aceder à aplicação


- **SecureScan:** http://localhost:3000
- **API:** http://localhost:8000/health
- **Grafana:** http://localhost:3001
- **Prometheus:** http://localhost:9090
- **Alertmanager:** http://localhost:9093

No Grafana, entre com:

- Utilizador: admin
- Password: a password que definiu no passo 2.


Nota: foi criada uma configuração SMTP de exemplo para permitir iniciar os serviços sem usar credenciais privadas. O envio real de emails de alertas não ficará configurado.
