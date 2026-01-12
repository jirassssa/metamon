# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email security concerns to: [security@example.com]
3. Include detailed steps to reproduce
4. Allow up to 48 hours for initial response

## Security Measures

### Authentication

- **SIWE (Sign-In with Ethereum)**: Cryptographic signature verification
- **JWT Tokens**: HS256 signed, configurable expiration (default 24h)
- **Nonce Regeneration**: New nonce per login attempt prevents replay attacks

### API Security

- **Rate Limiting**:
  - Nonce endpoint: 30 requests/minute
  - Verify endpoint: 10 requests/minute
  - General API: Default limits apply
- **Input Validation**: All inputs validated via Pydantic schemas
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **CORS**: Configurable allowed origins

### HTTP Security Headers

| Header | Value | Purpose |
|--------|-------|---------|
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| X-XSS-Protection | 1; mode=block | XSS filter |
| Referrer-Policy | strict-origin-when-cross-origin | Control referrer info |
| Strict-Transport-Security | max-age=31536000 (production) | Force HTTPS |

### Data Protection

- No sensitive data logged
- Passwords/secrets never stored in code
- Environment variables for all secrets
- `.env.example` provided without real values

## Production Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET` to a strong, unique value
- [ ] Set `APP_ENV=production`
- [ ] Set `APP_DEBUG=false`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Enable HTTPS
- [ ] Configure firewall rules
- [ ] Set up monitoring (Sentry DSN)
- [ ] Review and rotate API keys regularly
- [ ] Enable database connection encryption
- [ ] Set up log aggregation
- [ ] Configure backup procedures

## Dependency Security

- Run `pip audit` regularly to check for vulnerabilities
- Run `npm audit` for frontend dependencies
- Keep dependencies updated
- Use dependabot or similar for automated updates

## Known Limitations

1. **WebSocket JWT in Query String**: JWT token is passed via query parameter for WebSocket connections. Ensure logs are configured to scrub sensitive query parameters.

2. **Stateless JWT**: Tokens cannot be revoked before expiration. Consider implementing token blacklist with Redis for high-security scenarios.

## Security Updates

Security patches are applied as soon as possible after discovery. Subscribe to repository notifications for security advisories.
