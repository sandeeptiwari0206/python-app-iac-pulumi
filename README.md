<div align="center">

# ⚡ Python App — Infrastructure as Code with Pulumi

### Full-stack Python application deployed on AWS using Pulumi IaC + Jenkins CI/CD

[![Python](https://img.shields.io/badge/Python-59.4%25-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://github.com/sandeeptiwari0206/python-app-iac-pulumi)
[![Pulumi](https://img.shields.io/badge/Pulumi-IaC-8A3391?style=for-the-badge&logo=pulumi&logoColor=white)](https://www.pulumi.com/)
[![AWS](https://img.shields.io/badge/AWS-Cloud-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-D24939?style=for-the-badge&logo=jenkins&logoColor=white)](https://www.jenkins.io/)

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Infrastructure (Pulumi)](#-infrastructure-pulumi)
- [Getting Started](#-getting-started)
- [Environment Variables & Secrets](#-environment-variables--secrets)
- [Docker & Compose](#-docker--compose)
- [Kubernetes](#-kubernetes)
- [Author](#-author)

---

## 📖 Overview

This project demonstrates a **production-grade Python web application** provisioned entirely with **Pulumi Infrastructure as Code** — using real Python code instead of YAML to define and manage cloud resources on AWS.

Unlike traditional YAML-based IaC tools (like CloudFormation or Terraform HCL), Pulumi lets you write **type-safe, testable, and reusable infrastructure** using the same language as your application code.

The full stack includes:
- A **Python backend** (REST API) and **HTML/JS frontend**
- **Dockerized** services orchestrated with `docker-compose`
- **Jenkins pipeline** for automated build → push → deploy
- **Pulumi** for provisioning AWS infrastructure (VPC, EC2, Security Groups, etc.)
- **Kubernetes manifests** for optional K8s deployment

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   GitHub Repository                  │
│                        │                            │
│              Push to main branch                     │
└────────────────────────┼────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                  Jenkins Pipeline                    │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Checkout   │→ │ Build & Push │→ │  Deploy   │  │
│  │    Code     │  │  to DockerHub│  │  on EC2   │  │
│  └─────────────┘  └──────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               AWS Infrastructure (Pulumi)            │
│                                                     │
│   VPC ──► Subnet ──► Security Group ──► EC2         │
│                                                     │
│   ┌──────────────────────────────────────────┐      │
│   │              EC2 Instance                │      │
│   │  ┌──────────────┐   ┌────────────────┐  │      │
│   │  │   Backend    │   │    Frontend    │  │      │
│   │  │  :8000       │◄──│    :80 (Nginx) │  │      │
│   │  └──────────────┘   └────────────────┘  │      │
│   └──────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
python-app-iac-pulumi/
│
├── backend/                  # Python REST API (Flask/FastAPI)
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                 # HTML/JS frontend served via Nginx
│   ├── index.html
│   ├── app.js
│   └── Dockerfile
│
├── infra-pulumi/             # Pulumi IaC — AWS infrastructure in Python
│   ├── __main__.py           # VPC, EC2, Security Groups, etc.
│   ├── Pulumi.yaml
│   └── requirements.txt
│
├── infra/                    # Supporting infra scripts / configs
│
├── k8s/                      # Kubernetes manifests (optional)
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── service.yaml
│
├── .github/workflows/        # GitHub Actions workflows
│
├── Jenkinsfile               # Jenkins declarative pipeline
├── docker-compose.yml        # Multi-service local/EC2 orchestration
└── .gitignore
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python, HTML, JavaScript |
| **IaC** | Pulumi (Python SDK) |
| **Cloud** | AWS (EC2, VPC, Security Groups) |
| **Containers** | Docker, Docker Compose |
| **CI/CD** | Jenkins (Declarative Pipeline) |
| **Container Registry** | Docker Hub |
| **Orchestration** | Kubernetes (optional) |
| **Web Server** | Nginx |

---

## 🔄 CI/CD Pipeline

The Jenkins pipeline automates the full build-push-deploy cycle across two agents:

```
main branch push
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  Stage 1: Checkout, Build & Push  (built-in node)        │
│  ─────────────────────────────────────────────────────   │
│  • Checkout source code                                  │
│  • docker build backend  → sandeeptiwari0206/python-     │
│                             backend:<BUILD_NUMBER>        │
│  • docker build frontend → sandeeptiwari0206/python-     │
│                             frontend:<BUILD_NUMBER>       │
│  • docker login DockerHub (via Jenkins credential)       │
│  • docker push both images                               │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  Stage 2: Deploy on EC2  (ec2 agent)                     │
│  ─────────────────────────────────────────────────────   │
│  • docker pull backend:<BUILD_NUMBER>                    │
│  • docker pull frontend:<BUILD_NUMBER>                   │
│  • docker compose down                                   │
│  • docker compose up -d  (IMAGE_TAG=<BUILD_NUMBER>)      │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  Stage 3: Cleanup (ec2 agent)                            │
│  ─────────────────────────────────────────────────────   │
│  • docker image prune -af  (remove stale images)         │
│  • docker system df        (log disk usage)              │
└──────────────────────────────────────────────────────────┘
```

### Jenkins Setup Requirements

| Requirement | Details |
|-------------|---------|
| Jenkins Agent labels | `built-in`, `ec2` |
| Credential ID | `dockerhub-pass` (Secret Text) |
| Docker installed | On both agents |
| EC2 SSH access | Configured in Jenkins node settings |

---

## ☁️ Infrastructure (Pulumi)

The `infra-pulumi/` directory provisions all AWS resources using the **Pulumi Python SDK** — no YAML, no HCL, pure Python.

### Resources Provisioned

```python
# infra-pulumi/__main__.py (summary)

vpc              → Custom VPC with CIDR block
subnet           → Public subnet
internet_gateway → Enables outbound internet access
route_table      → Routes traffic through IGW
security_group   → Allows HTTP (80), API (8000), SSH (22)
ec2_instance     → t2.micro / t3.small with user_data bootstrap
```

### Deploy Infrastructure

```bash
# Install Pulumi CLI
curl -fsSL https://get.pulumi.com | sh

# Configure AWS credentials
aws configure

# Deploy
cd infra-pulumi
pip install -r requirements.txt
pulumi stack init dev
pulumi up
```

### Tear Down

```bash
pulumi destroy
pulumi stack rm dev
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- AWS CLI configured (`aws configure`)
- Pulumi CLI
- Jenkins (for CI/CD)

### 1. Clone the Repository

```bash
git clone https://github.com/sandeeptiwari0206/python-app-iac-pulumi.git
cd python-app-iac-pulumi
```

### 2. Run Locally with Docker Compose

```bash
# Build and start all services
IMAGE_TAG=local docker compose up --build

# Backend available at:  http://localhost:8000
# Frontend available at: http://localhost:80
```

### 3. Provision AWS Infrastructure

```bash
cd infra-pulumi
pip install -r requirements.txt
pulumi up
```

### 4. Deploy via Jenkins

Push to `main` branch — the Jenkins pipeline handles the rest automatically.

---

## 🔐 Environment Variables & Secrets

| Variable | Where | Description |
|----------|-------|-------------|
| `IMAGE_TAG` | `docker-compose.yml` | Docker image tag (set by Jenkins `BUILD_NUMBER`) |
| `ENV` | Backend container | Runtime environment (`production`) |
| `dockerhub-pass` | Jenkins Credentials | Docker Hub access token |
| `AWS_ACCESS_KEY_ID` | Pulumi / AWS CLI | AWS credentials for IaC |
| `AWS_SECRET_ACCESS_KEY` | Pulumi / AWS CLI | AWS credentials for IaC |

> ⚠️ Never commit secrets to the repository. Use Jenkins credentials store or AWS Secrets Manager.

---

## 🐳 Docker & Compose

### Services

```yaml
services:
  backend:
    image: sandeeptiwari0206/python-backend:${IMAGE_TAG}
    ports: ["8000:8000"]
    environment: [ENV=production]
    networks: [python-net]

  frontend:
    image: sandeeptiwari0206/python-frontend:${IMAGE_TAG}
    ports: ["80:80"]
    depends_on: [backend]
    networks: [python-net]
```

### Docker Hub Images

| Image | Link |
|-------|------|
| `sandeeptiwari0206/python-backend` | [Docker Hub](https://hub.docker.com/u/sandeeptiwari0206) |
| `sandeeptiwari0206/python-frontend` | [Docker Hub](https://hub.docker.com/u/sandeeptiwari0206) |

---

## ☸️ Kubernetes

Kubernetes manifests are available in the `k8s/` directory for deploying to any K8s cluster (EKS, GKE, etc.).

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services
```

---

## 👨‍💻 Author

<div align="center">

**Sandeep Tiwari** — Cloud Engineer & DevOps Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sandeep-tiwari-616a33116/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/sandeeptiwari0206)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-3b82f6?style=flat-square)](https://your-portfolio-url.com)

📍 Jaipur, Rajasthan, India

</div>

---

<div align="center">

⭐ **If this project helped you, give it a star!**

</div>
