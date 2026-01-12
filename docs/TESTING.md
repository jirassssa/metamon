# Testing Guide

This document describes how to run tests for the Shadow Copy-Trader platform.

## Backend Tests

### Unit Tests

Run backend unit tests:

```bash
cd backend
pytest -v
```

Run with coverage:

```bash
pytest -v --cov=app --cov-report=term-missing
```

### Integration Tests

Run integration tests (requires database):

```bash
# Start test database
docker compose -f docker-compose.test.yml up -d test-db test-redis

# Run tests
cd backend
DATABASE_URL=postgresql+asyncpg://test:test_password@localhost:5433/test_shadow_copy_trader \
pytest -v tests/test_*_integration.py
```

## Frontend Tests

### Type Checking

```bash
cd frontend
npm run type-check
```

### Linting

```bash
cd frontend
npm run lint
```

### E2E Tests

Run E2E tests locally:

```bash
cd frontend
npm run test:e2e
```

Run E2E tests with UI:

```bash
npm run test:e2e:ui
```

Run E2E tests in debug mode:

```bash
npm run test:e2e:debug
```

## Full Integration Testing

### Using Docker Compose

Run the complete test suite with Docker:

```bash
# Run all tests
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Clean up
docker compose -f docker-compose.test.yml down -v
```

### Using Makefile

```bash
# Run all tests
make test-all

# Run only backend tests
make test-backend

# Run only frontend tests
make test-frontend

# Run E2E tests
make test-e2e
```

## Test Coverage

Target coverage: 80%+

Current coverage areas:
- Authentication flow (SIWE + JWT)
- Copy trading CRUD operations
- Position management
- Stop-loss/take-profit triggers
- WebSocket connections
- API endpoints

## Writing Tests

### Backend Test Guidelines

1. Use pytest fixtures for database sessions and test data
2. Mock external API calls (Polymarket)
3. Test both success and error cases
4. Use async tests for database operations

Example:

```python
@pytest.mark.asyncio
async def test_create_copy(test_db, test_user, test_trader):
    """Test creating a new copy configuration."""
    copy_data = {
        "trader_address": test_trader.wallet_address,
        "allocation": "1000.00",
    }
    # ... test implementation
```

### Frontend Test Guidelines

1. Use Playwright for E2E tests
2. Test critical user flows
3. Test responsive design
4. Mock wallet connections when needed

Example:

```typescript
test("displays trader leaderboard", async ({ page }) => {
  await page.goto("/leaderboard");
  await expect(page.getByRole("heading", { name: /Top Traders/i })).toBeVisible();
});
```

## CI/CD Integration

Tests are automatically run on:
- Pull requests
- Pushes to main branch

GitHub Actions workflow:
1. Lint and type check
2. Run backend unit tests
3. Run frontend E2E tests
4. Build Docker images
5. Deploy to staging (on main)
