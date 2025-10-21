# Firebase Studio - Full Stack Parking Management System

This is a NextJS frontend in Firebase Studio with advanced parking management features, AI insights, and real-time monitoring. This project integrates with a FastAPI backend for comprehensive parking management.

## Features

- Real-time parking slot tracking
- AI-powered predictions and insights
- Analytics dashboard with usage trends
- Performance monitoring
- Mobile-responsive design
- Comprehensive testing suite
- Full backend API with PostgreSQL, Redis, and ML predictions

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Docker and Docker Compose
- Python 3.11+ (for backend development)

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd firebase frontend
```

2. Install frontend dependencies
```bash
cd studio-main
npm install
```

3. Create a `.env.local` file with your Firebase configuration (for authentication):
```env
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Running the Full Stack Application

### Option 1: Using Docker Compose (Recommended)

From the project root directory (`firebase frontend`), run:

```bash
docker-compose up --build
```

This will start:
- PostgreSQL database
- Redis cache
- FastAPI backend
- ML prediction service
- Next.js frontend

The frontend will be available at [http://localhost:3000](http://localhost:3000) and the backend API at [http://localhost:8000](http://localhost:8000).

### Option 2: Running Services Separately

1. Start the backend services:
```bash
cd backend/parkwise-fastapi
docker-compose up --build
```

2. In a separate terminal, start the frontend:
```bash
cd studio-main
npm run dev
```

The frontend will be available at [http://localhost:9002](http://localhost:9002).

3. Initialize the parking slots in the backend:
```bash
# After the backend services are running
docker-compose exec backend python -m app.scripts.seed_slots
```

## Development

Available frontend scripts:
- `npm run dev` - Start frontend development server
- `npm run build` - Build frontend for production
- `npm start` - Start frontend production server
- `npm run lint` - Run linter
- `npm run typecheck` - Run type checking
- `npm test` - Run tests
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage

## Backend API Endpoints

- Authentication: `/auth/register`, `/auth/login`
- Parking Management: `/v1/edge/slots`, `/v1/bookings/hold`
- Predictions: `/v1/predictions/{slot_id}`
- Health check: `/health`

## Project Structure

```
firebase frontend/           # Project root
├── backend/                 # Backend services (FastAPI)
│   └── parkwise-fastapi/    # ParkWise main backend
├── studio-main/             # Frontend application
│   ├── src/
│   │   ├── app/            # Next.js app router pages
│   │   ├── components/     # Reusable UI components
│   │   ├── context/        # React contexts (AuthContext)
│   │   ├── lib/            # Utilities and API functions
│   │   └── types/          # TypeScript type definitions
│   ├── public/
│   └── ...                 # Configuration files
```

## Testing

The project includes a comprehensive testing setup with Vitest and React Testing Library:
- Unit tests for components
- Integration tests for API functions
- Snapshot testing

Run tests with:
```bash
npm run test
```

## Deployment

### Docker Deployment

Build and run the full stack with Docker Compose:
```bash
# From the project root directory
docker-compose up --build -d
```

### Individual Service Deployment

Frontend:
```bash
cd studio-main
docker build -t firebase-studio .
docker run -p 3000:3000 firebase-studio
```

Backend:
```bash
cd backend/parkwise-fastapi
docker-compose up --build -d
```

## Environment Variables

- `NEXT_PUBLIC_FIREBASE_*` - Firebase configuration for authentication
- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL (default: http://localhost:8000)

Create a `.env.local` file based on the `.env.example` template to configure these values.

## Project Maintenance

This project includes:
- Security policies in `SECURITY.md`
- Contribution guidelines in `CONTRIBUTING.md`
- Automated dependency updates via `.github/dependabot.yml`
- CI/CD workflow in `.github/workflows/ci.yml`
- Node.js version specified in `.nvmrc`
