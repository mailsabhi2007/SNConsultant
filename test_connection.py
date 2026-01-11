"""Test ServiceNow connection and diagnose issues."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from servicenow_client import ServiceNowClient
from tools import get_client, get_error_logs

# Load environment variables
env_paths = [
    Path(__file__).parent / ".env",
    Path.cwd() / ".env"
]
env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        print(f"[OK] Loaded .env from: {env_path}")
        break

if not env_loaded:
    print("[WARN] No .env file found")
    load_dotenv()

# Check environment variables
print("\n=== Environment Variables Check ===")
instance = os.getenv("SN_INSTANCE")
username = os.getenv("SN_USER")
password = os.getenv("SN_PASSWORD")

print(f"SN_INSTANCE: {'[OK] Set' if instance else '[ERROR] NOT SET'}")
if instance:
    print(f"  Value: {instance}")
    
print(f"SN_USER: {'[OK] Set' if username else '[ERROR] NOT SET'}")
if username:
    print(f"  Value: {username[:3]}***")

print(f"SN_PASSWORD: {'[OK] Set' if password else '[ERROR] NOT SET'}")
if password:
    print(f"  Value: {'*' * len(password)}")

# Test client initialization
print("\n=== Client Initialization Test ===")
try:
    client = ServiceNowClient()
    print("[OK] ServiceNowClient initialized successfully")
    print(f"  Instance: {client.instance}")
    print(f"  Base URL: {client.base_url}")
except ValueError as e:
    print(f"[ERROR] Initialization failed: {e}")
    print("\n  This usually means missing credentials in .env file")
    exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error during initialization: {e}")
    exit(1)

# Test connection
print("\n=== Connection Test ===")
async def test_connection():
    try:
        # Try to get a simple record
        result = await client.get_table_records("sys_user", limit=1)
        if result and "result" in result:
            print("[OK] Connection successful!")
            print(f"  Retrieved {len(result.get('result', []))} test record(s)")
            return True
        else:
            print("[ERROR] Connection failed: No data returned")
            return False
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print(f"\n  Error type: {type(e).__name__}")
        return False
    finally:
        await client.close()

success = asyncio.run(test_connection())

# Test get_error_logs function
if success:
    print("\n=== Testing get_error_logs Function ===")
    async def test_error_logs():
        try:
            result = await get_error_logs()
            print("[OK] get_error_logs executed successfully")
            print(f"  Result length: {len(result)} characters")
            print(f"  First 200 chars: {result[:200]}...")
        except Exception as e:
            print(f"[ERROR] get_error_logs failed: {e}")
            print(f"  Error type: {type(e).__name__}")
            import traceback
            print("\n  Full traceback:")
            traceback.print_exc()
    
    asyncio.run(test_error_logs())

print("\n=== Summary ===")
if not instance or not username or not password:
    print("[WARN] Missing credentials - check your .env file")
if not success:
    print("[WARN] Connection test failed - check network and credentials")
