.PHONY: help dev up down logs test-backend test-frontend test-e2e clean

# Default target
help:
	@echo "Shadow Copy-Trader Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start all services in development mode"
	@echo "  make up           - Start all services with Docker Compose"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - View logs from all services"
	@echo ""
	@echo "Testing:"
	@echo "  make test-backend - Run backend tests"
	@echo "  make test-frontend - Run frontend type checking"
	@echo "  make test-e2e     - Run end-to-end tests"
	@echo "  make test-all     - Run all tests"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make db-seed      - Seed the database with sample data"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove all containers and volumes"

# Development
dev:
	docker compose up -d db redis
	@echo "Waiting for database to be ready..."
	@sleep 5
	@echo "Starting backend..."
	cd backend && uvicorn app.main:app --reload --port 8000 &
	@echo "Starting frontend..."
	cd frontend && npm run dev

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

# Testing
test-backend:
	cd backend && pytest -v --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && npm run type-check && npm run lint

test-e2e:
	cd frontend && npm run test:e2e

test-all: test-backend test-frontend
	@echo "All tests completed!"

# Database
db-migrate:
	cd backend && alembic upgrade head

db-seed:
	cd backend && python -m app.scripts.seed_data

# Cleanup
clean:
	docker compose down -v --remove-orphans
	rm -rf backend/__pycache__ backend/.pytest_cache
	rm -rf frontend/.next frontend/node_modules/.cache
