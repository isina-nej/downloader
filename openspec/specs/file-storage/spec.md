# File Storage Capability

**Capability ID**: `file-storage`  
**Version**: 1.0.0  
**Status**: Active  

## Overview

The File Storage module manages secure, persistent storage of uploaded files with UUID-based
identification, automatic cleanup, and efficient streaming operations. Files are never loaded
entirely into memory and are tracked in a database for ownership and lifecycle management.

## Architecture

```
Incoming File Stream
        ↓
    Validate Size
        ↓
    Generate UUID
        ↓
    Stream to Disk
        ↓
    Save Metadata → Database
        ↓
    Return (UUID, Size)
```

## Requirements

### Requirement: Secure UUID-based Storage
**ID**: REQ-STORAGE-001  
**Priority**: Critical  
**Status**: Implemented  

Files must be stored with UUIDs to prevent brute-force ID guessing attacks.

#### Scenario: Generate unique file ID
```
Given: A new file is uploaded
When: StorageManager processes the file
Then: A UUID v4 is generated
And: UUID is used as filename
And: UUID cannot be guessed or enumerated
And: UUID is returned to bot for link generation
```

#### Scenario: File ID collision prevention
```
Given: Multiple concurrent uploads
When: Each upload gets a UUID
Then: All UUIDs are unique
And: No collisions occur
And: Database unique constraint enforces this
```

### Requirement: Streaming File Storage
**ID**: REQ-STORAGE-002  
**Priority**: Critical  
**Status**: Implemented  

Files must be streamed directly to disk without loading into memory.

#### Scenario: Stream large file to disk
```
Given: A 500MB file is being stored
When: File chunks arrive from network
Then: Each chunk is written immediately to disk
And: No more than 5MB is buffered in memory
And: Total memory usage stays under 100MB
And: Write speed matches network speed
```

#### Scenario: Stream large file on slow connection
```
Given: A 1GB file on slow network (1Mbps)
When: File chunks arrive slowly
Then: Each chunk is written immediately
And: Bot remains responsive
And: Other users can upload simultaneously
```

### Requirement: File Metadata Tracking
**ID**: REQ-STORAGE-003  
**Priority**: High  
**Status**: Implemented  

All stored files must be tracked in database with metadata.

#### Scenario: Track file ownership
```
Given: User uploads a file
When: File is stored
Then: Database records:
  - Generated UUID
  - Original filename
  - File size
  - Telegram user ID (owner)
  - Upload timestamp
  - File path on disk
```

#### Scenario: Track download statistics
```
Given: File is downloaded multiple times
When: Each download occurs
Then: Database updates:
  - last_accessed timestamp
  - download_count incremented
```

### Requirement: Automatic File Cleanup
**ID**: REQ-STORAGE-004  
**Priority**: High  
**Status**: Implemented  

Files older than retention period must be automatically deleted.

#### Scenario: Cleanup expired files
```
Given: Retention period is 30 days
When: cleanup_old_files() is called
Then: All files older than 30 days are identified
And: Files are deleted from disk
And: Database records are removed
And: Disk space is freed
And: Cleanup operation is logged
```

#### Scenario: Selective cleanup on schedule
```
Given: Files with various ages
When: Daily cleanup task runs
Then: Only expired files are deleted
And: Active files are preserved
And: No accidental deletions occur
```

### Requirement: Size Validation
**ID**: REQ-STORAGE-005  
**Priority**: High  
**Status**: Implemented  

Files exceeding size limit must be rejected during upload.

#### Scenario: Reject oversized file
```
Given: Max file size is 2GB
When: File exceeds 2GB during streaming
Then: Stream is stopped immediately
And: Partial file is deleted
And: Database record is not created
And: User is notified of limit
```

### Requirement: Storage Statistics
**ID**: REQ-STORAGE-006  
**Priority**: Medium  
**Status**: Implemented  

System must provide storage statistics for monitoring.

#### Scenario: Get storage info
```
Given: 50 files stored totaling 500GB
When: get_storage_info() is called
Then: Returns:
  - total_files: 50
  - total_size_gb: 500.0
  - available_space_gb: 1000.0
```

## Implementation Details

### Module Location
- **File**: [src/storage.py](../../../src/storage.py)
- **Class**: `StorageManager`
- **Instance**: `storage_manager` (singleton)

### Public Interface

```python
class StorageManager:
    async def save_file_stream(
        telegram_file_id: str,
        filename: str,
        file_stream,
        user_id: int
    ) -> Tuple[str, int]
    
    async def get_file(file_id: str) -> Optional[Tuple[Path, str]]
    
    async def delete_file(file_id: str) -> bool
    
    async def cleanup_old_files() -> int
    
    async def get_storage_info() -> dict
```

### Dependencies
- `aiofiles` (async file I/O)
- `src.database.SessionLocal`
- `src.database.FileRecord`
- `src.config.config`

### Configuration
- `STORAGE_PATH`: Root directory for file storage
- `MAX_FILE_SIZE`: Maximum file size in bytes
- `FILE_RETENTION_DAYS`: Days to keep files

## Performance Characteristics

| Operation | Target | Notes |
|-----------|--------|-------|
| Stream 1GB file | < 60s | Depends on network speed |
| Save metadata | < 100ms | SQLite insert |
| Retrieve file | < 50ms | Disk lookup |
| Cleanup 1000 files | < 5s | Batch operation |
| Get storage info | < 500ms | Query all files |

## Storage Schema

### FileRecord Model
```sql
CREATE TABLE files (
    id TEXT PRIMARY KEY,                    -- UUID
    telegram_file_id TEXT UNIQUE NOT NULL,  -- From Telegram
    original_filename TEXT NOT NULL,        -- User's filename
    file_size INTEGER NOT NULL,             -- Bytes
    file_path TEXT NOT NULL,                -- Disk path
    telegram_user_id INTEGER NOT NULL,      -- Owner
    created_at DATETIME DEFAULT NOW(),      -- Upload time
    last_accessed DATETIME DEFAULT NOW(),   -- Last download
    download_count INTEGER DEFAULT 0        -- Download counter
);
```

## Security Considerations

- UUIDs prevent enumeration/guessing
- File paths are not exposed to users
- Owner tracking enables future access control
- Automatic cleanup prevents unlimited storage growth
- Disk space monitoring prevents exhaustion
- Atomic operations (write or fail, no partial records)

## Error Handling

- Incomplete uploads are deleted automatically
- Database transaction rollback on errors
- File system failures logged with context
- Graceful degradation if cleanup fails
- Partial files never exposed to users

## Monitoring

- Track storage usage trends
- Alert on disk space low
- Monitor cleanup operation duration
- Log file deletion reasons
- Track failed upload reasons

## Deployment Notes

- Ensure write permissions in STORAGE_PATH
- Monitor available disk space regularly
- Schedule cleanup task (daily recommended)
- Backup strategy for stored files
- Sync across replicas if running multiple instances
