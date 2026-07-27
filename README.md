<div align="center">
  <h1>⚡ PokéMission</h1>
  <p><strong>A Pokémon data explorer with subscription alerts — deployed on AWS EKS</strong></p>

  <p>
    <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react" alt="React 18">
    <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql" alt="PostgreSQL 16">
    <img src="https://img.shields.io/badge/Kubernetes-EKS-326CE5?logo=kubernetes" alt="EKS">
    <img src="https://img.shields.io/badge/Terraform-1.5+-844FBA?logo=terraform" alt="Terraform">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  </p>
</div>

---

## Overview

**PokéMission** syncs Pokémon data from the [PokéAPI](https://pokeapi.co) into a PostgreSQL database and serves it through a React dashboard. Users can browse generations, explore Pokémon stats, and subscribe to email alerts when new content is discovered.

Three microservices running on **AWS EKS**, provisioned with **Terraform**:

- **Frontend** — React SPA with Tailwind CSS, Recharts, and React Router
- **Mission Service** — FastAPI that syncs and serves Pokémon/generation data
- **Subscriber Service** — FastAPI that manages subscriptions and pushes alerts

---

## Architecture

```
                         ┌──────────────┐
                         │   Frontend   │  React + Vite served by nginx
                         │  :80         │  (EKS pod)
                         └──────┬───────┘
                                │
                       ┌────────┴────────┐
                       │     AWS ALB     │  Application Load Balancer
                       │  (Ingress)      │  (auto-provisioned)
                       └────────┬────────┘
                                │
                 ┌──────────────┼──────────────┐
                 │              │              │
        ┌────────┴──────┐ ┌────┴─────────┐    │
        │ Mission-Svc   │ │ Subscriber   │    │
        │ FastAPI :8000 │ │ FastAPI :8000 │    │
        │ /api/mission* │ │ /api/subscriber│   │
        └────────┬──────┘ └──────┬────────┘    │
                 │               │             │
                 └───────┬───────┘             │
                         │                     │
                 ┌───────┴───────┐             │
                 │  AWS RDS      │◄────────────┘
                 │  PostgreSQL 16│
                 └───────────────┘
```

### Infrastructure (Terraform)

```
terraform/
├── providers.tf      # AWS, Helm, K8s providers
├── vpc.tf             # VPC, subnets, NAT, routing
├── eks.tf             # EKS cluster + managed node group
├── rds.tf             # PostgreSQL on RDS (db.t4g.micro)
├── ecr.tf             # 3 container repositories
├── iam.tf             # OIDC + IRSA for ALB controller
├── secrets.tf         # Secrets Manager + random DB password
└── outputs.tf         # ECR URLs, RDS endpoint, kubectl config
```

---

## Quick Start (Local Dev)

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker

### 1. Start PostgreSQL

```bash
docker run -d --name pokemission-db \
  -e POSTGRES_USER=pokemissionadmin \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=pokemissiondb \
  -p 5432:5432 \
  postgres:16-alpine
```

### 2. Start the Mission Service

```bash
cd mission-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### 3. Start the Subscriber Service

```bash
cd subscriber-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:3000** — the Vite dev server proxies `/api/*` to port 8000.

---

## Local Kubernetes (Minikube / Kind)

```bash
# Start cluster
minikube start --cpus=4 --memory=4g
# or: kind create cluster --name pokemission

# Enable ingress
minikube addons enable ingress

# Build, load, deploy
make all

# Wait for pods
make wait
```

| Command | Description |
|---|---|
| `make build` | Build all 3 Docker images |
| `make load` | Load images into cluster |
| `make deploy` | Apply all Kubernetes manifests |
| `make all` | build + load + deploy |
| `make clean` | Delete namespace and images |
| `make status` | Show all resources |

---

## Deploy to AWS (EKS)

### Prerequisites

- AWS CLI configured with admin credentials
- Terraform 1.5+
- Docker

### One-Command Deploy

```bash
./deploy.sh
```

This script:
1. Applies Terraform (VPC, EKS cluster, RDS, ECR, IAM)
2. Configures `kubectl`
3. Builds & pushes images to ECR
4. Creates K8s namespace and DB secret
5. Applies all K8s manifests
6. Waits for pods and ALB provisioning
7. Runs health checks and prints the URL

### Manual Deploy

```bash
# 1. Provision infrastructure
cd terraform
terraform init
terraform apply -auto-approve

# 2. Configure kubectl
aws eks update-kubeconfig --name pokemission --region ap-south-1

# 3. Build & push images
./deploy.sh deploy   # or follow the manual steps in the script

# 4. Apply manifests
kubectl apply -f k8s/
```

### Cleanup

```bash
./deploy.sh cleanup
```

This deletes the K8s namespace (drains pods) then runs `terraform destroy`.

---

## API Reference

All endpoints are accessible through the ALB at `/api/mission/*` and `/api/subscriber/*`.

### Mission Service

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/mission/health` | Health check |
| `GET` | `/api/mission/generations` | All Pokémon generations |
| `GET` | `/api/mission/generations/latest` | Latest generation |
| `GET` | `/api/mission/generations/{gen_id}/pokemon` | Pokémon in a generation |
| `GET` | `/api/mission/pokemon` | All Pokémon |
| `GET` | `/api/mission/pokemon/{id}` | Single Pokémon |
| `GET` | `/api/mission/types` | All unique Pokémon types |

### Subscriber Service

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/subscriber/health` | Health check |
| `POST` | `/api/subscriber/subscribe` | Create/update subscription |
| `GET` | `/api/subscriber/{id}/alerts` | Get alerts for a subscriber |
| `PUT` | `/api/subscriber/{id}/alerts/{alert_id}/read` | Mark alert read |
| `DELETE` | `/api/subscriber/{id}` | Unsubscribe |

---

## Database Schema

PostgreSQL 16 with 4 tables — automatically created by SQLAlchemy on startup.

### `generations`
| Column | Type | Description |
|---|---|---|
| `id` | `VARCHAR PK` | e.g. `gen-1` |
| `name` | `VARCHAR` | e.g. "Generation I" |
| `gen_number` | `INTEGER` | 1–9 |
| `date_utc` | `TIMESTAMPTZ` | Approximate release date |
| `region_name` | `VARCHAR` | e.g. "Kanto" |
| `games` | `VARCHAR` | Comma-separated game titles |
| `pokemon_species` | `JSONB` | Array of species names |

### `pokemon`
| Column | Type | Description |
|---|---|---|
| `id` | `VARCHAR PK` | e.g. `pk-25` |
| `name` | `VARCHAR` | e.g. "Pikachu" |
| `type` | `VARCHAR` | e.g. "electric" |
| `sprite_url` | `VARCHAR` | Official artwork URL |
| `base_experience` | `INTEGER` | Base EXP yield |

### `subscribers` & `alerts`
Users subscribe to event types; the subscriber service polls for new generations every 2 minutes and creates alerts.

---

## Tech Stack

| Category | Technology |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts, Axios |
| **Backend** | FastAPI, SQLAlchemy (async), asyncpg, httpx |
| **Database** | PostgreSQL 16 (RDS) |
| **Infrastructure** | Terraform, AWS EKS, ECR, RDS, Secrets Manager |
| **K8s** | EKS 1.30, AWS Load Balancer Controller, IRSA |
| **CI/CD** | Manual (Jenkins-ready via `deploy.sh`) |
| **External API** | [PokéAPI](https://pokeapi.co) (with built-in fallback data) |

---

## Testing

```bash
# Frontend
cd frontend && npm test

# Mission service
cd mission-service && pip install -r requirements-test.txt && pytest

# Subscriber service
cd subscriber-service && pip install -r requirements-test.txt && pytest
```

---

## Project Structure

```
pokemission/
├── frontend/              # React SPA
│   ├── src/               # Components, API client
│   └── Dockerfile         # Multi-stage nginx build
├── mission-service/       # FastAPI Pokémon data API
│   ├── app/               # Routes, models, sync client
│   ├── tests/             # pytest tests
│   └── Dockerfile
├── subscriber-service/    # FastAPI subscription manager
│   ├── app/               # Routes, models, alert poller
│   ├── tests/             # pytest tests
│   └── Dockerfile
├── k8s/                   # Kubernetes manifests (EKS-ready)
│   ├── namespace.yaml
│   ├── mission-service.yaml
│   ├── subscriber-service.yaml
│   ├── frontend.yaml
│   └── ingress.yaml
├── terraform/             # AWS infrastructure as code
│   ├── vpc.tf, eks.tf, rds.tf, ...
│   └── outputs.tf
├── deploy.sh              # One-click deploy to AWS
├── Makefile               # Local K8s commands
└── README.md
```

---

## License

[MIT](LICENSE)
