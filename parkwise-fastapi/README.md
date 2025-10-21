# ParkWise - Smart Parking Management System

ParkWise is a real-time parking management system that provides intelligent parking slot monitoring, reservation, and predictive analytics to optimize parking availability in urban areas.

## Features

- Real-time parking slot occupancy monitoring via camera detection
- Instant slot reservation with distributed locking
- Predictive analytics for slot availability
- JWT-based user authentication and authorization
- Comprehensive monitoring and metrics
- Scalable microservices architecture

## Architecture

The system consists of multiple services:
- **Backend API**: FastAPI application handling business logic
- **Predictor Service**: ML-based prediction engine
- **PostgreSQL**: Persistent data storage
- **Redis**: Caching and job queues
- **Frontend UI** (Coming Soon): React-based dashboard

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js (for future frontend)

## Installation & Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd parkwise-fastapi
```

### 2. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific configuration:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/parkwise

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Services
PREDICTOR_URL=http://predictor:8080
HOST=0.0.0.0
PORT=8000
```

### 3. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

### 4. Initialize Database

Run database initialization script:

```bash
# Enter the backend container
docker-compose exec backend bash

# Run initialization
python -m app.scripts.init_db
python -m app.scripts.seed_slots
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token

### Parking Management
- `POST /cv/process-image` - Process parking lot image and detect occupancy
- `POST /cv/detect-occupancy` - Detect parking spot occupancy using webcam
- `POST /cv/update-slot-from-camera` - Update slot status from camera image
- `POST /cv/process-live-camera-feed` - Process live camera feed for occupancy detection
- `POST /cv/calibrate-slot` - Calibrate a parking slot by defining its position in an image
- `GET /cv/calibrated-slots` - Get all calibrated parking slots with their positions
- `GET /cv/slots-with-status` - Get all parking slots with their status and calibration data
- `DELETE /cv/calibrate-slot/{slot_id}` - Remove calibration for a parking slot
- `POST /v1/bookings/hold` - Reserve a parking slot
- `GET /v1/predictions/{slot_id}` - Get availability prediction

### Admin Dashboard
- `GET /admin/users` - Get all users (admin only)
- `GET /admin/stats` - Get system statistics (admin only)
- `GET /admin/slots` - Get all slots with analytics (admin only)

## Development

### Running Unit Tests

```bash
# Run backend tests
docker-compose exec backend python -m pytest tests/ -v
```

### Running with Hot Reload

For development with hot reload, modify the Docker configuration:

```bash
# In docker-compose.yml, change the backend CMD to:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Adding a New Model

1. Add the new SQLAlchemy model in `app/models.py`
2. Create corresponding Pydantic schema in `app/schemas.py`
3. Create routes in a new file under `app/routes/`
4. Import and include the router in `app/main.py`

## Configuration Guide

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `JWT_SECRET_KEY` | Secret for JWT signing | - |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | 7 |
| `PREDICTOR_URL` | URL for prediction service | http://predictor:8080 |

### Customizing Prediction Model

To use your own trained model:

1. Train your model and save as `xgb_model.joblib`
2. Place it in `predictor/models/`
3. Update the `MODEL_PATH` environment variable

## Security Best Practices

1. **JWT Secrets**: Use strong, randomly generated JWT secret keys
2. **HTTPS**: Always run the API behind HTTPS in production
3. **Rate Limiting**: The system includes rate limiting to prevent abuse
4. **Input Validation**: All endpoints have strict input validation
5. **Camera Access**: Secure camera feed endpoints with proper authentication

## Monitoring and Logging

The system includes:

- Structured logging with different log levels
- Prometheus metrics endpoint at `/metrics`
- Health check endpoint at `/health`
- Request tracing for debugging

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Ensure PostgreSQL is running and accessible
   - Check `DATABASE_URL` configuration

2. **Redis Connection Issues**
   - Ensure Redis is running and accessible
   - Check `REDIS_URL` configuration

3. **Prediction Service Unavailable**
   - Check that predictor service is running
   - Verify model file exists if using custom model

### Useful Commands

```bash
# View service logs
docker-compose logs backend
docker-compose logs predictor
docker-compose logs postgres
docker-compose logs redis

# Scale services
docker-compose up --scale backend=2

# Stop all services
docker-compose down
```

## Contributing

We welcome contributions to ParkWise! Please read our contributing guidelines for details on our code of conduct and the process for submitting pull requests.

## Deployment

For production deployment:

1. Use a production-grade PostgreSQL setup
2. Secure all API keys and secrets
3. Implement proper SSL certificates
4. Set up monitoring and alerting
5. Configure proper logging aggregation

## License

This project is licensed under the MIT License - see the LICENSE file for details.