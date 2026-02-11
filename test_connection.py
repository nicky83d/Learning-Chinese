#!/usr/bin/env python3
"""Quick test of database connection and migration script."""
import os
import sys

# Test 1: Check environment variables
db_url = "postgresql://postgres:mgB95PsgUxtAkgCL2lLvpbFNvVrih9W@34.52.239.163:5432/vocab?sslmode=require"
print(f"Database URL: {db_url[:50]}...")

# Test 2: Try to import and connect with SQLAlchemy
try:
    from sqlalchemy import create_engine, text
    print("[OK] SQLAlchemy import successful")
except ImportError as e:
    print(f"[ERROR] Failed to import SQLAlchemy: {e}")
    sys.exit(1)

try:
    engine = create_engine(db_url, echo=False, pool_pre_ping=True)
    print("[OK] Engine created")
except Exception as e:
    print(f"[ERROR] Failed to create engine: {e}")
    sys.exit(1)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("[OK] Connection successful")
        print(f"  Query result: {result.fetchone()}")
except Exception as e:
    print(f"[ERROR] Failed to connect: {e}")
    sys.exit(1)

print("\n[SUCCESS] All tests passed!")
