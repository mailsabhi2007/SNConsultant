"""Check what error occurs when trying to connect to ServiceNow."""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
env_paths = [
    Path(__file__).parent / ".env",
    Path.cwd() / ".env"
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"Loaded .env from: {env_path}")
        break
else:
    load_dotenv()
    print("Using default .env loading")

print("\n=== Checking Environment Variables ===")
instance = os.getenv("SN_INSTANCE")
username = os.getenv("SN_USER")
password = os.getenv("SN_PASSWORD")

print(f"SN_INSTANCE: {instance if instance else 'NOT SET'}")
print(f"SN_USER: {username if username else 'NOT SET'}")
print(f"SN_PASSWORD: {'SET' if password else 'NOT SET'}")

if not instance or not username or not password:
    print("\n[ERROR] Missing required credentials!")
    print("Please check your .env file and ensure SN_INSTANCE, SN_USER, and SN_PASSWORD are set.")
    sys.exit(1)

print("\n=== Testing ServiceNow Client ===")
try:
    from servicenow_client import ServiceNowClient
    client = ServiceNowClient()
    print(f"Client created successfully")
    print(f"Instance: {client.instance}")
    print(f"Base URL: {client.base_url}")
except Exception as e:
    print(f"[ERROR] Failed to create client: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== Testing Connection ===")
import asyncio

async def test():
    try:
        result = await client.get_table_records("sys_user", limit=1)
        print(f"[SUCCESS] Connection works! Retrieved {len(result.get('result', []))} records")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

asyncio.run(test())

print("\n=== Testing get_error_logs tool ===")
async def test_error_logs():
    try:
        from tools import get_error_logs
        result = await get_error_logs()
        print(f"[SUCCESS] get_error_logs returned: {len(result)} characters")
        if len(result) < 500:
            print(f"Full result: {result}")
        else:
            print(f"First 300 chars: {result[:300]}")
    except Exception as e:
        print(f"[ERROR] get_error_logs failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

asyncio.run(test_error_logs())
