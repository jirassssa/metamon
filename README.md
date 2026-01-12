# Shadow Copy-Trader

A Polymarket copy-trading platform that allows users to automatically copy the trades of successful traders.

## Features

- **SIWE Authentication**: Sign-In with Ethereum for secure wallet-based authentication
- **Copy Trading**: Automatically copy trades from top Polymarket traders
- **Real-time Updates**: WebSocket-based position updates
- **Risk Management**: Stop-loss, take-profit, and position sizing controls
- **Trader Leaderboard**: Browse and analyze top-performing traders
- **Portfolio Management**: Track your copy-trading performance

## Tech Stack

### Backend
- **FastAPI** - High-performance async API framework
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **Celery** - Background task processing
- **Redis** - Caching and task queue
- **Pydantic** - Data validation

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - UI component library
- **wagmi/viem** - Ethereum wallet integration
- **TanStack Query** - Server state management
- **Zustand** - Client state management

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/shadow-copy-trader.git
cd shadow-copy-trader

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Configure your environment variables (especially JWT_SECRET)

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Seed sample data (optional)
python -m app.scripts.seed_data

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your settings

# Start development server
npm run dev
```

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/shadow_trader

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT (IMPORTANT: Change in production!)
JWT_SECRET=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Polymarket API
POLYMARKET_API_KEY=your-api-key
POLYMARKET_API_SECRET=your-api-secret
POLYMARKET_API_PASSPHRASE=your-passphrase

# Application
APP_ENV=development  # or 'production'
APP_DEBUG=true       # false in production
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your-project-id
```

## API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/nonce` | Get authentication nonce |
| POST | `/api/auth/verify` | Verify SIWE signature |
| GET | `/api/traders` | List top traders |
| GET | `/api/traders/{address}` | Get trader details |
| GET | `/api/copies` | List user's copy configs |
| POST | `/api/copies` | Create new copy config |
| GET | `/api/portfolio` | Get portfolio summary |
| WS | `/api/ws/positions` | Real-time position updates |

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=app --cov-report=term-missing
```

### Frontend Tests

```bash
cd frontend

# Type check
npm run type-check

# Lint
npm run lint

# E2E tests
npm run test:e2e
```

### Integration Tests

```bash
# Using Docker Compose
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Using Makefile
make test-all
```

## Security

- **Authentication**: SIWE (Sign-In with Ethereum) with JWT tokens
- **Rate Limiting**: API rate limiting with slowapi
- **Security Headers**: HSTS, X-Frame-Options, X-Content-Type-Options
- **Input Validation**: Pydantic schemas for all inputs
- **SQL Injection Prevention**: SQLAlchemy ORM
- **CORS**: Configurable allowed origins

### Security Best Practices

1. Always change `JWT_SECRET` in production
2. Set `APP_DEBUG=false` in production
3. Configure proper CORS origins
4. Use HTTPS in production
5. Keep dependencies updated

## Architecture

```
shadow-copy-trader/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routers/          # API routes
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── middleware/       # Custom middleware
│   ├── tests/                # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── lib/              # Utilities
│   │   └── stores/           # Zustand stores
│   ├── e2e/                  # E2E tests
│   └── package.json
├── docker-compose.yml        # Docker setup
└── Makefile                  # Development commands
```

## Copy Trading Logic

Position sizing formula:
```
position_size = allocation * (trade_size / trader_portfolio_value) * (copy_ratio / 100)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For questions or issues, please open a GitHub issue.
