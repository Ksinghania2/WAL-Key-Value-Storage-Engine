import os

class WALStorageEngine:
    def __init__(self, log_path="wal.log"):
        self.log_path = log_path
        self.state = {}  # Volatile In-Memory Database State
        self.recover_state()

    def set(self, key, value):
        """Writes to disk ledger first (WAL rule), then updates memory state."""
        # 1. Commit mutation transaction to the Append-Only Log
        with open(self.log_path, "a") as log:
            log.write(f"SET:{key}:{value}\n")
        
        # 2. Update the live volatile state cache
        self.state[key] = value
        print(f"[STORED] Key: '{key}' -> Value: '{value}' (Committed to WAL & State)")

    def recover_state(self):
        """⚡ INTERVIEW FLEX: Replays the WAL to recover state after a crash."""
        if not os.path.exists(self.log_path):
            print("[INIT] No existing WAL found. Fresh database state initialized.")
            return

        print("[RECOVERY] System crash/restart detected! Replaying log ledger...")
        print("-" * 65)
        with open(self.log_path, "r") as log:
            for line in log:
                parts = line.strip().split(":")
                if parts[0] == "SET":
                    # Re-materialize the state machine step-by-step
                    self.state[parts[1]] = parts[2]
                    print(f" -> Replayed transaction: SET {parts[1]} = {parts[2]}")
        print("-" * 65)
        print(f"[RECOVERY COMPLETE] Current State Materialized: {self.state}\n")

if __name__ == "__main__":
    # --- SIMULATION 1: Run transactions and populate state ---
    db = WALStorageEngine()
    db.set("user_1", "Kshitij")
    db.set("role", "Engineer")
    
    print(f"\n[CRASH SIMULATION] Killing database connection... Memory cleared.")
    print(f"Active Memory State before crash: {db.state}\n")
    
    # --- SIMULATION 2: Instantiate new instance (Simulating system restart) ---
    print("Restarting database engine instance...")
    recovered_db = WALStorageEngine()
    print(f"Verified Recovered Memory State: {recovered_db.state}")