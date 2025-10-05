# Infrastructure Overview

This document describes the deployment setup for our monorepo (Next.js frontend + Fastify backend + Postgres + Redis).

---

## High-Level Architecture

            ┌─────────────────────────┐
            │        Vercel           │
            │   Next.js Frontend      │
            │  (prod & preview envs)  │
            └───────────┬─────────────┘
                        │ HTTPS
                        ▼
               Public API Endpoint
            (ECS Fargate Service or App Runner)
                        │
                 ┌──────┴──────┐
                 │  Fastify API │  (container from monorepo)
                 └──────┬──────┘
                        │ VPC (private subnets)
          ┌─────────────┴─────────────┐
          │                           │
  ┌───────▼────────┐           ┌──────▼──────────┐
  │   Amazon RDS   │           │  Redis (backend │
  │  Postgres (TF) │           │  caching only)  │
  └────────────────┘           └─────────────────┘


---

## Components

### 1. **Frontend**
- Framework: Next.js
- Hosting: [Vercel](https://vercel.com)
- Environments: Production + Preview
- Config:
  - API base URL → points to backend service
  - Secrets (API keys, etc.) managed in Vercel dashboard

---

### 2. **Backend**
- Language: TypeScript (Fastify framework)
- Deployment: **AWS ECS Fargate** service (alternatively AWS App Runner)
- Networking:
  - Runs in private subnet
  - Accessible via ALB (ECS) or App Runner endpoint
- Container:
  - Built from monorepo `backend/` Dockerfile
  - CI/CD builds and pushes to ECR

---

### 3. **Database**
- Service: **Amazon RDS for Postgres**
- Provisioning: **Terraform**
- Free-tier eligible config:
  - Instance: `db.t3.micro`
  - Storage: 20GB (gp2)
- Security:
  - Runs in private subnet
  - Accessible only by backend security group
- Secrets:
  - DB credentials stored in **AWS Secrets Manager**

---

### 4. **Redis**
Redis is used for **backend caching** (session storage, API response caching). Three deployment strategies:

1. **Sidecar in ECS Task**  
   - Redis runs in same Fargate task as backend API (localhost access).  
   - Suitable for small-scale caches, no persistence required.  
   - Limitation: each task has its own isolated Redis instance.

2. **External (Recommended for scale)**  
   - **Upstash Redis (serverless)** → easiest, pay-as-you-go.  
   - **Amazon ElastiCache Redis** → managed, production-grade.  
   - **EC2 + Docker Redis** → cheap, but ops overhead.

---

### 5. **Infrastructure as Code**
- Tool: **Terraform**
- Modules:
  - `network/` → VPC, subnets, NAT, SGs
  - `database/` → RDS, Secrets Manager
  - `service/` → ECS (or App Runner), ALB
  - `iam/` → OIDC roles for CI/CD
- Workspaces:
  - `envs/staging/`
  - `envs/prod/`

---

### 6. **CI/CD**
- Tool: GitHub Actions
- Pipelines:
  1. **Infra Pipeline**
     - Runs `terraform plan` + `apply`
     - Provisions RDS, ECS/App Runner, networking, Redis
  2. **Backend Pipeline**
     - Builds backend Docker image
     - Pushes to ECR
     - Triggers ECS/App Runner deployment
  3. **Frontend Pipeline**
     - Uses `vercel deploy --prod`
     - Pulls env vars from Vercel

---

## Alternatives

### A. Lean MVP
- Frontend: Vercel
- Backend: AWS App Runner
- Database: RDS (Terraform)
- Redis: Upstash

**Pros:** Simplest to start, no ops.  
**Cons:** App Runner less customizable.

---

### B. AWS-Native Scalable
- Frontend: Vercel
- Backend: ECS Fargate + ALB
- Database: RDS
- Redis: ElastiCache

**Pros:** Production-grade, VPC native.  
**Cons:** More infra pieces, higher cost.

---

### C. Fully Managed (Fastest to iterate)
- Frontend: Vercel
- Backend: Render / Fly.io
- Database: Supabase / Neon
- Redis: Upstash

**Pros:** Zero infra burden.  
**Cons:** Vendor sprawl, migration overhead later.

---

## Deployment Flow (CLI-first)

1. `terraform init && terraform apply` → sets up VPC, RDS, ECS/App Runner
2. GitHub Actions:
   - Build backend → push Docker image → deploy ECS service
   - Deploy frontend → `vercel deploy --prod`
3. Post-deploy:
   - Run database migrations via one-off ECS task
   - Verify health checks (`/health`)

---

## Notes
- **Redis sidecar** is acceptable for MVP/single-task setup, but not scalable for multi-task clusters or persistent workloads.
- For production-grade infra, prefer **Upstash or ElastiCache** for backend caching.
- Secrets should never be hard-coded. Use AWS Secrets Manager + Vercel envs.
- Backend uses Fastify framework with TypeScript for optimal performance.
