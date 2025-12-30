# Architecture Diagrams

## System Context Diagram

```mermaid
graph TB
    subgraph "External Users"
        LEARNER[Learners]
        EDUCATOR[Educators]
        ADMIN[Administrators]
        THIRD_PARTY[Third-Party Apps]
    end
    
    subgraph "External Systems"
        LMS[LMS Platforms<br/>Canvas, Moodle, Blackboard]
        NOTES[Note-Taking Apps<br/>Notion, Evernote, OneNote]
        OAUTH[OAuth Providers<br/>Google, GitHub, Microsoft]
        PAYMENT[Payment Processors<br/>Stripe, PayPal]
    end
    
    subgraph "Bloop Platform"
        BLOOP[Bloop System]
    end
    
    subgraph "AI/ML Services"
        OPENAI[OpenAI GPT-4]
        AZURE_TTS[Azure TTS]
        ELEVENLABS[ElevenLabs]
    end
    
    LEARNER -->|Uses| BLOOP
    EDUCATOR -->|Creates Content| BLOOP
    ADMIN -->|Manages| BLOOP
    THIRD_PARTY -->|Integrates via API| BLOOP
    
    BLOOP -->|Authenticates| OAUTH
    BLOOP -->|Syncs Content| LMS
    BLOOP -->|Syncs Notes| NOTES
    BLOOP -->|Processes Payments| PAYMENT
    BLOOP -->|Generates Content| OPENAI
    BLOOP -->|Generates Audio| AZURE_TTS
    BLOOP -->|Generates Audio| ELEVENLABS
```

## Container Diagram

```mermaid
graph TB
    subgraph "Client Applications"
        WEB[Web Application<br/>React + TypeScript]
        MOBILE[Mobile App<br/>React Native]
        API_CLIENT[Third-Party Apps<br/>REST/GraphQL Clients]
    end
    
    subgraph "Edge Layer"
        CDN[CDN<br/>CloudFlare]
        LB[Load Balancer<br/>AWS ALB/NLB]
        APIGW[API Gateway<br/>Kong]
    end
    
    subgraph "Application Services"
        AUTH[Auth Service<br/>FastAPI]
        USER[User Service<br/>FastAPI]
        CONTENT[Content Service<br/>FastAPI]
        VIDEO[Video Service<br/>FastAPI]
        LEARN[Learning Service<br/>FastAPI]
        SOCIAL[Social Service<br/>FastAPI]
        ANALYTICS[Analytics Service<br/>FastAPI]
        NOTIF[Notification Service<br/>Node.js]
        REALTIME[Real-time Service<br/>Node.js + Socket.io]
        INTEGRATION[Integration Service<br/>FastAPI]
    end
    
    subgraph "AI/ML Services"
        LLM[LLM Service<br/>Python]
        TTS[TTS Service<br/>Python]
        MANIM[Manim Renderer<br/>Python]
        AVATAR[Avatar Generator<br/>Python + SadTalker]
        RECOMMEND[Recommendation Engine<br/>Python + ML]
    end
    
    subgraph "Data Stores"
        POSTGRES[(PostgreSQL<br/>User & Transactional Data)]
        MONGO[(MongoDB<br/>Content & Documents)]
        NEO4J[(Neo4j<br/>Relationships & Graphs)]
        INFLUX[(InfluxDB<br/>Time-Series Analytics)]
        REDIS[(Redis<br/>Cache & Sessions)]
        S3[(S3/Blob Storage<br/>Media Files)]
        ELASTIC[(Elasticsearch<br/>Search Index)]
    end
    
    subgraph "Message Infrastructure"
        KAFKA[Kafka<br/>Event Streaming]
        RABBITMQ[RabbitMQ<br/>Task Queue]
    end
    
    WEB --> CDN
    MOBILE --> LB
    API_CLIENT --> APIGW
    CDN --> APIGW
    LB --> APIGW
    
    APIGW --> AUTH
    APIGW --> USER
    APIGW --> CONTENT
    APIGW --> VIDEO
    APIGW --> LEARN
    APIGW --> SOCIAL
    APIGW --> ANALYTICS
    APIGW --> NOTIF
    APIGW --> REALTIME
    APIGW --> INTEGRATION
    
    VIDEO --> LLM
    VIDEO --> TTS
    VIDEO --> MANIM
    VIDEO --> AVATAR
    CONTENT --> LLM
    LEARN --> RECOMMEND
    
    AUTH --> POSTGRES
    USER --> POSTGRES
    USER --> REDIS
    CONTENT --> MONGO
    CONTENT --> S3
    CONTENT --> ELASTIC
    LEARN --> NEO4J
    SOCIAL --> NEO4J
    ANALYTICS --> INFLUX
    VIDEO --> S3
    REALTIME --> REDIS
    
    AUTH --> KAFKA
    CONTENT --> KAFKA
    LEARN --> KAFKA
    SOCIAL --> KAFKA
    VIDEO --> RABBITMQ
    NOTIF --> RABBITMQ
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "DNS & CDN"
        DNS[Route 53 / Cloud DNS]
        CDN[CloudFlare CDN]
    end
    
    subgraph "Region 1 - Primary"
        subgraph "Availability Zone 1A"
            LB1A[Load Balancer]
            K8S1A[Kubernetes Cluster]
            DB1A[(Primary Databases)]
        end
        
        subgraph "Availability Zone 1B"
            LB1B[Load Balancer]
            K8S1B[Kubernetes Cluster]
            DB1B[(Replica Databases)]
        end
        
        subgraph "Availability Zone 1C"
            LB1C[Load Balancer]
            K8S1C[Kubernetes Cluster]
            DB1C[(Replica Databases)]
        end
    end
    
    subgraph "Region 2 - DR"
        subgraph "Availability Zone 2A"
            LB2A[Load Balancer]
            K8S2A[Kubernetes Cluster]
            DB2A[(Standby Databases)]
        end
    end
    
    subgraph "Global Services"
        S3_GLOBAL[S3 Multi-Region]
        KAFKA_GLOBAL[Kafka Multi-Region]
    end
    
    DNS --> CDN
    CDN --> LB1A
    CDN --> LB1B
    CDN --> LB1C
    
    LB1A --> K8S1A
    LB1B --> K8S1B
    LB1C --> K8S1C
    
    K8S1A --> DB1A
    K8S1B --> DB1B
    K8S1C --> DB1C
    
    DB1A -.->|Replication| DB1B
    DB1A -.->|Replication| DB1C
    DB1A -.->|Async Replication| DB2A
    
    K8S1A --> S3_GLOBAL
    K8S1B --> S3_GLOBAL
    K8S1C --> S3_GLOBAL
    K8S2A --> S3_GLOBAL
    
    K8S1A --> KAFKA_GLOBAL
    K8S1B --> KAFKA_GLOBAL
    K8S1C --> KAFKA_GLOBAL
```

## Network Architecture

```mermaid
graph TB
    subgraph "Public Subnet"
        IGW[Internet Gateway]
        NAT[NAT Gateway]
        ALB[Application Load Balancer]
    end
    
    subgraph "Private Subnet - Application Tier"
        APIGW[API Gateway]
        AUTH[Auth Service Pods]
        USER[User Service Pods]
        CONTENT[Content Service Pods]
        VIDEO[Video Service Pods]
        LEARN[Learning Service Pods]
        SOCIAL[Social Service Pods]
    end
    
    subgraph "Private Subnet - AI/ML Tier"
        LLM[LLM Service Pods<br/>GPU Instances]
        TTS[TTS Service Pods]
        MANIM[Manim Renderer Pods<br/>GPU Instances]
        AVATAR[Avatar Generator Pods<br/>GPU Instances]
    end
    
    subgraph "Private Subnet - Data Tier"
        POSTGRES[(PostgreSQL<br/>RDS Multi-AZ)]
        MONGO[(MongoDB<br/>Atlas Cluster)]
        NEO4J[(Neo4j<br/>Aura)]
        REDIS[(Redis<br/>ElastiCache)]
    end
    
    subgraph "Private Subnet - Message Tier"
        KAFKA[Kafka Cluster<br/>MSK]
        RABBITMQ[RabbitMQ Cluster<br/>AmazonMQ)]
    end
    
    IGW --> ALB
    ALB --> APIGW
    
    APIGW --> AUTH
    APIGW --> USER
    APIGW --> CONTENT
    APIGW --> VIDEO
    APIGW --> LEARN
    APIGW --> SOCIAL
    
    VIDEO --> LLM
    VIDEO --> TTS
    VIDEO --> MANIM
    VIDEO --> AVATAR
    
    AUTH --> POSTGRES
    USER --> POSTGRES
    CONTENT --> MONGO
    LEARN --> NEO4J
    SOCIAL --> NEO4J
    
    AUTH --> REDIS
    USER --> REDIS
    
    AUTH --> KAFKA
    CONTENT --> KAFKA
    VIDEO --> RABBITMQ
    
    AUTH --> NAT
    VIDEO --> NAT
    LLM --> NAT
```

## Service Mesh Architecture

```mermaid
graph TB
    subgraph "Istio Service Mesh"
        subgraph "Control Plane"
            PILOT[Pilot<br/>Service Discovery]
            CITADEL[Citadel<br/>Certificate Management]
            GALLEY[Galley<br/>Configuration]
        end
        
        subgraph "Data Plane"
            subgraph "Auth Service"
                AUTH_APP[Auth App]
                AUTH_PROXY[Envoy Sidecar]
            end
            
            subgraph "User Service"
                USER_APP[User App]
                USER_PROXY[Envoy Sidecar]
            end
            
            subgraph "Content Service"
                CONTENT_APP[Content App]
                CONTENT_PROXY[Envoy Sidecar]
            end
            
            subgraph "Video Service"
                VIDEO_APP[Video App]
                VIDEO_PROXY[Envoy Sidecar]
            end
        end
    end
    
    PILOT -.->|Config| AUTH_PROXY
    PILOT -.->|Config| USER_PROXY
    PILOT -.->|Config| CONTENT_PROXY
    PILOT -.->|Config| VIDEO_PROXY
    
    CITADEL -.->|mTLS Certs| AUTH_PROXY
    CITADEL -.->|mTLS Certs| USER_PROXY
    CITADEL -.->|mTLS Certs| CONTENT_PROXY
    CITADEL -.->|mTLS Certs| VIDEO_PROXY
    
    AUTH_PROXY <-->|mTLS| USER_PROXY
    USER_PROXY <-->|mTLS| CONTENT_PROXY
    CONTENT_PROXY <-->|mTLS| VIDEO_PROXY
    
    AUTH_APP --> AUTH_PROXY
    USER_APP --> USER_PROXY
    CONTENT_APP --> CONTENT_PROXY
    VIDEO_APP --> VIDEO_PROXY
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant CDN
    participant API_GW as API Gateway
    participant Auth as Auth Service
    participant Content as Content Service
    participant Kafka
    participant Analytics as Analytics Service
    participant InfluxDB
    participant Redis
    
    User->>CDN: Request Content
    CDN->>API_GW: Forward Request
    API_GW->>Auth: Validate Token
    Auth->>Redis: Check Token Cache
    Redis-->>Auth: Token Valid
    Auth-->>API_GW: Authorized
    
    API_GW->>Content: Get Content
    Content->>Redis: Check Cache
    
    alt Cache Hit
        Redis-->>Content: Cached Data
    else Cache Miss
        Content->>MongoDB: Query Content
        MongoDB-->>Content: Content Data
        Content->>Redis: Update Cache
    end
    
    Content-->>API_GW: Content Response
    API_GW-->>CDN: Response
    CDN-->>User: Deliver Content
    
    Content->>Kafka: Publish Event
    Kafka->>Analytics: Consume Event
    Analytics->>InfluxDB: Store Metrics
```


## Security Architecture

```mermaid
graph TB
    subgraph "External Layer"
        USER[Users]
        ATTACKER[Potential Attackers]
    end
    
    subgraph "Security Perimeter"
        WAF[Web Application Firewall<br/>AWS WAF / CloudFlare]
        DDOS[DDoS Protection<br/>CloudFlare / AWS Shield]
    end
    
    subgraph "Authentication Layer"
        OAUTH[OAuth 2.0 / OIDC]
        MFA[Multi-Factor Auth]
        JWT[JWT Token Service]
    end
    
    subgraph "Authorization Layer"
        RBAC[Role-Based Access Control]
        ABAC[Attribute-Based Access Control]
        POLICY[Policy Engine]
    end
    
    subgraph "Application Security"
        INPUT_VAL[Input Validation]
        RATE_LIMIT[Rate Limiting]
        CSRF[CSRF Protection]
        XSS[XSS Prevention]
    end
    
    subgraph "Data Security"
        ENCRYPT_TRANSIT[TLS 1.3 Encryption]
        ENCRYPT_REST[AES-256 Encryption at Rest]
        KEY_MGMT[Key Management Service]
        DATA_MASK[Data Masking]
    end
    
    subgraph "Network Security"
        VPC[Virtual Private Cloud]
        SG[Security Groups]
        NACL[Network ACLs]
        PRIVATE_SUBNET[Private Subnets]
    end
    
    subgraph "Monitoring & Audit"
        SIEM[SIEM System]
        AUDIT_LOG[Audit Logs]
        THREAT_DETECT[Threat Detection]
        ALERT[Alerting System]
    end
    
    USER --> WAF
    ATTACKER -.->|Blocked| WAF
    WAF --> DDOS
    DDOS --> OAUTH
    
    OAUTH --> MFA
    MFA --> JWT
    JWT --> RBAC
    RBAC --> POLICY
    POLICY --> INPUT_VAL
    
    INPUT_VAL --> RATE_LIMIT
    RATE_LIMIT --> CSRF
    CSRF --> XSS
    
    XSS --> ENCRYPT_TRANSIT
    ENCRYPT_TRANSIT --> VPC
    VPC --> SG
    SG --> PRIVATE_SUBNET
    
    PRIVATE_SUBNET --> ENCRYPT_REST
    ENCRYPT_REST --> KEY_MGMT
    
    WAF --> SIEM
    OAUTH --> AUDIT_LOG
    RBAC --> AUDIT_LOG
    AUDIT_LOG --> THREAT_DETECT
    THREAT_DETECT --> ALERT
```

## Monitoring & Observability Architecture

```mermaid
graph TB
    subgraph "Application Layer"
        SERVICES[Microservices]
    end
    
    subgraph "Instrumentation"
        METRICS[Metrics Collection<br/>Prometheus Client]
        TRACES[Distributed Tracing<br/>OpenTelemetry]
        LOGS[Structured Logging<br/>JSON Format]
    end
    
    subgraph "Collection Layer"
        PROM[Prometheus<br/>Metrics Storage]
        JAEGER[Jaeger<br/>Trace Storage]
        FLUENTD[Fluentd<br/>Log Aggregation]
    end
    
    subgraph "Storage Layer"
        PROM_DB[(Prometheus TSDB)]
        JAEGER_DB[(Jaeger Storage)]
        ELASTIC[(Elasticsearch<br/>Log Storage)]
    end
    
    subgraph "Visualization Layer"
        GRAFANA[Grafana<br/>Dashboards]
        JAEGER_UI[Jaeger UI<br/>Trace Visualization]
        KIBANA[Kibana<br/>Log Analysis]
    end
    
    subgraph "Alerting Layer"
        ALERT_MGR[Alert Manager]
        PAGERDUTY[PagerDuty]
        SLACK[Slack]
        EMAIL[Email]
    end
    
    SERVICES --> METRICS
    SERVICES --> TRACES
    SERVICES --> LOGS
    
    METRICS --> PROM
    TRACES --> JAEGER
    LOGS --> FLUENTD
    
    PROM --> PROM_DB
    JAEGER --> JAEGER_DB
    FLUENTD --> ELASTIC
    
    PROM_DB --> GRAFANA
    JAEGER_DB --> JAEGER_UI
    ELASTIC --> KIBANA
    
    GRAFANA --> ALERT_MGR
    ALERT_MGR --> PAGERDUTY
    ALERT_MGR --> SLACK
    ALERT_MGR --> EMAIL
```

## CI/CD Pipeline Architecture

```mermaid
graph LR
    subgraph "Source Control"
        GIT[Git Repository<br/>GitHub/GitLab]
    end
    
    subgraph "CI Pipeline"
        TRIGGER[Webhook Trigger]
        BUILD[Build & Test]
        LINT[Lint & Format]
        UNIT[Unit Tests]
        PROPERTY[Property Tests]
        INTEGRATION[Integration Tests]
        SECURITY[Security Scan]
        COVERAGE[Coverage Report]
    end
    
    subgraph "Artifact Management"
        DOCKER_REG[Docker Registry<br/>ECR/GCR]
        HELM_REPO[Helm Repository]
    end
    
    subgraph "CD Pipeline"
        DEPLOY_DEV[Deploy to Dev]
        E2E_DEV[E2E Tests - Dev]
        DEPLOY_STAGING[Deploy to Staging]
        E2E_STAGING[E2E Tests - Staging]
        PERF_TEST[Performance Tests]
        APPROVAL[Manual Approval]
        DEPLOY_PROD[Deploy to Production]
        SMOKE_TEST[Smoke Tests]
        ROLLBACK[Rollback on Failure]
    end
    
    subgraph "Environments"
        DEV[Development<br/>Kubernetes]
        STAGING[Staging<br/>Kubernetes]
        PROD[Production<br/>Kubernetes]
    end
    
    GIT --> TRIGGER
    TRIGGER --> BUILD
    BUILD --> LINT
    LINT --> UNIT
    UNIT --> PROPERTY
    PROPERTY --> INTEGRATION
    INTEGRATION --> SECURITY
    SECURITY --> COVERAGE
    
    COVERAGE --> DOCKER_REG
    COVERAGE --> HELM_REPO
    
    DOCKER_REG --> DEPLOY_DEV
    DEPLOY_DEV --> DEV
    DEV --> E2E_DEV
    
    E2E_DEV --> DEPLOY_STAGING
    DEPLOY_STAGING --> STAGING
    STAGING --> E2E_STAGING
    E2E_STAGING --> PERF_TEST
    
    PERF_TEST --> APPROVAL
    APPROVAL --> DEPLOY_PROD
    DEPLOY_PROD --> PROD
    PROD --> SMOKE_TEST
    
    SMOKE_TEST -.->|Failure| ROLLBACK
    ROLLBACK -.-> PROD
```

## Disaster Recovery Architecture

```mermaid
graph TB
    subgraph "Primary Region - US East"
        subgraph "Production"
            PROD_APP[Application Services]
            PROD_DB[(Primary Databases)]
            PROD_S3[S3 Primary]
        end
    end
    
    subgraph "Secondary Region - US West"
        subgraph "Hot Standby"
            DR_APP[Application Services<br/>Scaled Down]
            DR_DB[(Replica Databases<br/>Read-Only)]
            DR_S3[S3 Replica]
        end
    end
    
    subgraph "Backup Region - EU"
        subgraph "Cold Standby"
            BACKUP_DB[(Database Backups)]
            BACKUP_S3[S3 Backup]
        end
    end
    
    subgraph "Failover Management"
        HEALTH_CHECK[Health Monitoring]
        FAILOVER_TRIGGER[Failover Trigger]
        DNS_SWITCH[DNS Failover<br/>Route 53]
    end
    
    PROD_DB -.->|Async Replication| DR_DB
    PROD_S3 -.->|Cross-Region Replication| DR_S3
    PROD_DB -.->|Daily Snapshots| BACKUP_DB
    PROD_S3 -.->|Backup| BACKUP_S3
    
    HEALTH_CHECK -->|Monitor| PROD_APP
    HEALTH_CHECK -->|Monitor| PROD_DB
    
    HEALTH_CHECK -.->|Failure Detected| FAILOVER_TRIGGER
    FAILOVER_TRIGGER -.->|Promote| DR_DB
    FAILOVER_TRIGGER -.->|Scale Up| DR_APP
    FAILOVER_TRIGGER -.->|Update| DNS_SWITCH
    
    DNS_SWITCH -.->|Redirect Traffic| DR_APP
```

## Scaling Architecture

```mermaid
graph TB
    subgraph "Horizontal Pod Autoscaler"
        HPA[HPA Controller]
        METRICS[Metrics Server]
    end
    
    subgraph "Cluster Autoscaler"
        CA[Cluster Autoscaler]
        CLOUD_API[Cloud Provider API]
    end
    
    subgraph "Application Pods"
        POD1[Pod 1]
        POD2[Pod 2]
        POD3[Pod 3]
        PODN[Pod N]
    end
    
    subgraph "Worker Nodes"
        NODE1[Node 1]
        NODE2[Node 2]
        NODE3[Node 3]
        NODEN[Node N]
    end
    
    subgraph "Scaling Triggers"
        CPU[CPU > 70%]
        MEMORY[Memory > 80%]
        CUSTOM[Custom Metrics<br/>Request Rate, Queue Depth]
    end
    
    CPU --> METRICS
    MEMORY --> METRICS
    CUSTOM --> METRICS
    
    METRICS --> HPA
    HPA -.->|Scale Pods| POD1
    HPA -.->|Scale Pods| POD2
    HPA -.->|Scale Pods| POD3
    HPA -.->|Scale Pods| PODN
    
    POD1 --> NODE1
    POD2 --> NODE2
    POD3 --> NODE3
    PODN --> NODEN
    
    HPA -.->|Insufficient Resources| CA
    CA --> CLOUD_API
    CLOUD_API -.->|Provision Nodes| NODEN
```

## Event-Driven Architecture

```mermaid
graph TB
    subgraph "Event Producers"
        AUTH_SVC[Auth Service]
        USER_SVC[User Service]
        CONTENT_SVC[Content Service]
        VIDEO_SVC[Video Service]
        SOCIAL_SVC[Social Service]
    end
    
    subgraph "Event Bus"
        KAFKA[Apache Kafka]
        
        subgraph "Topics"
            USER_EVENTS[user.events]
            CONTENT_EVENTS[content.events]
            VIDEO_EVENTS[video.events]
            SOCIAL_EVENTS[social.events]
            ANALYTICS_EVENTS[analytics.events]
        end
    end
    
    subgraph "Event Consumers"
        ANALYTICS_SVC[Analytics Service]
        NOTIF_SVC[Notification Service]
        SEARCH_INDEX[Search Indexer]
        RECOMMEND_SVC[Recommendation Service]
        AUDIT_SVC[Audit Service]
    end
    
    AUTH_SVC -->|Publish| USER_EVENTS
    USER_SVC -->|Publish| USER_EVENTS
    CONTENT_SVC -->|Publish| CONTENT_EVENTS
    VIDEO_SVC -->|Publish| VIDEO_EVENTS
    SOCIAL_SVC -->|Publish| SOCIAL_EVENTS
    
    USER_EVENTS --> KAFKA
    CONTENT_EVENTS --> KAFKA
    VIDEO_EVENTS --> KAFKA
    SOCIAL_EVENTS --> KAFKA
    
    KAFKA --> ANALYTICS_SVC
    KAFKA --> NOTIF_SVC
    KAFKA --> SEARCH_INDEX
    KAFKA --> RECOMMEND_SVC
    KAFKA --> AUDIT_SVC
    
    ANALYTICS_SVC -->|Publish| ANALYTICS_EVENTS
    ANALYTICS_EVENTS --> KAFKA
```

