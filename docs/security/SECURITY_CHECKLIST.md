# MOBIUS Security Checklist

## Authentication & Authorization

- [x] Passwords hashed with bcrypt (cost factor ≥ 12)
- [x] JWT access tokens short-lived (15 min default)
- [x] Refresh tokens stored hashed in database
- [x] Refresh token rotation on use
- [x] All protected routes require valid JWT
- [ ] Role-based access control (Phase 2+)
- [x] Secure password minimum length (8+ characters)

## Data Protection

- [x] Secrets via environment variables only
- [x] `.env` in `.gitignore`
- [ ] Encryption at rest for sensitive fields (Phase 2)
- [x] No API keys in client-side code
- [x] User data scoped by `user_id` on all queries

## API Security

- [x] Rate limiting on auth endpoints
- [x] Rate limiting on API endpoints
- [x] Input validation via Pydantic schemas
- [x] CORS configured for known origins only
- [x] Security headers (via middleware)
- [x] Audit logging for auth events

## Infrastructure

- [ ] TLS/HTTPS in production (reverse proxy)
- [x] Database credentials not in code
- [x] Docker secrets for production deployment
- [ ] Network isolation between services
- [x] Health endpoint does not expose sensitive data

## AI & Privacy

- [x] User can choose AI provider
- [x] Local LLM support via Ollama (data stays local)
- [x] No conversation data sent to AI without user action
- [ ] Data retention policies configurable (Phase 2)
- [ ] Memory export/delete (GDPR readiness) (Phase 2)

## Development

- [x] Dependency scanning in CI
- [x] No hardcoded credentials in codebase
- [x] Pre-commit secret scanning recommended
- [x] Structured logging without PII in logs

## Voice & Files

- [x] File upload size limits
- [x] MIME type validation on uploads
- [x] Uploaded files stored outside web root

## Incident Response

- [ ] Documented incident response plan (Phase 2)
- [x] Audit logs retained for investigation
- [ ] Token revocation endpoint (Phase 2)

## Pre-Production Review

Before deploying to production:

1. Rotate all default secrets
2. Enable HTTPS with valid certificates
3. Configure firewall rules (only 443/80 public)
4. Set `DEBUG=false`
5. Review CORS allowed origins
6. Enable database backups
7. Configure log aggregation
8. Run security scan (`bandit`, `npm audit`)
9. Penetration test auth flows
10. Document data handling for AI providers
