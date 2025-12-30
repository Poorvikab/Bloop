# Bloop Platform Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Local Development](#local-development)
4. [Staging Deployment](#staging-deployment)
5. [Production Deployment](#production-deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [Disaster Recovery](#disaster-recovery)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- Docker 20.10+
- Kubernetes 1.24+
- kubectl CLI
- Helm 3.0+
- Terraform 1.0+ (for infrastructure provisioning)
- Git

### Cloud Provider Setup

**AWS:**
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure credentials
aws configure
```

**Azure:**
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login
```

**GCP:**
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize
gcloud init
```

### Kubernetes Cluster Setup

**EKS (AWS):**
```bash
eksctl create cluster \
  --name bloop-prod \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10 \
  --managed

# Add GPU node group for video/avatar services
eksctl create nodegroup \
  --cluster bloop-prod \
  --name gpu-workers \
  --node-type p3.2xlarge \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 5 \
  --node-labels gpu=true
```

**AKS (Azure):**
```bash
az aks create \
  --resource-group bloop-rg \
  --name bloop-prod \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10 \
  --generate-ssh-keys

# Add GPU node pool
az aks nodepool add \
  --resource-group bloop-rg \
  --cluster-name bloop-prod \
  --name gpupool \
  --node-count 2 \
  --node-vm-size Standard_NC6s_v3 \
  --node-taints sku=gpu:NoSchedule \
  --labels gpu=true
```

**GKE (GCP):**
```bash
gcloud container clusters create bloop-prod \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10

# Add GPU node pool
gcloud container node-pools create gpu-pool \
  --cluster bloop-prod \
  --zone us-central1-a \
  --num-nodes 2 \
  --machine-type n1-standard-4 \
  --accelerator type=nvidia-tesla-t4,count=1 \
  --node-labels gpu=true
```

## Infrastructure Setup

### 1. Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.replicaCount=2 \
  --set controller.nodeSelector."kubernetes\.io/os"=linux \
  --set controller.service.type=LoadBalancer
```

### 2. Install cert-manager for SSL

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@bloop.ai
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 3. Create Namespaces

```bash
kubectl create namespace bloop-prod
kubectl create namespace bloop-staging
kubectl create namespace bloop-monitoring
```

### 4. Create Secrets

```bash
# Database credentials
kubectl create secret generic bloop-secrets \
  --from-literal=postgres_user=bloop \
  --from-literal=postgres_password=<STRONG_PASSWORD> \
  --from-literal=database_url=postgresql://bloop:<PASSWORD>@postgres:5432/bloop \
  --from-literal=openai_api_key=<OPENAI_KEY> \
  --from-literal=azure_speech_key=<AZURE_KEY> \
  -n bloop-prod

# Copy to staging
kubectl get secret bloop-secrets -n bloop-prod -o yaml | \
  sed 's/namespace: bloop-prod/namespace: bloop-staging/' | \
  kubectl apply -f -
```

### 5. Create ConfigMaps

```bash
kubectl create configmap bloop-config \
  --from-literal=redis_url=redis://redis:6379 \
  --from-literal=rabbitmq_url=amqp://bloop:bloop@rabbitmq:5672 \
  --from-literal=environment=production \
  -n bloop-prod
```

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/poorvikab/bloop.git
cd bloop
```

### 2. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Services with Docker Compose

```bash
cd .kiro/specs/deployment-optimization
docker-compose up -d
```

### 4. Verify Services

```bash
# Check service health
curl http://localhost:8000/health

# View logs
docker-compose logs -f api-gateway

# Access Grafana
open http://localhost:3000  # admin/admin
```

### 5. Run Tests

```bash
# Unit tests
docker-compose exec api-gateway pytest tests/unit

# Integration tests
docker-compose exec api-gateway pytest tests/integration

# Property-based tests
docker-compose exec api-gateway pytest tests/property
```

## Staging Deployment

### 1. Build and Push Images

```bash
# Login to container registry
docker login ghcr.io

# Build images
docker build -t ghcr.io/poorvikab/bloop/api-gateway:staging -f backend/Dockerfile.gateway .
docker build -t ghcr.io/poorvikab/bloop/video-service:staging -f backend/Dockerfile.video .
docker build -t ghcr.io/poorvikab/bloop/avatar-service:staging -f backend/Dockerfile.avatar .

# Push images
docker push ghcr.io/poorvikab/bloop/api-gateway:staging
docker push ghcr.io/poorvikab/bloop/video-service:staging
docker push ghcr.io/poorvikab/bloop/avatar-service:staging
```

### 2. Deploy to Staging

```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes-deployment.yaml -n bloop-staging

# Wait for rollout
kubectl rollout status deployment/api-gateway -n bloop-staging
kubectl rollout status deployment/video-service -n bloop-staging
kubectl rollout status deployment/avatar-service -n bloop-staging
```

### 3. Verify Deployment

```bash
# Check pods
kubectl get pods -n bloop-staging

# Check services
kubectl get svc -n bloop-staging

# Test health endpoint
kubectl port-forward svc/api-gateway 8000:80 -n bloop-staging
curl http://localhost:8000/health
```

### 4. Run Smoke Tests

```bash
# Test API endpoints
curl https://staging.bloop.ai/api/v1/health

# Test video generation
curl -X POST https://staging.bloop.ai/api/v1/video/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain photosynthesis", "duration": "short"}'
```

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] All tests passing in CI/CD
- [ ] Staging deployment successful
- [ ] Performance tests completed
- [ ] Database migrations tested
- [ ] Backup verified
- [ ] Rollback plan documented
- [ ] Team notified

### 2. Database Migration

```bash
# Run migrations in init container
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: bloop-prod
spec:
  template:
    spec:
      containers:
      - name: migration
        image: ghcr.io/poorvikab/bloop/api-gateway:latest
        command: ["alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bloop-secrets
              key: database_url
      restartPolicy: Never
EOF

# Wait for completion
kubectl wait --for=condition=complete job/db-migration -n bloop-prod --timeout=5m
```

### 3. Deploy to Production

```bash
# Update image tags
kubectl set image deployment/api-gateway \
  api-gateway=ghcr.io/poorvikab/bloop/api-gateway:v1.0.0 \
  -n bloop-prod

kubectl set image deployment/video-service \
  video-service=ghcr.io/poorvikab/bloop/video-service:v1.0.0 \
  -n bloop-prod

kubectl set image deployment/avatar-service \
  avatar-service=ghcr.io/poorvikab/bloop/avatar-service:v1.0.0 \
  -n bloop-prod

# Monitor rollout
kubectl rollout status deployment/api-gateway -n bloop-prod --watch
```

### 4. Post-Deployment Verification

```bash
# Check pod status
kubectl get pods -n bloop-prod

# Check logs for errors
kubectl logs -l app=api-gateway -n bloop-prod --tail=100

# Test endpoints
curl https://api.bloop.ai/health
curl https://api.bloop.ai/api/v1/health

# Monitor metrics
kubectl port-forward svc/grafana 3000:3000 -n bloop-monitoring
```

### 5. Rollback (if needed)

```bash
# Rollback to previous version
kubectl rollout undo deployment/api-gateway -n bloop-prod
kubectl rollout undo deployment/video-service -n bloop-prod
kubectl rollout undo deployment/avatar-service -n bloop-prod

# Verify rollback
kubectl rollout status deployment/api-gateway -n bloop-prod
```

## Monitoring Setup

### 1. Install Prometheus

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace bloop-monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi
```

### 2. Install Grafana Dashboards

```bash
# Import Bloop dashboards
kubectl apply -f grafana/dashboards/ -n bloop-monitoring
```

### 3. Configure Alertmanager

```bash
kubectl apply -f alert-rules.yaml -n bloop-monitoring

# Configure Slack webhook
kubectl create secret generic alertmanager-slack \
  --from-literal=webhook-url=<SLACK_WEBHOOK_URL> \
  -n bloop-monitoring
```

### 4. Access Monitoring

```bash
# Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n bloop-monitoring

# Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n bloop-monitoring
# Default credentials: admin / prom-operator
```

## Disaster Recovery

### 1. Automated Backups

```bash
# PostgreSQL backup CronJob
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: bloop-prod
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command:
            - /bin/sh
            - -c
            - |
              pg_dump \$DATABASE_URL | gzip > /backup/backup-\$(date +%Y%m%d-%H%M%S).sql.gz
              aws s3 cp /backup/*.sql.gz s3://bloop-backups/postgres/
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: bloop-secrets
                  key: database_url
            volumeMounts:
            - name: backup
              mountPath: /backup
          volumes:
          - name: backup
            emptyDir: {}
          restartPolicy: OnFailure
EOF
```

### 2. Restore from Backup

```bash
# Download latest backup
aws s3 cp s3://bloop-backups/postgres/backup-latest.sql.gz .

# Restore to database
gunzip -c backup-latest.sql.gz | kubectl exec -i postgres-0 -n bloop-prod -- psql -U bloop bloop
```

### 3. Multi-Region Failover

```bash
# Configure DNS failover with Route53/CloudFlare
# Set health checks on primary region
# Automatic failover to secondary region on failure
```

## Troubleshooting

### Common Issues

**Pods Not Starting:**
```bash
# Check pod status
kubectl describe pod <pod-name> -n bloop-prod

# Check logs
kubectl logs <pod-name> -n bloop-prod

# Check events
kubectl get events -n bloop-prod --sort-by='.lastTimestamp'
```

**High Memory Usage:**
```bash
# Check resource usage
kubectl top pods -n bloop-prod

# Increase memory limits
kubectl set resources deployment/api-gateway \
  --limits=memory=2Gi \
  -n bloop-prod
```

**Database Connection Issues:**
```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -- \
  psql postgresql://bloop:<password>@postgres:5432/bloop
```

**Video Generation Failures:**
```bash
# Check video service logs
kubectl logs -l app=video-service -n bloop-prod --tail=100

# Check GPU availability
kubectl describe node <gpu-node-name>

# Restart video service
kubectl rollout restart deployment/video-service -n bloop-prod
```

### Performance Issues

**Slow API Responses:**
```bash
# Check Prometheus metrics
# Query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Scale up API gateway
kubectl scale deployment/api-gateway --replicas=5 -n bloop-prod

# Check database slow queries
kubectl exec -it postgres-0 -n bloop-prod -- psql -U bloop -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

**Cache Issues:**
```bash
# Check Redis status
kubectl exec -it redis-0 -n bloop-prod -- redis-cli INFO

# Clear cache
kubectl exec -it redis-0 -n bloop-prod -- redis-cli FLUSHALL

# Restart Redis
kubectl rollout restart statefulset/redis -n bloop-prod
```

## Support

For additional help:
- Documentation: https://docs.bloop.ai
- GitHub Issues: https://github.com/poorvikab/bloop/issues
- Email: support@bloop.ai
