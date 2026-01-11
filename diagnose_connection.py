"""Diagnose ServiceNow connection issues."""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

print("=" * 60)
print("ServiceNow Connection Diagnostic Tool")
print("=" * 60)

# Load environment variables
env_paths = [
    Path(__file__).parent / ".env",
    Path.cwd() / ".env"
]
env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"\n[OK] Loaded .env from: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("\n[WARNING] No .env file found in expected locations")
    load_dotenv()

# Check environment variables
print("\n" + "=" * 60)
print("STEP 1: Checking Environment Variables")
print("=" * 60)

instance = os.getenv("SN_INSTANCE")
username = os.getenv("SN_USER")
password = os.getenv("SN_PASSWORD")

issues = []

if not instance:
    print("[ERROR] SN_INSTANCE is not set")
    issues.append("Missing SN_INSTANCE")
else:
    print(f"[OK] SN_INSTANCE: {instance}")

if not username:
    print("[ERROR] SN_USER is not set")
    issues.append("Missing SN_USER")
else:
    print(f"[OK] SN_USER: {username[:3]}***")

if not password:
    print("[ERROR] SN_PASSWORD is not set")
    issues.append("Missing SN_PASSWORD")
else:
    print(f"[OK] SN_PASSWORD: {'*' * len(password)}")

if issues:
    print(f"\n[CRITICAL] Found {len(issues)} credential issue(s):")
    for issue in issues:
        print(f"  - {issue}")
    print("\nPlease check your .env file and ensure all three variables are set:")
    print("  SN_INSTANCE=your-instance.service-now.com")
    print("  SN_USER=your-username")
    print("  SN_PASSWORD=your-password")
    sys.exit(1)

# Test client initialization
print("\n" + "=" * 60)
print("STEP 2: Testing Client Initialization")
print("=" * 60)

try:
    from servicenow_client import ServiceNowClient
    client = ServiceNowClient()
    print("[OK] ServiceNowClient initialized successfully")
    print(f"  Instance: {client.instance}")
    print(f"  Base URL: {client.base_url}")
except ValueError as e:
    print(f"[ERROR] Initialization failed: {e}")
    print("\nThis usually means missing or invalid credentials.")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test connection
print("\n" + "=" * 60)
print("STEP 3: Testing Connection to ServiceNow")
print("=" * 60)

async def test_connection():
    try:
        print("Attempting to connect...")
        result = await client.get_table_records("sys_user", limit=1)
        if result and "result" in result:
            print("[SUCCESS] Connection successful!")
            print(f"  Retrieved {len(result.get('result', []))} test record(s)")
            return True, None
        else:
            error_msg = "Connection failed: No data returned"
            print(f"[ERROR] {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"[ERROR] Connection failed!")
        print(f"  Error Type: {error_type}")
        print(f"  Error Message: {error_msg}")
        
        # Provide specific guidance based on error type
        if "401" in error_msg or "Unauthorized" in error_msg:
            print("\n  [DIAGNOSIS] Authentication failed - check username/password")
        elif "403" in error_msg or "Forbidden" in error_msg:
            print("\n  [DIAGNOSIS] Access denied - check user permissions")
        elif "404" in error_msg or "Not Found" in error_msg:
            print("\n  [DIAGNOSIS] Instance URL may be incorrect")
        elif "timeout" in error_msg.lower() or "Timeout" in error_msg:
            print("\n  [DIAGNOSIS] Connection timeout - check network/firewall")
        elif "Request error" in error_msg:
            print("\n  [DIAGNOSIS] Network error - check internet connection and instance URL")
        
        import traceback
        print("\n  Full traceback:")
        traceback.print_exc()
        return False, error_msg
    finally:
        await client.close()

success, error_msg = asyncio.run(test_connection())

# Test get_error_logs function
if success:
    print("\n" + "=" * 60)
    print("STEP 4: Testing get_error_logs Tool")
    print("=" * 60)
    
    async def test_error_logs():
        try:
            from tools import get_error_logs
            print("Calling get_error_logs()...")
            result = await get_error_logs()
            print("[SUCCESS] get_error_logs executed successfully")
            print(f"  Result length: {len(result)} characters")
            if len(result) < 500:
                print(f"\n  Full result:\n  {result}")
            else:
                print(f"\n  First 300 characters:\n  {result[:300]}...")
        except Exception as e:
            print(f"[ERROR] get_error_logs failed: {e}")
            print(f"  Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(test_error_logs())

# Summary
print("\n" + "=" * 60)
print("DIAGNOSTIC SUMMARY")
print("=" * 60)

if not success:
    print("\n[FAILED] Connection test failed")
    print(f"\nError details: {error_msg}")
    print("\nPossible causes:")
    print("  1. Incorrect instance URL (check SN_INSTANCE)")
    print("  2. Incorrect username/password (check SN_USER/SN_PASSWORD)")
    print("  3. Network/firewall blocking connection")
    print("  4. ServiceNow instance is down or unreachable")
    print("  5. User account is locked or disabled")
    print("\nNext steps:")
    print("  1. Verify credentials in .env file")
    print("  2. Test connection manually in browser: https://{instance}/api/now/table/sys_user?sysparm_limit=1")
    print("  3. Check network connectivity")
    print("  4. Contact ServiceNow administrator if issue persists")
else:
    print("\n[SUCCESS] All connection tests passed!")
    print("Your ServiceNow connection is working correctly.")

print("\n" + "=" * 60)
