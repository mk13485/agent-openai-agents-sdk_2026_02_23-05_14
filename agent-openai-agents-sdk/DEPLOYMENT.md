# Deployment & Infrastructure Blueprint
**Copilot-Style Coding Agent - Production Deployment Guide**
**Date: February 23, 2026**

---

## Table of Contents

1. [Deployment Strategy](#1-deployment-strategy)
2. [Infrastructure as Code (IaC)](#2-infrastructure-as-code-iac)
3. [EU Cloud Deployment](#3-eu-cloud-deployment)
4. [Kubernetes Configuration](#4-kubernetes-configuration)
5. [CI/CD Pipeline](#5-cicd-pipeline)
6. [Scaling & Auto-Scaling](#6-scaling--auto-scaling)
7. [Disaster Recovery](#7-disaster-recovery)
8. [Cost Optimization](#8-cost-optimization)
9. [Operations Runbooks](#9-operations-runbooks)
10. [Production Checklist](#10-production-checklist)

---

## 1. Deployment Strategy

### 1.1 Phased Rollout

#### Phase 1: Proof of Concept (Weeks 1-4)
**Goal**: Validate technical feasibility and basic functionality

**Infrastructure**:
- Single EU region (AWS eu-central-1 or Azure West Europe)
- Minimal resources: 1 GPU node, 2 CPU nodes, managed databases
- No high availability (acceptable for PoC)

**Features**:
- Inline completions (fast model only)
- VS Code plugin
- Basic telemetry

**Users**: 2-3 engineers (alpha testers)

**Success Criteria**:
- Completions work end-to-end
- Latency <1s for P95
- No major security issues

#### Phase 2: Pilot (Months 2-3)
**Goal**: Test with real users, collect feedback, validate product-market fit

**Infrastructure**:
- Single EU region with high availability (multi-AZ)
- Autoscaling for app server and model serving
- Managed databases with replication
- Monitoring and alerting in place

**Features**:
- Fast model + agent model
- VS Code + JetBrains plugins
- Chat pane, multi-file refactors
- Privacy controls

**Users**: 10-20 engineers across 2-3 teams

**Success Criteria**:
- Acceptance rate >50%
- Test pass rate >70%
- Uptime >99%
- Positive user feedback

#### Phase 3: Production (Months 4-6)
**Goal**: Scale to entire engineering org

**Infrastructure**:
- Multi-region for disaster recovery (primary + backup)
- Full autoscaling, GPU pools, sandbox clusters
- Comprehensive monitoring, SLOs, alerting
- Security hardening, compliance audits

**Features**:
- All IDE plugins (VS Code, JetBrains, Neovim, Web)
- Full agentic capabilities
- RLHF training loop
- Enterprise features (SSO, team dashboards)

**Users**: 100-200+ engineers

**Success Criteria**:
- SLA 99.5% uptime
- Acceptance rate >60%
- Cost per user <€50/month
- GDPR compliance verified

### 1.2 Deployment Environments

| Environment | Purpose                     | Infrastructure                | Uptime Target |
|-------------|-----------------------------|-------------------------------|---------------|
| Development | Engineer testing            | Local Docker Compose          | N/A           |
| Staging     | Pre-production validation   | Single region, minimal scale  | 95%           |
| Production  | Live users                  | Multi-AZ, autoscaling         | 99.5%         |

**Environment Parity**: Keep staging as close to production as possible (same tools, configs, versions)

---

## 2. Infrastructure as Code (IaC)

### 2.1 Tool Choice

**Recommended**: **Terraform** + **Helm** (Kubernetes)

**Why**:
- Terraform: Multi-cloud, declarative, state management, strong community
- Helm: Kubernetes package manager, reusable charts, templating

**Alternative**: Pulumi (if team prefers TypeScript/Python over HCL)

### 2.2 Repository Structure

```
infra/
├── terraform/
│   ├── modules/
│   │   ├── vpc/                  # Network setup
│   │   ├── kubernetes/           # EKS/AKS cluster
│   │   ├── rds/                  # PostgreSQL database
│   │   ├── redis/                # Redis cluster
│   │   ├── s3/                   # Object storage
│   │   └── monitoring/           # Prometheus, Grafana
│   ├── environments/
│   │   ├── dev/
│   │   │   └── main.tf
│   │   ├── staging/
│   │   │   └── main.tf
│   │   └── production/
│   │       └── main.tf
│   └── backend.tf                # Terraform state backend (S3 + DynamoDB)
├── helm/
│   ├── charts/
│   │   ├── app-server/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   └── templates/
│   │   ├── model-serving/
│   │   └── sandbox-manager/
│   └── values/
│       ├── dev.yaml
│       ├── staging.yaml
│       └── production.yaml
└── scripts/
    ├── deploy.sh                 # Deployment automation
    ├── rollback.sh               # Emergency rollback
    └── db-migrate.sh             # Database migrations
```

### 2.3 Terraform Example (AWS)

**VPC Module** (`modules/vpc/main.tf`):
```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-copilot-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  count                   = 3
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.environment}-public-subnet-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + 3)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.environment}-private-subnet-${count.index + 1}"
  }
}
```

**EKS Cluster** (`modules/kubernetes/main.tf`):
```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${var.environment}-copilot-cluster"
  cluster_version = "1.28"

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  enable_irsa = true  # IAM Roles for Service Accounts

  # GPU node group for model serving
  eks_managed_node_groups = {
    gpu_nodes = {
      instance_types = ["g5.2xlarge"]  # 1x NVIDIA A10G GPU
      capacity_type  = "SPOT"          # Cost savings (or ON_DEMAND for prod)
      min_size       = 1
      max_size       = 4
      desired_size   = 2

      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NoSchedule"
      }]

      labels = {
        workload = "model-serving"
      }
    }

    # CPU node group for app server
    cpu_nodes = {
      instance_types = ["m5.xlarge"]
      capacity_type  = "ON_DEMAND"
      min_size       = 2
      max_size       = 10
      desired_size   = 3

      labels = {
        workload = "general"
      }
    }
  }

  # NVIDIA GPU driver
  cluster_addons = {
    kube-proxy = {}
    vpc-cni    = {}
    coredns    = {}
    aws-ebs-csi-driver = {}
  }

  tags = {
    Environment = var.environment
  }
}

# Install NVIDIA device plugin for Kubernetes
resource "helm_release" "nvidia_device_plugin" {
  name       = "nvidia-device-plugin"
  repository = "https://nvidia.github.io/k8s-device-plugin"
  chart      = "nvidia-device-plugin"
  namespace  = "kube-system"

  depends_on = [module.eks]
}
```

**RDS PostgreSQL** (`modules/rds/main.tf`):
```hcl
resource "aws_db_instance" "postgres" {
  identifier     = "${var.environment}-copilot-db"
  engine         = "postgres"
  engine_version = "15.5"

  instance_class    = var.instance_class  # db.t3.medium (dev), db.r5.xlarge (prod)
  allocated_storage = var.allocated_storage  # 20 GB (dev), 100 GB (prod)
  storage_type      = "gp3"
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn

  db_name  = "copilot"
  username = var.db_username
  password = var.db_password  # Use AWS Secrets Manager in production

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  multi_az               = var.environment == "production" ? true : false
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "03:00-04:00"  # UTC
  maintenance_window     = "sun:04:00-sun:05:00"

  deletion_protection = var.environment == "production" ? true : false
  skip_final_snapshot = var.environment != "production"

  tags = {
    Environment = var.environment
  }
}
```

### 2.4 Helm Chart Example (App Server)

**Chart.yaml**:
```yaml
apiVersion: v2
name: app-server
description: Copilot App Server
type: application
version: 1.0.0
appVersion: "1.0.0"
```

**values.yaml** (default values):
```yaml
replicaCount: 2

image:
  repository: registry.eu.example.com/app-server
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  port: 8080
  metricsPort: 8081

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.copilot.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: api-tls
      hosts:
        - api.copilot.example.com

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

env:
  - name: LOG_LEVEL
    value: "info"
  - name: POSTGRES_HOST
    value: "postgres-service.default.svc.cluster.local"
  - name: POSTGRES_PORT
    value: "5432"
  - name: POSTGRES_DB
    value: "copilot"
  - name: REDIS_HOST
    value: "redis-service.default.svc.cluster.local"
  - name: MODEL_SERVING_ENDPOINT
    value: "http://model-serving:8000"

envFrom:
  - secretRef:
      name: app-server-secrets  # Contains POSTGRES_PASSWORD, etc.

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

serviceMonitor:
  enabled: true
  interval: 30s
  path: /metrics
```

**templates/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "app-server.fullname" . }}
  labels:
    {{- include "app-server.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "app-server.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "app-server.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.service.port }}
          protocol: TCP
        - name: metrics
          containerPort: {{ .Values.service.metricsPort }}
          protocol: TCP
        env:
        {{- toYaml .Values.env | nindent 8 }}
        envFrom:
        {{- toYaml .Values.envFrom | nindent 8 }}
        livenessProbe:
          {{- toYaml .Values.livenessProbe | nindent 10 }}
        readinessProbe:
          {{- toYaml .Values.readinessProbe | nindent 10 }}
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
```

---

## 3. EU Cloud Deployment

### 3.1 AWS (Recommended for Quick Start)

#### Regions
- **Primary**: `eu-central-1` (Frankfurt, Germany)
- **Backup**: `eu-west-1` (Ireland)

#### Core Services
- **Compute**: EKS (Kubernetes), EC2 (GPU instances: g5.xlarge, p4d.24xlarge)
- **Database**: RDS PostgreSQL, ElastiCache Redis
- **Storage**: S3 (with EU bucket policy), EFS (for persistent volumes)
- **Networking**: VPC, Application Load Balancer, Transit Gateway
- **Monitoring**: CloudWatch, X-Ray
- **Security**: KMS (encryption keys), Secrets Manager, IAM

#### Data Residency Enforcement
```hcl
# S3 bucket policy: block access from non-EU regions
resource "aws_s3_bucket_policy" "eu_only" {
  bucket = aws_s3_bucket.training_data.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyNonEURequests"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          "${aws_s3_bucket.training_data.arn}",
          "${aws_s3_bucket.training_data.arn}/*"
        ]
        Condition = {
          StringNotEquals = {
            "aws:RequestedRegion" = ["eu-central-1", "eu-west-1"]
          }
        }
      }
    ]
  })
}
```

### 3.2 Azure (Alternative)

#### Regions
- **Primary**: `West Europe` (Netherlands)
- **Backup**: `North Europe` (Ireland)

#### Core Services
- **Compute**: AKS (Kubernetes), VM Scale Sets (GPU: NC-series, ND-series)
- **Database**: Azure Database for PostgreSQL, Azure Cache for Redis
- **Storage**: Blob Storage, Azure Files
- **Networking**: Virtual Network, Application Gateway, Load Balancer
- **Monitoring**: Azure Monitor, Application Insights
- **Security**: Key Vault, Managed Identities

#### Data Residency Enforcement
```hcl
resource "azurerm_storage_account" "training_data" {
  name                     = "copilottrainingdata"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = "West Europe"
  account_tier             = "Standard"
  account_replication_type = "GRS"  # Geo-redundant within EU

  # Enforce EU-only access
  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
    virtual_network_subnet_ids = [azurerm_subnet.private.id]
  }

  tags = {
    DataResidency = "EU"
  }
}
```

### 3.3 GCP (Alternative)

#### Regions
- **Primary**: `europe-west4` (Netherlands)
- **Backup**: `europe-west1` (Belgium)

#### Core Services
- **Compute**: GKE (Kubernetes), Compute Engine (GPU: A100, T4)
- **Database**: Cloud SQL (PostgreSQL), Memorystore (Redis)
- **Storage**: Cloud Storage (with location constraint)
- **Networking**: VPC, Cloud Load Balancing
- **Monitoring**: Cloud Monitoring, Cloud Trace
- **Security**: Cloud KMS, Secret Manager

#### Data Residency Enforcement
```hcl
resource "google_storage_bucket" "training_data" {
  name          = "copilot-training-data"
  location      = "EU"  # Multi-region within EU
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90  # Delete training data after 90 days
    }
  }
}
```

---

## 4. Kubernetes Configuration

### 4.1 Namespace Organization

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: copilot-prod
  labels:
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: copilot-staging
  labels:
    environment: staging
---
apiVersion: v1
kind: Namespace
metadata:
  name: copilot-monitoring
  labels:
    purpose: observability
```

### 4.2 Resource Quotas

**Production Namespace**:
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
  namespace: copilot-prod
spec:
  hard:
    requests.cpu: "100"       # Max 100 CPU cores requested
    requests.memory: 500Gi    # Max 500 GB RAM requested
    requests.nvidia.com/gpu: "10"  # Max 10 GPUs
    limits.cpu: "150"
    limits.memory: 750Gi
    limits.nvidia.com/gpu: "10"
    pods: "200"               # Max 200 pods
```

### 4.3 Network Policies

**Isolate Sandboxes** (sandboxes can't talk to each other or external internet):
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sandbox-isolation
  namespace: copilot-prod
spec:
  podSelector:
    matchLabels:
      component: sandbox
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          component: sandbox-manager  # Only sandbox-manager can talk to sandboxes
  egress:
  - to:
    - podSelector:
        matchLabels:
          component: sandbox-manager
  # No external egress allowed
```

**Allow App Server to Model Serving**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-server-to-model
  namespace: copilot-prod
spec:
  podSelector:
    matchLabels:
      component: app-server
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          component: model-serving
    ports:
    - protocol: TCP
      port: 8000
  - to:  # Also allow DNS
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

### 4.4 Pod Security Standards

**Enforce Restricted Standard**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: copilot-prod
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Restricted means**:
- No privileged containers
- No host namespaces (network, PID, IPC)
- Run as non-root user
- Drop all capabilities
- No hostPath volumes

### 4.5 Persistent Volumes

**Model Cache** (shared across model serving pods):
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-cache
  namespace: copilot-prod
spec:
  accessModes:
    - ReadWriteMany  # Shared volume
  storageClassName: efs  # AWS EFS or Azure Files
  resources:
    requests:
      storage: 100Gi
```

---

## 5. CI/CD Pipeline

### 5.1 Pipeline Stages

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Code      │    │   Build &   │    │   Test &    │    │   Deploy    │
│   Commit    │───▶│   Lint      │───▶│   Security  │───▶│   (staging) │
│             │    │             │    │   Scan      │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │  Manual Approval│
                                                         │  (for prod)     │
                                                         └────────┬────────┘
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │   Deploy        │
                                                         │   (production)  │
                                                         └─────────────────┘
```

### 5.2 GitHub Actions Workflow

**.github/workflows/deploy.yaml**:
```yaml
name: Build and Deploy

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

env:
  AWS_REGION: eu-central-1
  ECR_REGISTRY: 123456789012.dkr.ecr.eu-central-1.amazonaws.com

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: golangci-lint
        uses: golangci/golangci-lint-action@v3
        with:
          version: latest

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Run tests
        run: go test -v -race -coverprofile=coverage.out ./...

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.out

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail if vulnerabilities found

      - name: Run govulncheck
        run: |
          go install golang.org/x/vuln/cmd/govulncheck@latest
          govulncheck ./...

  build:
    needs: [lint, test, security-scan]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/app-server:$IMAGE_TAG .
          docker push $ECR_REGISTRY/app-server:$IMAGE_TAG
          docker tag $ECR_REGISTRY/app-server:$IMAGE_TAG $ECR_REGISTRY/app-server:latest
          docker push $ECR_REGISTRY/app-server:latest

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name staging-copilot-cluster --region $AWS_REGION

      - name: Deploy to staging
        run: |
          helm upgrade --install app-server ./helm/charts/app-server \
            --namespace copilot-staging \
            --values ./helm/values/staging.yaml \
            --set image.tag=${{ github.sha }} \
            --wait

  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://api.copilot.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name production-copilot-cluster --region $AWS_REGION

      - name: Deploy to production (canary)
        run: |
          # Deploy canary (10% traffic)
          helm upgrade --install app-server-canary ./helm/charts/app-server \
            --namespace copilot-prod \
            --values ./helm/values/production.yaml \
            --set image.tag=${{ github.sha }} \
            --set replicaCount=1 \
            --set service.name=app-server-canary \
            --wait

          # Wait for canary health checks
          sleep 60

          # Check canary metrics (error rate, latency)
          # If canary healthy, proceed with full rollout
          helm upgrade --install app-server ./helm/charts/app-server \
            --namespace copilot-prod \
            --values ./helm/values/production.yaml \
            --set image.tag=${{ github.sha }} \
            --wait
```

### 5.3 Rollback Strategy

**Automatic Rollback** (if deployment fails health checks):
```yaml
# In Helm chart
spec:
  progressDeadlineSeconds: 600  # 10 minutes
  revisionHistoryLimit: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero-downtime deployment
```

**Manual Rollback**:
```bash
# List revisions
helm history app-server -n copilot-prod

# Rollback to previous version
helm rollback app-server -n copilot-prod

# Rollback to specific revision
helm rollback app-server 5 -n copilot-prod
```

---

## 6. Scaling & Auto-Scaling

### 6.1 Horizontal Pod Autoscaler (HPA)

**App Server**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-server-hpa
  namespace: copilot-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app-server
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"  # Scale if >1000 req/s per pod
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60  # Scale down max 50% per minute
    scaleUp:
      stabilizationWindowSeconds: 0  # Scale up immediately
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30  # Scale up max 100% per 30 seconds
```

**Model Serving** (GPU nodes):
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: model-serving-hpa
  namespace: copilot-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: model-serving
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Pods
    pods:
      metric:
        name: inference_queue_depth
      target:
        type: AverageValue
        averageValue: "10"  # Scale if queue >10 requests per pod
  - type: Resource
    resource:
      name: nvidia.com/gpu
      target:
        type: Utilization
        averageUtilization: 80
```

### 6.2 Cluster Autoscaler

**AWS EKS** (auto-add nodes):
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/ClusterAutoscalerRole
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      serviceAccountName: cluster-autoscaler
      containers:
      - image: registry.k8s.io/autoscaling/cluster-autoscaler:v1.28.0
        name: cluster-autoscaler
        command:
          - ./cluster-autoscaler
          - --cloud-provider=aws
          - --namespace=kube-system
          - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/production-copilot-cluster
          - --balance-similar-node-groups
          - --skip-nodes-with-system-pods=false
          - --scale-down-unneeded-time=10m
          - --scale-down-delay-after-add=10m
```

### 6.3 Vertical Pod Autoscaler (VPA)

**Recommender** (suggests resource limits):
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: app-server-vpa
  namespace: copilot-prod
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app-server
  updatePolicy:
    updateMode: "Auto"  # Automatically apply recommendations
  resourcePolicy:
    containerPolicies:
    - containerName: '*'
      minAllowed:
        cpu: 100m
        memory: 256Mi
      maxAllowed:
        cpu: 4000m
        memory: 8Gi
```

---

## 7. Disaster Recovery

### 7.1 Backup Strategy

**Database Backups** (RDS):
- **Frequency**: Automated daily snapshots
- **Retention**: 30 days
- **Cross-Region**: Weekly backups to secondary EU region

**Application Data** (S3):
- **Versioning**: Enabled for training data, model artifacts
- **Cross-Region Replication**: Async replication to backup region
- **Lifecycle Policies**: Move old backups to Glacier after 90 days

**Kubernetes Resources**:
- **Tool**: Velero (backup K8s manifests, persistent volumes)
- **Frequency**: Daily
- **Storage**: S3 bucket in backup region

**Velero Setup**:
```bash
# Install Velero
helm install velero vmware-tanzu/velero \
  --namespace velero \
  --set-file credentials.secretContents.cloud=./aws-credentials \
  --set configuration.provider=aws \
  --set configuration.backupStorageLocation.bucket=copilot-velero-backups \
  --set configuration.backupStorageLocation.config.region=eu-west-1

# Create daily backup schedule
velero schedule create daily-backup \
  --schedule="0 2 * * *" \
  --include-namespaces copilot-prod \
  --ttl 720h0m0s  # 30 days retention
```

### 7.2 Recovery Procedures

#### Database Recovery
```bash
# Restore from snapshot (AWS RDS)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier copilot-db-restored \
  --db-snapshot-identifier copilot-db-snapshot-2026-02-23 \
  --db-subnet-group-name copilot-db-subnet-group \
  --vpc-security-group-ids sg-0123456789abcdef0

# Update app server to point to restored DB
kubectl set env deployment/app-server \
  POSTGRES_HOST=copilot-db-restored.c9xyz.eu-central-1.rds.amazonaws.com \
  -n copilot-prod
```

#### Kubernetes Cluster Recovery
```bash
# Restore entire namespace from Velero backup
velero restore create --from-backup daily-backup-20260223020000

# Or restore specific resources
velero restore create --from-backup daily-backup-20260223020000 \
  --include-resources deployments,services
```

### 7.3 Disaster Recovery Testing

**Monthly DR Drill**:
1. **Simulate Disaster**: Shut down primary region
2. **Failover**: Route traffic to backup region
3. **Verify**: Test all functionality (completions, chat, refactors)
4. **Measure**: Record RTO (Recovery Time Objective) and RPO (Recovery Point Objective)
5. **Document**: Update runbooks based on learnings

**Target Metrics**:
- **RTO**: <1 hour (time to restore service)
- **RPO**: <15 minutes (maximum data loss)

---

## 8. Cost Optimization

### 8.1 Cost Breakdown (Production, Monthly)

| Component                 | Estimated Cost (EUR) | Optimization Strategy              |
|---------------------------|----------------------|------------------------------------|
| GPU Compute (4x A100)     | €24,000              | Use spot instances, autoscaling    |
| CPU Compute (10x m5.2xl)  | €3,000               | Reserved instances (1-year)        |
| Database (RDS)            | €1,500               | Right-size after monitoring        |
| Redis (ElastiCache)       | €500                 | Use smaller node types             |
| Storage (S3, EFS)         | €800                 | Lifecycle policies, compression    |
| Data Transfer (egress)    | €1,000               | Use CloudFront CDN for static      |
| Monitoring/Logging        | €500                 | Reduce retention, sampling         |
| **Total**                 | **€31,300**          |                                    |

### 8.2 Optimization Techniques

#### GPU Spot Instances
**Savings**: 60-70% compared to on-demand

```hcl
# Terraform: Use spot instances for model serving
eks_managed_node_groups = {
  gpu_nodes = {
    instance_types = ["g5.2xlarge", "g5.4xlarge"]
    capacity_type  = "SPOT"  # Spot instances
    ...
  }
}
```

**Risk Mitigation**:
- Use multiple instance types (diversification)
- Set up spot interruption handling (graceful shutdown)
- Maintain 1-2 on-demand instances for critical workloads

#### Reserved Instances
**Savings**: 40-50% for predictable workloads (app servers, databases)

```bash
# Purchase 1-year reserved instances for 10x m5.2xlarge
aws ec2 purchase-reserved-instances-offering \
  --instance-type m5.2xlarge \
  --instance-count 10 \
  --offering-id <offering-id>
```

#### S3 Lifecycle Policies
**Savings**: Move old data to cheaper storage tiers

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "training_data" {
  bucket = aws_s3_bucket.training_data.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"  # Infrequent Access (cheaper)
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"  # Instant Retrieval Glacier
    }

    expiration {
      days = 180  # Delete after 6 months
    }
  }
}
```

#### Right-Sizing
**Tool**: AWS Compute Optimizer, Kubernetes VPA

```bash
# Get recommendations
aws compute-optimizer get-ec2-instance-recommendations
```

**Example**: If app server CPU usage consistently <30%, downsize from m5.2xlarge to m5.xlarge (50% cost savings)

### 8.3 Cost Monitoring

**Alerts**:
```yaml
# Prometheus alert: Notify if monthly cost projection exceeds budget
- alert: CostOverrun
  expr: sum(aws_billing_estimated_charges{currency="USD"}) > 35000
  for: 1h
  annotations:
    summary: "AWS costs exceeding budget"
    description: "Projected monthly cost: {{ $value }} EUR"
```

**Dashboard Metrics**:
- Cost per user (monthly spend / active users)
- Cost per completion request
- GPU utilization (if <50%, consider downsizing)
- Spot interruption rate

---

## 9. Operations Runbooks

### 9.1 Deployment Runbook

**Pre-Deployment Checklist**:
- [ ] All tests passing (unit, integration, E2E)
- [ ] Security scans passed (Trivy, govulncheck)
- [ ] Helm chart validated (`helm lint`)
- [ ] Database migrations tested (if any)
- [ ] Rollback plan ready
- [ ] On-call engineer available

**Deployment Steps**:
```bash
# 1. Deploy to staging
helm upgrade --install app-server ./helm/charts/app-server \
  --namespace copilot-staging \
  --values ./helm/values/staging.yaml \
  --set image.tag=<version>

# 2. Run smoke tests in staging
./scripts/smoke-test.sh staging

# 3. If staging OK, deploy to production (canary)
helm upgrade --install app-server-canary ./helm/charts/app-server \
  --namespace copilot-prod \
  --values ./helm/values/production.yaml \
  --set image.tag=<version> \
  --set replicaCount=1

# 4. Monitor canary for 10 minutes
watch kubectl get pods -n copilot-prod -l version=canary
# Check Grafana dashboard for error rate, latency

# 5. If canary healthy, full rollout
helm upgrade --install app-server ./helm/charts/app-server \
  --namespace copilot-prod \
  --values ./helm/values/production.yaml \
  --set image.tag=<version>

# 6. Verify deployment
kubectl rollout status deployment/app-server -n copilot-prod
./scripts/smoke-test.sh production
```

### 9.2 Incident Response Runbook

See **[SECURITY.md, Section 9: Incident Response](./SECURITY.md#9-incident-response)** for full incident response plan.

**Quick Reference**:
1. **Detect**: Alert → On-call notified
2. **Assess**: Severity (P0-P4), impact
3. **Contain**: Isolate affected systems
4. **Communicate**: Post status to #incidents, email users if needed
5. **Investigate**: Root cause analysis
6. **Resolve**: Deploy fix, verify resolution
7. **Post-Mortem**: Document, share learnings

### 9.3 Scaling Runbook

**Manual Scale-Up** (if autoscaler not fast enough):
```bash
# Scale app server
kubectl scale deployment/app-server --replicas=20 -n copilot-prod

# Scale GPU nodes (AWS)
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name copilot-gpu-nodes \
  --desired-capacity 8
```

**Manual Scale-Down** (after traffic spike):
```bash
# Check current utilization
kubectl top pods -n copilot-prod

# Scale down if utilization <30%
kubectl scale deployment/app-server --replicas=5 -n copilot-prod
```

---

## 10. Production Checklist

### 10.1 Infrastructure

- [ ] Multi-AZ deployment in primary EU region
- [ ] Backup region configured for disaster recovery
- [ ] Kubernetes cluster with GPU support
- [ ] Managed databases (PostgreSQL, Redis) with replication
- [ ] Object storage (S3/Blob) with cross-region replication
- [ ] VPC networking with private subnets for data layer
- [ ] TLS certificates (Let's Encrypt or ACM)
- [ ] DNS configured (api.copilot.example.com)
- [ ] Load balancers with health checks

### 10.2 Security

- [ ] Secrets stored in vault (AWS Secrets Manager, Key Vault)
- [ ] IAM roles with least privilege
- [ ] Network policies (pod-to-pod isolation)
- [ ] Pod security standards enforced (restricted)
- [ ] Secret rotation automated (90-day cycle)
- [ ] Vulnerability scanning in CI/CD
- [ ] WAF rules configured (rate limiting, DDoS protection)
- [ ] Audit logging enabled (3-year retention)

### 10.3 Monitoring & Alerting

- [ ] Prometheus deployed and scraping metrics
- [ ] Grafana dashboards created (system, model, user)
- [ ] ELK/Loki deployed for log aggregation
- [ ] Jaeger deployed for distributed tracing
- [ ] Alertmanager configured with runbooks
- [ ] PagerDuty/Opsgenie integration
- [ ] Slack notifications for warnings
- [ ] Weekly cost reports automated

### 10.4 CI/CD

- [ ] GitHub Actions workflows configured
- [ ] Automated tests (unit, integration, E2E)
- [ ] Security scans in pipeline
- [ ] Canary deployments to production
- [ ] Rollback tested and documented
- [ ] Database migration strategy (Flyway, Liquibase)

### 10.5 Documentation

- [ ] Architecture diagrams updated
- [ ] Deployment runbooks written
- [ ] Incident response procedures documented
- [ ] Disaster recovery plan tested
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User privacy policy published
- [ ] GDPR compliance documentation

### 10.6 Legal & Compliance

- [ ] Data Processing Agreement (DPA) signed with customers
- [ ] EU data residency verified
- [ ] GDPR user rights implemented (access, deletion, export)
- [ ] Privacy Impact Assessment (PIA) completed
- [ ] Terms of Service and Privacy Policy published
- [ ] License detection and attribution implemented

---

## Summary

This deployment blueprint provides:

1. **Phased Rollout**: PoC → Pilot → Production over 6 months
2. **Infrastructure as Code**: Terraform modules for AWS/Azure/GCP, Helm charts for Kubernetes
3. **EU Cloud Deployment**: Data residency enforcement, GDPR-compliant regions
4. **Kubernetes Configuration**: Namespaces, resource quotas, network policies, pod security
5. **CI/CD Pipeline**: GitHub Actions with linting, testing, security scanning, canary deploys
6. **Scaling**: HPA for pods, Cluster Autoscaler for nodes, VPA for resource optimization
7. **Disaster Recovery**: Automated backups, cross-region replication, tested failover (RTO <1h)
8. **Cost Optimization**: Spot instances, reserved instances, lifecycle policies (€31k/month for 100-200 users)
9. **Operations Runbooks**: Deployment, incident response, scaling procedures
10. **Production Checklist**: 60+ items across infrastructure, security, monitoring, compliance

**Next Steps**:
1. Choose cloud provider (AWS recommended for quick start)
2. Set up Terraform backend (S3 + DynamoDB for state)
3. Provision infrastructure in dev environment
4. Deploy PoC with minimal resources
5. Test end-to-end (IDE → App Server → Model)
6. Iterate and scale to pilot phase

**Dependencies**: Review [ARCHITECTURE.md](./ARCHITECTURE.md) for high-level design, [COMPONENTS.md](./COMPONENTS.md) for detailed specs, [SECURITY.md](./SECURITY.md) for compliance.

---

**Document Version**: 1.0
**Last Updated**: February 23, 2026
**Owner**: Slovakia Engineering Team / DevOps & SRE
**Review Cycle**: Quarterly or before major infrastructure changes
