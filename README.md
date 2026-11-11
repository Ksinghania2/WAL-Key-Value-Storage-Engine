# WAL-Key-Value-Storage-Engine

A simple Python key-value storage project for learning.

## What It Does
This project shows how to save and retrieve data using a simple log file.

## Basic Usage
```python
# Simple example
from storage import KeyValueStore
store = KeyValueStore()
store.put('mykey', 'myvalue')
value = store.get('mykey')
print(value)  # Output: myvalue
```

## How It Works
1. Data gets written to a log file
2. The log remembers the order things were added
3. You can read data back in the same order

## Learn More
- Search online for "Python file storage"
- Try adding more keys and values
- See how the log grows

## Concepts
- Key-value pairs
- Simple file writing
- Reading data back

## Author
Educational project for learning Python
