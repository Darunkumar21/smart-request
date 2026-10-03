# Security Test Report — Panimalar Smart Campus Portal

## Automated checks

The included `security_test.py` was run against this build. **18/18 checks passed.**

- Python syntax compilation: PASS
- PBKDF2-SHA256 salted password hashing: PASS
- No plaintext password storage in the user table: PASS
- Parameterized SQL for user-controlled values: PASS
- Server-side role verification: PASS
- Student identity bound to authenticated official email + master record: PASS
- Student request ownership checks: PASS
- Faculty approver scoping: PASS
- HOD department scoping: PASS
- HOD-only full faculty permission: PASS
- Field-specific student profile permissions: PASS
- Upload size validation: PASS
- PDF/PNG/JPEG signature validation: PASS
- Safe upload filenames: PASS
- Security audit logging: PASS
- Confidential support recipient scoping: PASS
- Duplicate request detection: PASS
- No pandas dependency: PASS

## Important limitation

This is a local Streamlit demonstration and not a guarantee of perfect security. The build was statically/security-reviewed and syntax-checked here; the execution environment used for the build did not have Streamlit installed, so a live browser penetration test was not performed here. Before real college deployment, use institutional SSO/OIDC or SAML with MFA, HTTPS, a production database, centralized rate limiting/session controls, secure secrets management, malware scanning for uploads, encrypted backups, monitoring, dependency scanning, and an independent authorized penetration test.
