# ParkWise Configuration Guide

This guide provides detailed information on how to configure the ParkWise parking management system for different environments and use cases.

## Table of Contents
- [Environment Configuration](#environment-configuration)
- [Database Configuration](#database-configuration)
- [Security Configuration](#security-configuration)
- [Service Configuration](#service-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Performance Tuning](#performance-tuning)
- [Production Deployment](#production-deployment)

## Environment Configuration

### .env File Setup

The system uses a `.env` file to manage configuration. Copy the example file:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `REDIS_URL` | Redis connection string | - | Yes |
| `JWT_SECRET_KEY` | Secret for JWT signing | - | Yes |
| `JWT_ALGORITHM` | JWT algorithm | HS256 | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | 30 | No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | 7 | No |
| `PREDICTOR_URL` | URL for prediction service | http://predictor:8080 | No |
| `HOST` | Server host | 0.0.0.0 | No |
| `PORT` | Server port | 8000 | No |

### Generating Secure Keys

For production, generate secure keys:

```bash
# Generate JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate edge API key
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

## Database Configuration

### PostgreSQL Setup

For production, consider these PostgreSQL settings:

```sql
-- Connection settings
max_connections = 100
shared_buffers = 25% of RAM
effective_cache_size = 50-75% of RAM

-- Performance settings
work_mem = 4MB
maintenance_work_mem = 64MB
```

### Connection Pooling

Configure connection pooling in your production environment:

```python
# In production settings
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
)
```

## Security Configuration

### JWT Security

- Use a strong, randomly generated `JWT_SECRET_KEY`
- Set appropriate token expiration times
- Implement refresh token rotation
- Use HTTPS in production

### API Security

- Use rate limiting to prevent abuse
- Implement proper CORS policies
- Secure camera feed endpoints with proper authentication

### Password Security

The system uses bcrypt for password hashing:

```python
# Password strength requirements
MIN_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGIT = True
```

## Service Configuration

### Backend Service

Customize the backend service configuration:

```yaml
# docker-compose.yml
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile.backend
  environment:
    # Health check settings
    - HEALTH_CHECK_INTERVAL=30
    # Logging level
    - LOG_LEVEL=INFO
    # API rate limiting
    - RATE_LIMIT="100/minute"
```

### Predictor Service

Configure the predictor service for your ML model:

```yaml
# docker-compose.yml
predictor:
  build:
    context: ./predictor
    dockerfile: Dockerfile.predictor
  environment:
    # Model path
    - MODEL_PATH=/models/xgb_model.joblib
    # Model refresh interval
    - MODEL_REFRESH_INTERVAL=3600  # 1 hour
```

## Monitoring and Logging

### Prometheus Configuration

The system exposes metrics at `/metrics` endpoint. Configure your Prometheus instance:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'parkwise'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
    metrics_path: /metrics
```

### Logging Configuration

Configure log levels and outputs:

```python
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "parkwise.log")
MAX_LOG_SIZE = os.getenv("MAX_LOG_SIZE", "10MB")
BACKUP_COUNT = os.getenv("BACKUP_COUNT", "5")
```

## Performance Tuning

### Database Performance

- Create indexes for frequently queried columns
- Partition large tables
- Configure connection pooling appropriately

```sql
-- Example indexes
CREATE INDEX idx_slot_status_slot_id ON slot_status(slot_id);
CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_hold_until ON bookings(hold_until);
```

### Redis Configuration

Optimize Redis for your use case:

```yaml
# docker-compose.yml
redis:
  image: redis:7
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  sysctls:
    - net.core.somaxconn=1024
```

### Rate Limiting

Configure rate limits based on your API usage patterns:

```python
# Rate limits for different endpoints
LIMITS = {
    'auth': '10/minute',      # Authentication endpoints
    'edge': '1000/hour',      # Edge device updates
    'booking': '30/minute',   # Booking operations
    'user': '60/minute',      # User operations
}
```

## Production Deployment

### Docker Compose Production Setup

Create a production-specific docker-compose file:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: parkwise
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/parkwise
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    ports:
      - "80:8000"
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  predictor:
    build:
      context: ./predictor
      dockerfile: Dockerfile.predictor
    environment:
      - MODEL_PATH=/models/xgb_model.joblib
    volumes:
      - ./predictor/models:/models
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
```

### Security Hardening

1. **Disable debug mode** in production:
   ```python
   DEBUG = False
   ```

2. **Use SSL certificates**:
   ```yaml
   # Reverse proxy configuration (nginx)
   server {
       listen 443 ssl;
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       
       location / {
           proxy_pass http://backend:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Implement CORS properly**:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Environment-Specific Settings

Create environment-specific configuration files:

```
config/
├── development.py
├── staging.py
├── production.py
└── base.py
```

Example production configuration:

```python
# config/production.py
import os
from .base import *

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

# Security settings
DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Redis configuration
REDIS_URL = os.environ.get('REDIS_URL')

# JWT settings
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)  # Shorter token life in production
```

### Deployment Commands

Deploy the application:

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up --build -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale services
docker-compose -f docker-compose.prod.yml up --scale backend=3
```

This configuration guide provides comprehensive information to set up, customize, and deploy the ParkWise parking management system for various environments while maintaining security and performance best practices.