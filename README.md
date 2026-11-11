# WAL-Key-Value-Storage-Engine

Python demo of append-first writes and in-memory state recovery by replaying a simple log.

## Overview
This project demonstrates append-first write patterns and in-memory state recovery using a simple log-based approach.

## Features
- Append-first write strategy
- In-memory state recovery via log replay
- Lightweight key-value storage engine
- Write-ahead logging (WAL) pattern

## Usage
```python
from wal_key_value import KVStore
store = KVStore()
store.put('key', 'value')
value = store.get('key')
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Topics
- database
- key-value-store
- persistence
- storage-engine
- write-ahead-log
```