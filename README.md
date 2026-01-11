# ServiceNow Consultant - AI-Powered Solution Architect

An intelligent AI assistant for ServiceNow that provides expert guidance on best practices, troubleshooting, and architecture decisions. Built with Claude (Anthropic), LangChain, and Streamlit.

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file:
   ```
   ANTHROPIC_API_KEY=your_anthropic_key
   OPENAI_API_KEY=your_openai_key
   TAVILY_API_KEY=your_tavily_key
   SN_INSTANCE=your-instance.service-now.com (optional)
   SN_USER=your_username (optional)
   SN_PASSWORD=your_password (optional)
   ```

3. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Access at:** http://localhost:8501

### Quick Deployment

- **Streamlit Cloud:** See `QUICK_DEPLOY.md` or `streamlit_cloud_config.md`
- **Docker:** `docker-compose up -d`
- **Full Guide:** See `DEPLOYMENT_GUIDE.md`

## 📖 Features

- 🔍 **Intelligent Search:** Searches official ServiceNow documentation
- 📚 **Knowledge Base:** Upload and query your internal documents
- 🔌 **Live Instance:** Connect to your ServiceNow instance for real-time data
- 💡 **Best Practices:** AI-powered recommendations based on official docs
- 🎯 **Context-Aware:** Considers both official standards and your internal policies

## 🛠️ Architecture

- **AI Model:** Claude Sonnet 4 (Anthropic)
- **Framework:** LangChain + LangGraph
- **UI:** Streamlit
- **Vector DB:** ChromaDB
- **Search:** Tavily API for public docs

## 📚 Documentation

- `DEPLOYMENT_GUIDE.md` - Comprehensive deployment options
- `QUICK_DEPLOY.md` - Fast deployment guide
- `manual_testing_guide.md` - Testing procedures
- `CONNECTION_DIAGNOSTIC_REPORT.md` - Troubleshooting connection issues

## 🔐 Security

- Never commit `.env` file (already in `.gitignore`)
- Use environment variables or secrets management
- Rotate API keys regularly
- Use least-privilege ServiceNow credentials

---

## ServiceNow Python Client

A Python-based client for interacting with ServiceNow REST API using async httpx requests.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

3. Update `.env` with your ServiceNow credentials:
```
SN_INSTANCE=your-instance.service-now.com
SN_USER=your_username
SN_PASSWORD=your_password
```

## Usage

### Basic Usage

```python
import asyncio
from servicenow_client import ServiceNowClient

async def main():
    client = ServiceNowClient()
    
    # Get records from a table
    records = await client.get_table_records(
        table_name="sys_user",
        query_params={"active": "true"},
        limit=10
    )
    
    print(records)
    await client.close()

asyncio.run(main())
```

### Using Context Manager

```python
async def main():
    async with ServiceNowClient() as client:
        records = await client.get_table_records("sys_user", limit=5)
        print(records)
```

## Testing

Run the test script:
```bash
python main.py
```

This will test the connection to ServiceNow and retrieve a few records from the `sys_user` table.
