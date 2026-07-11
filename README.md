# Storage Engine with Write-Ahead Log (WAL) Recovery

A low-overhead, transaction-safe storage engine prototype engineered in Python to demonstrate data durability, atomic appends, and state-machine crash recovery pipelines.

The architecture enforces strict Write-Ahead Logging protocols, ensuring that memory mutations are serialized to disk before updating the volatile data structures to survive unexpected hardware failures.

## Architectural Framework

1. Write-Ahead Ingestion: Prevents data loss during runtime crashes. Incoming state updates are formatted as transactional commands and committed to disk storage using low-overhead append-only strategies before cache exposure.

2. State Machine Materialization: Maintains a volatile key-value registry representing the active memory space. This provides O(1) read operations while decoupling memory caching from persistence layers.

3. Log Replay Pipeline: Implements deterministic boot recovery logic. Upon engine startup, the crash recovery layer parses the ledger chronologically, executing mutations to rebuild the accurate state without external snapshots.


* **What does it do?** *"It is an in-memory key-value database engine featuring a Write-Ahead Log to guarantee absolute data durability across system crashes."*
* **How does the code work simply?** *"When a write occurs, the engine appends the operation command directly to a text file (`wal.log`). Only after that disk write completes does it update the live memory dictionary. If the program crashes, it re-reads the log file line-by-line during boot to rebuild the exact memory dictionary from scratch."*
* **Why is this architecture impressive?** *"It shows an understanding of fundamental database internals. Instead of writing slow, complex parsing infrastructure, it leverages sequential append-only disk I/O—the fastest write method available—and decouples persistence logic from active runtime cache."*


## Deployment and Verification

Execute the storage engine pipeline and recovery simulation:

```bash
python3 wal_engine.py