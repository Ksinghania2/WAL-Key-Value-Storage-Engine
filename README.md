# WAL Key-Value Storage Engine

A small Python project that demonstrates an append-first write path and rebuilding an in-memory key-value dictionary by replaying a log file.

## What it demonstrates

- `WALStorageEngine.set()` appends a `SET:key:value` record to `wal.log` before updating the in-memory dictionary.
- Starting a new engine instance reads the log and replays the stored `SET` records.
- The script includes a simple restart/recovery demonstration.

## Run

```bash
python wal_engine.py
```

The script creates `wal.log` in the current working directory.

## Scope and limitations

This is a learning prototype, not a production database. The log format uses colon-separated fields and does not escape colons or newlines in keys and values. It does not implement transactions, deletes, concurrent writers, checksums, log compaction, or explicit `fsync`; an append call alone does not guarantee survival of power loss or every operating-system failure.
