# Streamlit Cloud Package Loading Troubleshooting

## Common Issues and Solutions

### Issue 1: "ModuleNotFoundError" or "No module named 'X'"

**Cause:** Package not in `requirements.txt` or version conflict

**Solution:**
1. Check Streamlit Cloud logs (Dashboard → Manage app → Logs)
2. Verify the package is in `requirements.txt`
3. Ensure version is compatible (not too new/old)

**Fix:**
```bash
# Add missing package to requirements.txt
# Use specific version if needed
package-name==1.2.3
```

### Issue 2: Build Fails During Package Installation

**Cause:** 
- Version conflicts between packages
- Incompatible Python version
- Missing system dependencies

**Solution:**
1. **Pin package versions:**
   ```txt
   # Instead of: package>=1.0.0
   # Use: package==1.2.3
   ```

2. **Check Python version:**
   - Streamlit Cloud uses Python 3.11 by default
   - Ensure packages support Python 3.11

3. **Remove conflicting packages:**
   - Remove test packages from production `requirements.txt`
   - Use `requirements-dev.txt` for development

### Issue 3: ChromaDB Installation Issues

**Cause:** ChromaDB has native dependencies that may fail to build

**Solution:**
```txt
# Use pre-built wheel
chromadb>=0.4.0,<0.5.0
```

### Issue 4: LangChain Package Conflicts

**Cause:** Rapidly changing LangChain ecosystem with version conflicts

**Solution:**
```txt
# Pin compatible versions
langchain-core==0.3.0
langchain-anthropic==0.2.0
langchain-openai==0.2.0
langchain-community==0.3.0
langgraph==0.2.0
```

### Issue 5: Memory Issues During Installation

**Cause:** Large packages or insufficient memory during build

**Solution:**
1. Remove unnecessary packages
2. Use lighter alternatives where possible
3. Split installation into multiple steps (not possible on Streamlit Cloud, but optimize)

## Quick Fixes

### Fix 1: Update requirements.txt

Replace your `requirements.txt` with the production version (without test packages):

```txt
httpx>=0.25.0
python-dotenv>=1.0.0
langchain-core>=0.1.0
langchain-anthropic>=0.1.0
langgraph>=0.0.20
langchain-community>=0.0.20
langchain-openai>=0.1.0
langchain-chroma>=0.4.0
chromadb>=0.4.0
pypdf>=3.0.0
beautifulsoup4>=4.12.0
tavily-python>=0.3.0
langchain-tavily>=0.1.0
streamlit>=1.28.0
streamlit-shadcn-ui>=0.1.0
streamlit-option-menu>=0.3.0
```

### Fix 2: Pin Versions (If Issues Persist)

If you're still having issues, pin specific versions:

```txt
httpx==0.27.0
python-dotenv==1.0.1
langchain-core==0.3.0
langchain-anthropic==0.2.0
langgraph==0.2.0
langchain-community==0.3.0
langchain-openai==0.2.0
langchain-chroma==0.1.0
chromadb==0.4.22
pypdf==4.0.1
beautifulsoup4==4.12.3
tavily-python==0.3.0
langchain-tavily==0.1.0
streamlit==1.39.0
streamlit-shadcn-ui==0.1.0
streamlit-option-menu==0.3.13
```

### Fix 3: Check Logs

1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Click "Manage app" → "Logs"
4. Look for specific error messages
5. Search for the package name that's failing

## Step-by-Step Debugging

### Step 1: Check Build Logs

```
Dashboard → Your App → Manage app → Logs
```

Look for:
- `ERROR: Could not find a version that satisfies the requirement`
- `ModuleNotFoundError: No module named 'X'`
- `ImportError: cannot import name 'X'`

### Step 2: Verify Package Names

Common mistakes:
- `langchain` vs `langchain-core` (use `langchain-core`)
- `openai` vs `langchain-openai` (use `langchain-openai`)
- `anthropic` vs `langchain-anthropic` (use `langchain-anthropic`)

### Step 3: Test Locally First

Before deploying:
```bash
# Create fresh virtual environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install from requirements.txt
pip install -r requirements.txt

# Test imports
python -c "import streamlit; import langchain_core; print('OK')"
```

### Step 4: Check Streamlit Cloud Python Version

Streamlit Cloud uses Python 3.11 by default. Ensure your packages support it.

## Specific Package Issues

### ChromaDB

If ChromaDB fails:
```txt
# Try specific version
chromadb==0.4.22

# Or exclude if not critical (if you're not using knowledge base)
# chromadb>=0.4.0
```

### LangChain Packages

If LangChain packages conflict:
```txt
# Use compatible versions together
langchain-core==0.3.0
langchain-anthropic==0.2.0
langchain-openai==0.2.0
langchain-community==0.3.0
```

### Streamlit Extensions

If Streamlit extensions fail:
```txt
# Try without optional extensions first
streamlit>=1.28.0
# streamlit-shadcn-ui>=0.1.0  # Comment out if causing issues
# streamlit-option-menu>=0.3.0  # Comment out if causing issues
```

## Prevention

1. **Keep requirements.txt minimal:**
   - Only production dependencies
   - No test packages
   - No development tools

2. **Pin versions for stability:**
   - Use `==` instead of `>=` for critical packages
   - Test version combinations locally first

3. **Test before deploying:**
   ```bash
   pip install -r requirements.txt
   python -c "import streamlit_app"  # Test imports
   ```

4. **Monitor package updates:**
   - LangChain packages update frequently
   - Test updates before deploying

## Still Having Issues?

1. **Check Streamlit Cloud Status:**
   - https://status.streamlit.io

2. **Review Full Error Logs:**
   - Copy full error message
   - Search for the specific package

3. **Try Minimal requirements.txt:**
   - Start with just Streamlit
   - Add packages one by one
   - Identify the problematic package

4. **Contact Support:**
   - Streamlit Community: https://discuss.streamlit.io
   - Include full error logs

---

**Quick Fix:** Use the updated `requirements.txt` without test packages!
