import os
import json
import struct
import zlib
import tempfile
import sys
from typing import Any, Optional, Dict

# Cross-platform file locking
if sys.platform == "win32":
    import msvcrt

    def _lock_file(fd):
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)

    def _unlock_file(fd):
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
else:
    import fcntl

    def _lock_file(fd):
        fcntl.flock(fd, fcntl.LOCK_EX)

    def _unlock_file(fd):
        fcntl.flock(fd, fcntl.LOCK_UN)


class WALStorageEngine:
    """Write-Ahead Log key-value storage engine with crash recovery."""

    MAGIC = b"WAL1"
    RECORD_HEADER_SIZE = 12

    def __init__(self, log_path="wal.log", auto_compact=False, compact_threshold=1000):
        self.log_path = log_path
        self.state = {}
        self._lock_file = log_path + ".lock"
        self._lock_fd = None
        self.auto_compact = auto_compact
        self.compact_threshold = compact_threshold
        self._write_count = 0
        self._acquire_lock()
        self.recover_state()

    def _acquire_lock(self):
        self._lock_fd = os.open(self._lock_file, os.O_RDWR | os.O_CREAT, 0o644)
        _lock_file(self._lock_fd)

    def _release_lock(self):
        if self._lock_fd is not None:
            _unlock_file(self._lock_fd)
            os.close(self._lock_fd)
            self._lock_fd = None

    def close(self):
        self._release_lock()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @staticmethod
    def _encode_record(op, key, value=None):
        payload = json.dumps({"op": op, "key": key, "value": value},
                             separators=(",", ":")).encode("utf-8")
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        header = WALStorageEngine.MAGIC + struct.pack("<II", len(payload), crc)
        return header + payload

    @staticmethod
    def _decode_record(data):
        if len(data) < WALStorageEngine.RECORD_HEADER_SIZE:
            return None
        if data[:4] != WALStorageEngine.MAGIC:
            return None
        payload_len, crc = struct.unpack("<II", data[4:12])
        payload = data[12:12 + payload_len]
        if len(payload) != payload_len:
            return None
        if (zlib.crc32(payload) & 0xFFFFFFFF) != crc:
            return None
        try:
            return json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def set(self, key, value):
        record = self._encode_record("SET", key, value)
        self._append(record)
        self.state[key] = value
        self._write_count += 1
        self._maybe_compact()
        print(f"[STORED] Key: '{key}' -> Value: {value!r}")

    def get(self, key, default=None):
        return self.state.get(key, default)

    def delete(self, key):
        if key not in self.state:
            return False
        record = self._encode_record("DEL", key)
        self._append(record)
        del self.state[key]
        self._write_count += 1
        self._maybe_compact()
        print(f"[DELETED] Key: '{key}'")
        return True

    def exists(self, key):
        return key in self.state

    def keys(self):
        return list(self.state.keys())

    def items(self):
        return iter(self.state.items())

    def __len__(self):
        return len(self.state)

    def __contains__(self, key):
        return key in self.state

    def __getitem__(self, key):
        if key not in self.state:
            raise KeyError(key)
        return self.state[key]

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        if not self.delete(key):
            raise KeyError(key)

    def _append(self, record):
        with open(self.log_path, "ab") as log:
            log.write(record)
            log.flush()
            os.fsync(log.fileno())

    def sync(self):
        if os.path.exists(self.log_path):
            fd = os.open(self.log_path, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)

    def recover_state(self):
        if not os.path.exists(self.log_path):
            print("[INIT] No existing WAL found. Fresh database state initialized.")
            return

        print("[RECOVERY] System crash/restart detected! Replaying log ledger...")
        print("-" * 65)

        with open(self.log_path, "rb") as log:
            raw = log.read()

        offset = 0
        recovered = 0
        corrupted = 0
        truncated = 0
        while offset < len(raw):
            if offset + self.RECORD_HEADER_SIZE > len(raw):
                truncated += 1
                break
            rec = self._decode_record(raw[offset:])
            if rec is None:
                next_magic = raw.find(self.MAGIC, offset + 1)
                if next_magic == -1:
                    truncated += 1
                    break
                corrupted += 1
                offset = next_magic
                continue

            payload_len = struct.unpack("<I", raw[offset + 4:offset + 8])[0]
            record_size = self.RECORD_HEADER_SIZE + payload_len

            if rec["op"] == "SET":
                self.state[rec["key"]] = rec["value"]
            elif rec["op"] == "DEL":
                self.state.pop(rec["key"], None)

            recovered += 1
            offset += record_size

        print("-" * 65)
        if corrupted:
            print(f"[WARNING] Skipped {corrupted} corrupted record(s).")
        if truncated:
            print(f"[WARNING] Truncated trailing data detected and ignored.")
        print(f"[RECOVERY COMPLETE] Replayed {recovered} transaction(s). "
              f"State has {len(self.state)} key(s).")

    def begin_transaction(self):
        return Transaction(self)

    def compact(self):
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(self.log_path) or ".")
        try:
            with os.fdopen(tmp_fd, "wb") as tmp:
                for key, value in self.state.items():
                    record = self._encode_record("SET", key, value)
                    tmp.write(record)
                tmp.flush()
                os.fsync(tmp.fileno())
            if os.path.exists(self.log_path):
                os.remove(self.log_path)
            os.rename(tmp_path, self.log_path)
            self._write_count = 0
            print(f"[COMPACT] Log compacted. {len(self.state)} key(s) retained.")
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise RuntimeError(f"Compaction failed: {e}")

    def _maybe_compact(self):
        if self.auto_compact and self._write_count >= self.compact_threshold:
            self.compact()

    def clear(self):
        self.state.clear()
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
        self._write_count = 0
        print("[CLEAR] All data cleared.")

    def stats(self):
        log_size = os.path.getsize(self.log_path) if os.path.exists(self.log_path) else 0
        return {
            "keys": len(self.state),
            "log_size_bytes": log_size,
            "write_count": self._write_count,
            "log_path": self.log_path,
        }

    def dump(self):
        return json.dumps(self.state, indent=2, default=str)

class Transaction:
    def __init__(self, engine):
        self._engine = engine
        self._pending = []
        self._committed = False

    def set(self, key, value):
        self._pending.append(("SET", key, value))
        return self

    def delete(self, key):
        self._pending.append(("DEL", key))
        return self

    def commit(self):
        if self._committed:
            raise RuntimeError("Transaction already committed.")
        for op, key, *rest in self._pending:
            if op == "SET":
                record = self._engine._encode_record("SET", key, rest[0])
            else:
                record = self._engine._encode_record("DEL", key)
            self._engine._append(record)
        for op, key, *rest in self._pending:
            if op == "SET":
                self._engine.state[key] = rest[0]
            else:
                self._engine.state.pop(key, None)
        self._engine._write_count += len(self._pending)
        self._committed = True
        print(f"[TXN] Committed {len(self._pending)} operation(s).")

    def rollback(self):
        self._pending.clear()
        print("[TXN] Rolled back.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *args):
        if exc_type is None and not self._committed:
            self.commit()
        elif exc_type is not None:
            self.rollback()


if __name__ == "__main__":
    for f in ["wal.log", "wal.log.lock"]:
        if os.path.exists(f):
            os.remove(f)

    print("=" * 70)
    print("WAL Key-Value Storage Engine - Demo")
    print("=" * 70)

    print("\n--- Basic Operations ---")
    db = WALStorageEngine("wal.log")
    db.set("user_1", "Kshitij")
    db.set("role", "Engineer")
    db.set("config", {"theme": "dark", "lang": "en"})
    db.set("scores", [95, 87, 92])
    print(f"\nget('user_1') = {db.get('user_1')!r}")
    print(f"get('missing') = {db.get('missing', 'N/A')!r}")
    print(f"len(db) = {len(db)}")
    print(f"'role' in db = {'role' in db}")

    print("\n--- Delete ---")
    db.delete("role")
    print(f"'role' in db = {'role' in db}")

    print("\n--- Transaction ---")
    with db.begin_transaction() as txn:
        txn.set("a", 1).set("b", 2).set("c", 3)
    print(f"State after txn: {db.state}")

    print("\n--- Crash & Recovery ---")
    print(f"Active Memory State before crash: {db.state}\n")
    db.close()

    print("Restarting database engine instance...")
    recovered_db = WALStorageEngine("wal.log")
    print(f"Verified Recovered Memory State: {recovered_db.state}")

    print("\n--- Compaction ---")
    recovered_db.compact()
    print(f"Stats: {recovered_db.stats()}")

    print("\n--- Partial Write Recovery ---")
    recovered_db.close()
    with open("wal.log", "ab") as f:
        f.write(b"WAL1\x05\x00\x00\x00")
    recovered_db2 = WALStorageEngine("wal.log")
    print(f"State after partial-write recovery: {recovered_db2.state}")
    recovered_db2.close()

    for f in ["wal.log", "wal.log.lock"]:
        if os.path.exists(f):
            os.remove(f)
    print("\n[DEMO COMPLETE]")