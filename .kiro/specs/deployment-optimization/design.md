# Design Document: Deployment Strategies and Performance Optimization

## Overview

This design document outlines a comprehensive deployment and optimization strategy for the Bloop AI-powered educational learning platform. The solution transforms the current monolithic architecture into a scalable, cloud-native microservices platform with automated deployment pipelines, multi-layer caching, and performance optimizations across all components.

The design addresses three critical areas:
1. **Infrastructure & Deployment**: Containerization, Kubernetes orchestration, CI/CD automation
2. **Performance Optimization**: Caching strategies, async processing, GPU acceleration
3. **Operational Excellence**: Monitoring, security, disaster recovery, cost optimization

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Cloud Infrastructure                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Region 1   │  │   Region 2   │  │   Region 3   │         │
│  │  (Primary)   │  │  (Failover)  │  │   (DR Site)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Global CDN      │
                    │  (CloudFlare/     │
                    │   CloudFront)     │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Load Balancer    │
                    │  (NGINX/ALB)      │
                    │  - SSL Termination│
                    │  - Rate Limiting  │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  API Gateway   │  │  API Gateway    │  │  API Gateway    │
│   (Instance 1) │  │  (Instance 2)   │  │  (Instance N)   │
└───────┬────────┘  └────────┬────────┘  └────────┬────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │    Kubernetes Cluster         │
              │                               │
              │  ┌─────────────────────────┐ │
              │  │   Service Mesh          │ │
              │  │   (Istio/Linkerd)       │ │
              │  └─────────────────────────┘ │
              │                               │
              │  ┌─────────────────────────┐ │
              │  │  Microservices Layer    │ │
              │  │                         │ │
              │  │  ┌──────────────────┐  │ │
              │  │  │  ASK Service     │  │ │
              │  │  │  - Q&A           │  │ │
              │  │  │  - Flashcards    │  │ │
              │  │  │  - Quiz Gen      │  │ │
              │  │  └──────────────────┘  │ │
              │  │                         │ │
              │  │  ┌──────────────────┐  │ │
              │  │  │  PLAN Service    │  │ │
              │  │  │  - Roadmap Gen   │  │ │
              │  │  └──────────────────┘  │ │
              │  │                         │ │
              │  │  ┌──────────────────┐  │ │
              │  │  │  PLAY Service    │  │ │
              │  │  │  - Games         │  │ │
              │  │  │  - Voice I/O     │  │ │
              │  │  └──────────────────┘  │ │
              │  │                         │ │
              │  │  ┌──────────────────┐  │ │
              │  │  │  Video Service   │  │ │
              │  │  │  - Manim Render  │  │ │
              │  │  │  - Scene Manager │  │ │
              │  │  └──────────────────┘  │ │
              │  │                         │ │
              │  │  ┌──────────────────┐  │ │
              │  │  │  Avatar Service  │  │ │
              │  │  │  - SadTalker     │  │ │
              │  │  │  - GPU Workers   │  │ │
              │  │  └──────────────────┘  │ │
              │  └─────────────────────────┘ │
              └───────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  Redis Cache   │  │  Message Queue  │  │  PostgreSQL     │
│  - Session     │  │  (RabbitMQ)     │  │  Cluster        │
│  - Results     │  │  - Video Jobs   │  │  - Primary      │
│  - Rate Limit  │  │  - Avatar Jobs  │  │  - Replicas     │
└────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Object Storage   │
                    │  (S3/Azure Blob)  │
                    │  - Videos         │
                    │  - Documents      │
                    │  - Avatars        │
                    └───────────────────┘
```

## Components and Interfaces

### 1. Containerization Layer

**Docker Multi-Stage Builds**

Each service uses optimized multi-stage Docker builds:

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Service Containers:**
- `bloop-api-gateway`: FastAPI gateway (200MB)
- `bloop-ask-service`: ASK mode services (250MB)
- `bloop-plan-service`: PLAN mode services (220MB)
- `bloop-play-service`: PLAY mode services (280MB)
- `bloop-video-service`: Manim rendering (1.2GB with LaTeX)
- `bloop-avatar-service`: SadTalker GPU service (3.5GB with models)
- `bloop-worker`: Celery task workers (300MB)

### 2. Kubernetes Orchestration

**Namespace Organization:**
- `bloop-prod`: Production workloads
- `bloop-staging`: Staging environment
- `bloop-dev`: Development environment
- `bloop-monitoring`: Observability stack

**Deployment Strategy:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: bloop-prod
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
        version: v1.0.0
    spec:
      containers:
      - name: api-gateway
        image: bloop/api-gateway:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 3. CI/CD Pipeline Architecture

**GitHub Actions Workflow:**

```yaml
name: Deploy Bloop Platform

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
      
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push images
        run: |
          docker build -t bloop/api-gateway:${{ github.sha }} .
          docker push bloop/api-gateway:${{ github.sha }}
  
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/api-gateway \
            api-gateway=bloop/api-gateway:${{ github.sha }} \
            -n bloop-staging
  
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy to production
        run: |
          kubectl set image deployment/api-gateway \
            api-gateway=bloop/api-gateway:${{ github.sha }} \
            -n bloop-prod
```

### 4. Load Balancing and API Gateway

**NGINX Configuration:**

```nginx
upstream api_backend {
    least_conn;
    server api-gateway-1:8000 max_fails=3 fail_timeout=30s;
    server api-gateway-2:8000 max_fails=3 fail_timeout=30s;
    server api-gateway-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.bloop.ai;
    
    ssl_certificate /etc/ssl/certs/bloop.crt;
    ssl_certificate_key /etc/ssl/private/bloop.key;
    ssl_protocols TLSv1.3;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
    
    # Compression
    gzip on;
    gzip_types application/json text/plain;
    
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5. Caching Architecture

**Multi-Layer Caching Strategy:**

```python
# Layer 1: Application-level cache (in-memory)
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_flashcard_template(difficulty: str) -> dict:
    return load_template(difficulty)

# Layer 2: Redis cache (distributed)
import redis
from typing import Optional

class CacheService:
    def __init__(self):
        self.redis = redis.Redis(
            host='redis-cluster',
            port=6379,
            decode_responses=True
        )
    
    def get_cached_video(self, query_hash: str) -> Optional[str]:
        return self.redis.get(f"video:{query_hash}")
    
    def cache_video(self, query_hash: str, video_url: str, ttl: int = 3600):
        self.redis.setex(f"video:{query_hash}", ttl, video_url)
    
    def get_flashcards(self, doc_id: str) -> Optional[list]:
        cached = self.redis.get(f"flashcards:{doc_id}")
        return json.loads(cached) if cached else None

# Layer 3: CDN cache (CloudFront/CloudFlare)
# Configured via headers
response.headers["Cache-Control"] = "public, max-age=86400"
response.headers["CDN-Cache-Control"] = "max-age=604800"
```

### 6. Asynchronous Task Processing

**Celery Configuration:**

```python
from celery import Celery
from kombu import Queue

app = Celery('bloop')

app.conf.update(
    broker_url='amqp://rabbitmq:5672',
    result_backend='redis://redis:6379/0',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'tasks.generate_video': {'queue': 'video_queue'},
        'tasks.generate_avatar': {'queue': 'avatar_queue'},
        'tasks.generate_flashcards': {'queue': 'default'},
    },
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('video_queue', routing_key='video', priority=5),
        Queue('avatar_queue', routing_key='avatar', priority=3),
    )
)

@app.task(bind=True, max_retries=3)
def generate_video(self, query: str, options: dict):
    try:
        # Video generation logic
        result = video_service.generate(query, options)
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

## Data Models

### Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class DeploymentConfig(BaseModel):
    environment: str = Field(..., description="dev/staging/prod")
    replicas: int = Field(default=3, ge=1, le=10)
    resources: ResourceConfig
    autoscaling: AutoscalingConfig
    monitoring: MonitoringConfig

class ResourceConfig(BaseModel):
    cpu_request: str = "500m"
    cpu_limit: str = "2000m"
    memory_request: str = "1Gi"
    memory_limit: str = "4Gi"
    gpu_enabled: bool = False
    gpu_count: int = 0

class AutoscalingConfig(BaseModel):
    enabled: bool = True
    min_replicas: int = 2
    max_replicas: int = 10
    target_cpu_percent: int = 70
    target_memory_percent: int = 80

class CacheConfig(BaseModel):
    redis_url: str
    ttl_video: int = 3600
    ttl_flashcards: int = 7200
    ttl_quiz: int = 7200
    max_memory: str = "2gb"
    eviction_policy: str = "allkeys-lru"
```

### Monitoring Metrics Schema

```python
class ServiceMetrics(BaseModel):
    service_name: str
    timestamp: datetime
    request_count: int
    error_count: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    cpu_usage_percent: float
    memory_usage_mb: float
    active_connections: int

class VideoGenerationMetrics(BaseModel):
    video_id: str
    total_duration_sec: float
    scene_count: int
    scenes_succeeded: int
    scenes_failed: int
    scenes_skipped: int
    rendering_time_sec: float
    tts_time_sec: float
    ffmpeg_time_sec: float
    cache_hit: bool
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Container Health Consistency

*For any* deployed container instance, if the health check endpoint returns success, then the container should be able to process requests successfully.

**Validates: Requirements 1.3, 1.4**

### Property 2: Zero-Downtime Deployment

*For any* rolling update deployment, the total number of available replicas should never drop below the minimum required threshold during the update process.

**Validates: Requirements 2.4**

### Property 3: Cache Consistency

*For any* cached item with a given key, retrieving the item before TTL expiration should return the same value that was originally stored.

**Validates: Requirements 6.1, 6.2, 6.3**

### Property 4: Task Retry Idempotency

*For any* asynchronous task that is retried after failure, executing the task multiple times with the same input should produce the same final result.

**Validates: Requirements 7.5**

### Property 5: Load Distribution Fairness

*For any* set of healthy backend instances, the load balancer should distribute requests such that no single instance receives more than 150% of the average load over a 5-minute window.

**Validates: Requirements 5.1, 5.2**

### Property 6: Auto-Scaling Responsiveness

*For any* sustained load increase that exceeds the target CPU threshold, the auto-scaler should add new replicas within 60 seconds.

**Validates: Requirements 2.2, 16.1**

### Property 7: Database Connection Pool Efficiency

*For any* database connection pool, the number of active connections should never exceed the configured maximum, and idle connections should be released within the configured timeout.

**Validates: Requirements 8.2**

### Property 8: Monitoring Alert Accuracy

*For any* critical threshold breach, the monitoring system should generate an alert within 30 seconds with accurate context about the issue.

**Validates: Requirements 9.5**

### Property 9: Secrets Isolation

*For any* deployed service, sensitive credentials should never appear in container logs, environment variable dumps, or error messages.

**Validates: Requirements 14.2, 14.4**

### Property 10: Backup Recoverability

*For any* automated backup, restoring from that backup should result in a system state that is consistent with the state at the time the backup was taken.

**Validates: Requirements 15.3**

### Property 11: Rate Limit Enforcement

*For any* API client, when the request rate exceeds the configured limit, subsequent requests should receive 429 status codes until the rate window resets.

**Validates: Requirements 5.3**

### Property 12: GPU Resource Allocation

*For any* GPU-enabled pod, the pod should have exclusive access to the allocated GPU resources, and GPU memory should be released when the pod terminates.

**Validates: Requirements 10.2, 11.1**

## Error Handling

### Deployment Failures

**Container Startup Failures:**
- Implement readiness probes with appropriate delays
- Log detailed error messages to centralized logging
- Prevent traffic routing to unhealthy containers
- Automatic rollback on repeated failures

**Database Migration Failures:**
- Run migrations in init containers before main app
- Implement migration versioning and rollback scripts
- Test migrations on staging before production
- Maintain migration logs for audit trail

**Configuration Errors:**
- Validate all configuration on startup
- Fail fast with clear error messages
- Use configuration schemas for validation
- Provide configuration examples in documentation

### Runtime Failures

**Service Degradation:**
- Implement circuit breakers for external dependencies
- Graceful degradation when services are unavailable
- Return cached results when possible
- Clear error messages to users

**Resource Exhaustion:**
- Set resource limits on all containers
- Implement memory leak detection
- Auto-restart containers on OOM errors
- Alert on sustained high resource usage

**Task Processing Failures:**
- Retry with exponential backoff
- Dead letter queue for permanently failed tasks
- Detailed error logging with context
- Manual intervention queue for complex failures

### Monitoring and Alerting

**Alert Severity Levels:**
- **Critical**: Service down, data loss risk (page on-call)
- **High**: Performance degradation, partial outage (notify team)
- **Medium**: Resource warnings, elevated errors (ticket)
- **Low**: Informational, trends (dashboard only)

**Alert Routing:**
```yaml
alerting:
  routes:
    - match:
        severity: critical
      receiver: pagerduty
      repeat_interval: 5m
    
    - match:
        severity: high
      receiver: slack-alerts
      repeat_interval: 15m
    
    - match:
        severity: medium
      receiver: email-team
      repeat_interval: 1h
```

## Testing Strategy

### Unit Testing

**Infrastructure as Code Tests:**
- Validate Kubernetes manifests with kubeval
- Test Terraform configurations with terratest
- Validate Docker builds complete successfully
- Test configuration parsing and validation

**Service Tests:**
- Test cache hit/miss scenarios
- Test rate limiting logic
- Test health check endpoints
- Test graceful shutdown procedures

### Integration Testing

**Service Communication:**
- Test API gateway routing to services
- Test message queue delivery
- Test database connection pooling
- Test cache invalidation across services

**Deployment Tests:**
- Test rolling update procedures
- Test auto-scaling triggers
- Test load balancer failover
- Test secret rotation

### Property-Based Testing

**Load Balancing Properties:**
- Generate random request patterns
- Verify fair distribution across backends
- Test failover behavior with random failures
- Verify sticky session consistency

**Caching Properties:**
- Generate random cache operations
- Verify TTL expiration behavior
- Test cache invalidation correctness
- Verify cache hit rate under load

**Auto-Scaling Properties:**
- Generate random load patterns
- Verify scaling decisions are correct
- Test scale-up and scale-down timing
- Verify resource limits are respected

### Performance Testing

**Load Testing:**
- Simulate 1000 concurrent users
- Test video generation under load
- Test API response times at scale
- Identify bottlenecks and limits

**Stress Testing:**
- Push system beyond normal capacity
- Identify breaking points
- Test recovery from overload
- Validate error handling under stress

**Endurance Testing:**
- Run at normal load for 24+ hours
- Detect memory leaks
- Verify log rotation
- Test backup procedures

### Chaos Engineering

**Failure Injection:**
- Random pod termination
- Network latency injection
- Disk space exhaustion
- Database connection failures

**Recovery Validation:**
- Verify automatic recovery
- Test alert generation
- Validate data consistency
- Measure recovery time

## Performance Optimization Details

### Video Generation Optimization

**Parallel Scene Rendering:**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

class OptimizedVideoService:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def render_scenes_parallel(self, scenes: List[Scene]) -> List[VideoSegment]:
        futures = {
            self.executor.submit(self.render_scene, scene): scene 
            for scene in scenes
        }
        
        results = []
        for future in as_completed(futures):
            scene = futures[future]
            try:
                result = future.result(timeout=120)
                results.append(result)
            except Exception as e:
                logger.error(f"Scene {scene.id} failed: {e}")
                results.append(None)
        
        return results
    
    def render_scene(self, scene: Scene) -> VideoSegment:
        # Check cache first
        cache_key = self.get_scene_cache_key(scene)
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Render with GPU acceleration
        with gpu_context():
            segment = manim_render(scene, quality="high", gpu=True)
        
        # Cache result
        self.cache.set(cache_key, segment, ttl=3600)
        return segment
```

**FFmpeg Optimization:**

```python
def optimize_ffmpeg_encoding(input_video: str, output_video: str):
    """Optimized FFmpeg encoding for web delivery"""
    cmd = [
        'ffmpeg',
        '-i', input_video,
        '-c:v', 'libx264',           # H.264 codec
        '-preset', 'fast',            # Fast encoding
        '-crf', '23',                 # Quality (18-28 range)
        '-c:a', 'aac',                # AAC audio
        '-b:a', '128k',               # Audio bitrate
        '-movflags', '+faststart',    # Web optimization
        '-threads', '4',              # Parallel encoding
        output_video
    ]
    subprocess.run(cmd, check=True)
```

### Avatar Generation Optimization

**Batch Processing:**

```python
class AvatarBatchProcessor:
    def __init__(self, batch_size: int = 4):
        self.batch_size = batch_size
        self.queue = []
    
    async def process_avatar_request(self, request: AvatarRequest) -> str:
        # Add to batch queue
        future = asyncio.Future()
        self.queue.append((request, future))
        
        # Process batch when full
        if len(self.queue) >= self.batch_size:
            await self.process_batch()
        
        return await future
    
    async def process_batch(self):
        batch = self.queue[:self.batch_size]
        self.queue = self.queue[self.batch_size:]
        
        # Batch inference on GPU
        requests = [req for req, _ in batch]
        results = await self.sadtalker_batch_inference(requests)
        
        # Resolve futures
        for (_, future), result in zip(batch, results):
            future.set_result(result)
```

**Model Optimization:**

```python
# Use TensorRT for faster inference
import torch
from torch2trt import torch2trt

class OptimizedSadTalker:
    def __init__(self, model_path: str):
        # Load model
        self.model = load_sadtalker_model(model_path)
        
        # Convert to TensorRT
        dummy_input = torch.randn(1, 3, 256, 256).cuda()
        self.model_trt = torch2trt(
            self.model,
            [dummy_input],
            fp16_mode=True,  # Half precision
            max_batch_size=4
        )
    
    def generate(self, image: np.ndarray, audio: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            result = self.model_trt(image, audio)
        return result
```

### Database Optimization

**Connection Pooling:**

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Base connections
    max_overflow=10,           # Additional connections
    pool_timeout=30,           # Wait timeout
    pool_recycle=3600,         # Recycle after 1 hour
    pool_pre_ping=True,        # Verify connections
    echo_pool=True             # Log pool events
)
```

**Query Optimization:**

```python
# Use indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_videos_created_at ON videos(created_at DESC);
CREATE INDEX idx_flashcards_document_id ON flashcards(document_id);

# Use query optimization
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Eager loading to avoid N+1 queries
query = (
    select(Document)
    .options(selectinload(Document.flashcards))
    .where(Document.user_id == user_id)
)
```

### API Optimization

**Response Compression:**

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Async Endpoints:**

```python
from fastapi import FastAPI, BackgroundTasks
import asyncio

@app.post("/api/v1/video/generate")
async def generate_video(
    request: VideoRequest,
    background_tasks: BackgroundTasks
):
    # Create job immediately
    job_id = create_job(request)
    
    # Process in background
    background_tasks.add_task(process_video_generation, job_id, request)
    
    return {"job_id": job_id, "status": "processing"}

async def process_video_generation(job_id: str, request: VideoRequest):
    try:
        result = await video_service.generate(request)
        update_job_status(job_id, "completed", result)
    except Exception as e:
        update_job_status(job_id, "failed", str(e))
```

**GraphQL for Flexible Queries:**

```python
import strawberry
from typing import List

@strawberry.type
class Document:
    id: str
    title: str
    content: str
    flashcards: List['Flashcard']
    quizzes: List['Quiz']

@strawberry.type
class Query:
    @strawberry.field
    async def document(self, id: str) -> Document:
        return await get_document(id)
    
    @strawberry.field
    async def documents(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Document]:
        return await get_documents(limit, offset)

schema = strawberry.Schema(query=Query)
```

