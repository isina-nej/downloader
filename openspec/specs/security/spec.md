# Security Capability

**Capability ID**: `security`  
**Version**: 1.0.0  
**Status**: Active  

## Overview

The Security capability encompasses token management, rate limiting, input validation, and
access control mechanisms to protect the system against common attacks and abuse patterns.

## Architecture

```
Incoming Request
        ↓
    ├─→ Token Validation (.env)
    ├─→ Rate Limit Check
    ├─→ Input Validation
    ├─→ Size Limit Check
    ├─→ UUID Format Validation
    └─→ Logging/Audit
        ↓
    Either: Process Request
    Or: Reject with Error
```

## Requirements

### Requirement: Token Security
**ID**: REQ-SEC-001  
**Priority**: Critical  
**Status**: Implemented  

Bot token must be kept secret and never exposed.

#### Scenario: Load token securely
```
Given: TELEGRAM_BOT_TOKEN is in .env file
When: Application starts
Then: Token is loaded from .env
And: Token is never logged
And: Token is never displayed in error messages
And: Token is never committed to version control
```

#### Scenario: Prevent hardcoded tokens
```
Given: Development or production
When: Code review occurs
Then: Hardcoded tokens are rejected
And: .env usage is required
And: .gitignore protects .env
```

### Requirement: Rate Limiting
**ID**: REQ-SEC-002  
**Priority**: High  
**Status**: Implemented  

Per-user rate limiting prevents abuse and DoS attacks.

#### Scenario: Enforce per-user limits
```
Given: Rate limit is 10 files/minute
When: User uploads 11 files in 60 seconds
Then: 11th upload is rejected
And: User receives rate limit message
And: Request is logged
And: User must wait before next upload
```

#### Scenario: Rate limit across sessions
```
Given: User has multiple Telegram clients
When: Uploading from multiple clients
Then: Rate limit applies to user ID (not session)
And: Attempts from all clients count toward limit
```

#### Scenario: Reset rate limit after window
```
Given: Rate limit window is 60 seconds
When: First upload is at 0s, 10th at 59s
Then: User hits limit at 10 uploads
And: At 60.1s, limit resets
And: 11th upload at 60.1s is allowed
```

### Requirement: Input Validation
**ID**: REQ-SEC-003  
**Priority**: High  
**Status**: Implemented  

All user inputs must be validated for security and correctness.

#### Scenario: Validate file size
```
Given: Max file size is 2GB
When: User uploads file
Then: Size is checked before streaming
And: Oversized files are rejected immediately
And: User receives clear error message
```

#### Scenario: Validate UUID format
```
Given: File ID must be UUID format
When: GET /download/{file_id} is called
Then: UUID format is validated
And: Invalid formats are rejected with 400 error
And: Malicious patterns are blocked
```

#### Scenario: Prevent path traversal
```
Given: File ID is UUID-based
When: User requests download
Then: File ID is validated as UUID
And: No path traversal sequences (../, etc) are possible
And: File path cannot escape storage directory
```

### Requirement: UUID-based File IDs
**ID**: REQ-SEC-004  
**Priority**: Critical  
**Status**: Implemented  

File IDs must use UUID v4 to prevent ID guessing/enumeration.

#### Scenario: Generate non-guessable IDs
```
Given: New file is uploaded
When: File ID is generated
Then: UUID v4 is used
And: IDs are cryptographically random
And: Probability of guessing ID is negligible
And: Sequential or predictable patterns are impossible
```

#### Scenario: Prevent ID enumeration
```
Given: Attacker has one valid UUID
When: Attacker tries sequential UUIDs
Then: Random distribution makes enumeration impossible
And: 2^122 possible IDs (UUID v4)
And: Brute force would take centuries
```

### Requirement: Error Message Security
**ID**: REQ-SEC-005  
**Priority**: High  
**Status**: Implemented  

Error messages must not leak sensitive information.

#### Scenario: Generic error messages
```
Given: File storage fails
When: User requests download
Then: User sees: "File not found or expired"
And: Server logs detailed error
And: Stack trace is not shown to user
And: Sensitive details are hidden
```

#### Scenario: Audit logging
```
Given: Security event occurs
When: Error is handled
Then: Detailed error is logged server-side
And: User ID is recorded
And: Timestamp is recorded
And: Error type is categorized
```

### Requirement: File Ownership Tracking
**ID**: REQ-SEC-006  
**Priority**: Medium  
**Status**: Implemented  

All files are tracked with owner information for future access control.

#### Scenario: Track file owner
```
Given: User uploads a file
When: File is stored
Then: Telegram user ID is recorded
And: Database stores user_id with file
And: Owner can be verified if needed
```

#### Scenario: Enable future access control
```
Given: File ownership is tracked
When: Future requirements change
Then: Access control can be implemented
And: Only owner can delete files
And: Sharing can be permission-based
```

## Implementation Details

### Token Management

**Location**: [src/config.py](../../../src/config.py)

```python
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Never log or print this value
```

**Best Practices**:
- Store in .env file only
- Add .env to .gitignore
- Use .env.example for template
- Rotate token if compromised
- Audit token access logs

### Rate Limiter

**Location**: [src/rate_limiter.py](../../../src/rate_limiter.py)

```python
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60)
    async def is_allowed(self, key: str) -> bool
    def get_remaining(self, key: str) -> int
```

**Algorithm**: Sliding window counter
- Tracks request timestamps per user
- Cleans up expired timestamps
- O(1) average case, O(n) worst case

### Input Validation

**UUID Validation**:
```python
def _is_valid_uuid(value: str) -> bool:
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return uuid_pattern.match(value) is not None
```

**Size Validation**:
```python
if file_size > config.MAX_FILE_SIZE:
    raise ValueError("File size exceeds maximum limit")
```

## Threat Models

### Threat: Token Exposure
**Severity**: Critical  
**Mitigation**: 
- Stored in .env file
- Never logged
- .gitignore protection
- Consider token rotation mechanism

### Threat: DoS via Rate Limiting
**Severity**: High  
**Mitigation**: 
- Per-user rate limiting (10 req/min)
- IP-based rate limiting (optional future)
- Progressive backoff
- Resource monitoring

### Threat: ID Enumeration
**Severity**: High  
**Mitigation**: 
- UUID v4 with 2^122 possibilities
- No sequential or predictable patterns
- Brute force resistance measured in centuries

### Threat: Path Traversal
**Severity**: High  
**Mitigation**: 
- UUID-only file IDs
- Database lookup for path
- No user-controlled path construction

### Threat: Storage Exhaustion
**Severity**: Medium  
**Mitigation**: 
- File size limit (2GB per file)
- Automatic TTL-based cleanup
- Disk space monitoring
- Per-user quotas (future)

### Threat: Unauthorized Access
**Severity**: Medium  
**Mitigation**: 
- URL-based access (UUID)
- Owner tracking for future ACLs
- No authentication required (trade-off)
- Consideration: Add password-protected links (future)

## Compliance & Standards

- **OWASP Top 10**: Addresses injection, auth, sensitive data, etc.
- **Rate Limit Header**: X-RateLimit-Remaining
- **Security Headers**: Consider adding (future)
- **HTTPS**: Required in production
- **Data Retention**: Implement based on jurisdiction

## Monitoring & Alerts

### Security Metrics
- Failed authentication attempts (future)
- Rate limit violations (track by user)
- Large file attempts (track by size)
- Unusual error patterns
- Token exposure detection

### Alerting Thresholds
- 100+ rate limit violations in 1 hour: Alert
- File size > 1GB: Log and monitor
- Error rate > 5%: Alert
- Unusual error patterns: Alert

## Testing

### Security Testing
- Token leak detection in logs
- Rate limit boundary testing
- UUID format validation tests
- Path traversal attempt tests
- Error message review tests
- Concurrent rate limit tests

### Penetration Testing Considerations
- Manual token leak attempts
- Brute force ID guessing (time analysis)
- Rate limit bypass techniques
- Path traversal payloads
- Error message information leakage

## Future Enhancements

1. **API Key Authentication**: For programmatic access
2. **Password-Protected Links**: Add password to download links
3. **Time-Limited URLs**: Add expiration to download links
4. **Per-User Quotas**: Limit total storage per user
5. **IP-Based Rate Limiting**: Additional layer
6. **Encryption at Rest**: Encrypt stored files
7. **Audit Log Retention**: Extend audit logging
8. **Two-Factor Authentication**: For admin functions
