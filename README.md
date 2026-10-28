# WAL Key-Value Storage Engine

A Python project that demonstrates an append-first write path and rebuilding an in-memory key-value dictionary by replaying a log file.

## What it demonstrates

- `WALStorageEngine.set()` appends a binary record (with CRC32 checksum) to `wal.log` before updating the in-memory dictionary.
- Starting a new engine instance reads the log and replays the stored records.
- The script includes a restart/recovery demonstration.

## Improvements over the original

- **Binary record format** with magic bytes, length prefix, and CRC32 checksums for corruption detection.
- **Partial-write recovery**: truncated trailing records are detected and ignored.
- **Delete operations** (`delete`, `__delitem__`).
- **Type-preserving storage**: JSON serialization supports dicts, lists, ints, floats, booleans, and None.
- **File locking** (cross-platform: fcntl on Unix, msvcrt on Windows) for concurrent access.
- **fsync** after every write for durability.
- **Log compaction** to reclaim space from deleted/overwritten keys.
- **Transactions** for atomic batch writes (commit/rollback).
- **Context manager** support (`with WALStorageEngine(...) as db:`).
- **Rich API**: `get`, `set`, `delete`, `exists`, `keys`, `items`, `stats`, `dump`, `clear`, `compact`, `sync`.
- **Auto-compaction** with configurable threshold.
- **Corruption handling**: skips corrupted records and continues recovery.

## Run

```bash
python wal_engine.py
```

The script creates `wal.log` in the current working directory.

## API example

```python
from wal_engine import WALStorageEngine

with WALStorageEngine("my.db") as db:
    db.set("user", "Alice")
    db.set("config", {"theme": "dark"})
    print(db.get("user"))          # Alice
    print(db["config"])            # {'theme': 'dark'}
    del db["user"]
    print("user" in db)            # False

    with db.begin_transaction() as txn:
        txn.set("a", 1).set("b", 2)

    db.compact()
    print(db.stats())
```

## Scope and limitations

This is a learning prototype, not a production database. It does not implement multi-version concurrency control, replication, or a query planner. Concurrent writers are serialized via file locking but readers may see stale data.
