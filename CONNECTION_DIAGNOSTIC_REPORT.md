# ServiceNow Connection Diagnostic Report

## Issue Summary
You're experiencing an error message: *"I apologize, but I'm experiencing a technical issue connecting to your live instance at the moment. Let me provide you with the specific steps you can take to analyze your Discovery logs manually"*

This error occurs when the agent tries to connect to your ServiceNow instance but encounters a connection failure.

## Root Cause Analysis

The error flow is:
1. User requests to check live instance (e.g., "check Discovery logs")
2. Agent calls `check_live_instance` tool
3. Tool calls `get_error_logs()` or similar function
4. Function tries to initialize `ServiceNowClient()`
5. Connection fails (missing credentials, network issue, authentication failure, etc.)
6. Exception is caught and returned as error string
7. AI model generates the apologetic response you're seeing

## Common Causes

### 1. Missing Credentials (Most Common)
**Symptoms:**
- Error mentions missing SN_INSTANCE, SN_USER, or SN_PASSWORD
- Connection fails immediately

**Solution:**
- Check your `.env` file in the project root
- Ensure these variables are set:
  ```
  SN_INSTANCE=your-instance.service-now.com
  SN_USER=your-username
  SN_PASSWORD=your-password
  ```
- Note: Instance URL should NOT include `https://` prefix

### 2. Authentication Failure
**Symptoms:**
- Error contains "401" or "Unauthorized"
- Credentials are set but connection fails

**Solution:**
- Verify username and password are correct
- Check if account is locked or disabled
- Ensure password hasn't expired
- Try logging into ServiceNow web UI with same credentials

### 3. Network/Connection Issues
**Symptoms:**
- Error contains "timeout", "Connection", or "Request error"
- Connection hangs or fails to establish

**Solution:**
- Check internet connectivity
- Verify instance URL is correct and accessible
- Check firewall/proxy settings
- Test connection manually: `https://your-instance.service-now.com/api/now/table/sys_user?sysparm_limit=1`

### 4. Access Permissions
**Symptoms:**
- Error contains "403" or "Forbidden"
- Connection succeeds but API calls fail

**Solution:**
- Verify user has REST API access
- Check user roles include necessary permissions
- Ensure user can access the specific tables (syslog, sys_dictionary, etc.)

### 5. Incorrect Instance URL
**Symptoms:**
- Error contains "404" or "Not Found"
- Connection fails immediately

**Solution:**
- Verify instance URL format: `your-instance.service-now.com` (no https://)
- Check for typos in instance name
- Ensure instance is active and accessible

## Diagnostic Steps

### Step 1: Check Environment Variables
Run the diagnostic script:
```bash
python diagnose_connection.py
```

Or manually check your `.env` file:
- Location: `c:\Users\Kajal Gupta\SN Consultant\.env`
- Should contain: `SN_INSTANCE`, `SN_USER`, `SN_PASSWORD`

### Step 2: Test Connection Manually
1. Open browser
2. Navigate to: `https://your-instance.service-now.com/api/now/table/sys_user?sysparm_limit=1`
3. Enter credentials when prompted
4. If this fails, the issue is with credentials or network

### Step 3: Check Recent Logs
Check the debug log for detailed error information:
```bash
# View last 50 lines of debug log
Get-Content ".cursor\debug.log" -Tail 50
```

### Step 4: Verify ServiceNow Instance
- Ensure instance is active and not in maintenance mode
- Check ServiceNow status page if applicable
- Verify instance URL is correct

## Improvements Made

I've improved error handling in the codebase to provide more specific error messages:

1. **Better credential error messages** - Now tells you exactly which credential is missing
2. **HTTP status code detection** - Provides specific guidance for 401, 403, 404 errors
3. **Timeout detection** - Identifies network timeout issues
4. **Connection error details** - More descriptive error messages

## Next Steps

1. **Run the diagnostic script:**
   ```bash
   python diagnose_connection.py
   ```

2. **Check your `.env` file** and verify credentials are correct

3. **Test connection manually** in browser to isolate the issue

4. **Review the specific error message** - The improved error handling should now tell you exactly what's wrong

5. **If issue persists**, check:
   - ServiceNow instance status
   - Network connectivity
   - Firewall/proxy settings
   - User account status in ServiceNow

## Files Modified

- `tools.py` - Enhanced error handling for all ServiceNow connection functions:
  - `get_error_logs()` - Better error messages for connection failures
  - `fetch_recent_changes()` - Improved credential and connection error handling
  - `check_table_schema()` - Enhanced error detection and reporting

## Additional Resources

- ServiceNow REST API Documentation: https://docs.servicenow.com/
- ServiceNow Instance Status: Check your instance admin panel
- Connection Test Script: `diagnose_connection.py` (created for you)

---

**Last Updated:** Based on analysis of connection error patterns
**Status:** Error handling improved, diagnostic tools created
