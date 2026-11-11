import pytest
from wal_key_value import KVStore

def test_put_and_get():
    """Test basic put and get operations."""
    store = KVStore()
    store.put('key1', 'value1')
    assert store.get('key1') == 'value1'

def test_nonexistent_key():
    """Test getting nonexistent key."""
    store = KVStore()
    assert store.get('nonexistent') is None

def test_multiple_operations():
    """Test multiple sequential operations."""
    store = KVStore()
    store.put('a', 1)
    store.put('b', 2)
    assert store.get('a') == 1
    assert store.get('b') == 2
    store.delete('a')
    assert store.get('a') is None