"""Streamlit UI for ServiceNow Consultant."""

import asyncio
import streamlit as st
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
import json
import os
from datetime import datetime, timedelta
import time
import re

from agent import get_agent
from knowledge_base import ingest_user_file, get_indexed_files, remove_file_from_kb, get_knowledge_base_stats
from config import (
    load_config, save_config, get_search_domains, get_sn_credentials,
    update_sn_credentials, add_search_domain, remove_search_domain,
    get_safety_level, update_safety_level
)
from ui_helpers import get_learned_rules, delete_learned_rule, test_sn_connection, check_connection_health
from rate_limit_handler import get_rate_limit_info_from_exception, format_cooldown_message
from tools import save_learned_preference




def normalize_instance_name(instance: str) -> str:
    """
    Normalize ServiceNow instance name to just the domain.
    Strips protocol, trailing slashes, paths, and www prefix.
    
    Args:
        instance: Instance input (could be URL or just domain)
        
    Returns:
        Normalized instance name (e.g., 'dev12345.service-now.com')
    """
    if not instance:
        return ""
    
    # Remove protocol
    instance = instance.replace("https://", "").replace("http://", "")
    
    # Remove www. prefix
    if instance.startswith("www."):
        instance = instance[4:]
    
    # Remove trailing slash and any path
    instance = instance.split("/")[0]
    
    # Remove trailing slash if still present
    instance = instance.rstrip("/")
    
    return instance.strip()


def extract_instance_name_for_display(instance_url: str) -> str:
    """
    Extract just the instance name from a full URL for display purposes.
    Removes protocol and .service-now.com suffix.
    
    Args:
        instance_url: Full instance URL (e.g., 'https://dev12345.service-now.com')
        
    Returns:
        Instance name only (e.g., 'dev12345')
    """
    if not instance_url:
        return ""
    
    # Remove protocol
    instance = instance_url.replace("https://", "").replace("http://", "")
    
    # Remove trailing slash and any path
    instance = instance.split("/")[0]
    
    # Remove .service-now.com suffix if present
    if instance.endswith(".service-now.com"):
        instance = instance[:-len(".service-now.com")]
    
    return instance.strip()


def format_instance_for_save(instance_input: str) -> str:
    """
    Format instance input to full URL for saving.
    Accepts instance name or full URL, returns full URL.
    
    Args:
        instance_input: Instance name or URL (e.g., 'dev12345' or 'dev12345.service-now.com' or 'https://dev12345.service-now.com')
        
    Returns:
        Full URL (e.g., 'https://dev12345.service-now.com')
    """
    if not instance_input:
        return ""
    
    # Normalize to get just the domain (strips protocol, paths, etc.)
    instance = normalize_instance_name(instance_input)
    
    if not instance:
        return ""
    
    # If it already has .service-now.com, use it as is
    if ".service-now.com" in instance:
        return f"https://{instance}"
    
    # Otherwise, assume it's just the instance name (e.g., 'dev12345') and add .service-now.com
    return f"https://{instance}.service-now.com"


# Page configuration
st.set_page_config(
    page_title="ServiceNow Consultant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"  # Collapsed since we use tabs
)

# Load Inter font
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# Minimal CSS for clean, professional UI
st.markdown("""
<style>
/* Minimal Professional CSS - Clean & Maintainable */
:root {
    --primary: #0F172A;
    --accent: #4A90A4;
    --success: #10B981;
    --text-primary: #1F2937;
    --text-secondary: #6B7280;
    --border: #E5E7EB;
    --bg: #FFFFFF;
    --bg-secondary: #F8F9FA;
}

/* Typography */
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Hide Streamlit Chrome */
#MainMenu, footer, .stDeployButton {
    display: none !important;
}

/* Sidebar toggle button - ensure visible */
header[data-testid="stHeader"] button:first-child {
    display: flex !important;
    visibility: visible !important;
}

/* Content container - reduced top padding */
.main .block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
}

/* Chat messages */
div[data-testid="stChatMessageUser"] {
    background-color: #F1F5F9 !important;
    padding: 12px 16px !important;
    border-radius: 12px !important;
    margin: 8px 0 !important;
    max-width: 85% !important;
    margin-left: auto !important;
}

div[data-testid="stChatMessageAssistant"] {
    background-color: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-left: 4px solid var(--primary) !important;
    padding: 16px 20px !important;
    border-radius: 12px !important;
    margin: 8px 0 !important;
    max-width: 85% !important;
}

/* Chat input sticky */
.stChatInputContainer {
    position: sticky !important;
    bottom: 0 !important;
    background: white !important;
    padding-top: 1rem !important;
    margin-top: 2rem !important;
    border-top: 1px solid var(--border) !important;
}

/* Hide Material Icon text in expanders - hide the icon span elements */
div[data-testid="stExpander"] summary span[data-testid="stIconMaterial"],
div[data-testid="stExpander"] summary span[class*="stIconMaterial"],
div[data-testid="stExpander"] summary .st-emotion-cache-ixgm6x {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    font-size: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
}

/* Responsive */
@media screen and (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
    }
}
</style>
<script>
// Remove Material Icon text from expander labels
(function() {
    function cleanExpanderLabels() {
        document.querySelectorAll('div[data-testid="stExpander"] summary').forEach(summary => {
            // Hide Material Icon span elements
            summary.querySelectorAll('span[data-testid="stIconMaterial"], span[class*="stIconMaterial"]').forEach(span => {
                span.style.display = 'none';
                span.style.visibility = 'hidden';
                span.style.width = '0';
                span.style.height = '0';
                span.style.fontSize = '0';
                span.style.lineHeight = '0';
            });
            
            // Remove Material Icon text from text nodes
            const walker = document.createTreeWalker(summary, NodeFilter.SHOW_TEXT, null, false);
            let node;
            while (node = walker.nextNode()) {
                const text = node.textContent;
                if (text && /keyboard[_\\s]*arrow|key[_\\s]*oard/.test(text)) {
                    node.textContent = text.replace(/keyboard[_\\s]*arrow[_\\s]*right/gi, '')
                                           .replace(/keyboard[_\\s]*double[_\\s]*arrow[_\\s]*right/gi, '')
                                           .replace(/key[_\\s]*oard[_\\s]*arrow/gi, '')
                                           .replace(/key[_\\s]*oard/gi, '')
                                           .trim();
                }
            }
        });
    }
    
    // Run immediately and on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', cleanExpanderLabels);
    } else {
        cleanExpanderLabels();
    }
    
    // Watch for new expanders added dynamically
    const observer = new MutationObserver(() => {
        cleanExpanderLabels();
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = get_agent()
            st.session_state.agent_state = {
                "messages": [SystemMessage(content=st.session_state.agent.system_prompt)]
            }
        except Exception as e:
            st.session_state.agent = None
            st.session_state.agent_error = str(e)
    if "tool_calls_history" not in st.session_state:
        st.session_state.tool_calls_history = {}
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Consultant"
    # Initialize connection health tracking
    if "last_health_check" not in st.session_state:
        st.session_state.last_health_check = 0
    if "connection_health_status" not in st.session_state:
        st.session_state.connection_health_status = "not_configured"
    if "connection_health_message" not in st.session_state:
        st.session_state.connection_health_message = ""
    if "connection_instance_url" not in st.session_state:
        st.session_state.connection_instance_url = ""
    if "connection_last_check_time" not in st.session_state:
        st.session_state.connection_last_check_time = None


def run_agent_sync(message: str, state: dict) -> dict:
    """Run agent asynchronously and return result (synchronous wrapper)."""
    try:
        agent = st.session_state.agent
        if not agent:
            return {"error": "Agent not initialized"}
        return asyncio.run(agent.invoke(message, state))
    except Exception as e:
        return {"error": str(e)}


def parse_agent_messages(messages: List) -> List[Dict[str, Any]]:
    """Parse agent messages into displayable format."""
    # #region debug log
    try:
        with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"streamlit_app.py:144","message":"parse_agent_messages entry","data":{"message_count":len(messages)},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
    except: pass
    # #endregion
    parsed = []
    all_tool_calls = []  # Collect all tool calls for the final AI response
    
    for msg in messages:
        if isinstance(msg, HumanMessage):
            parsed.append({
                "type": "human",
                "content": msg.content,
                "id": id(msg)
            })
        elif isinstance(msg, AIMessage):
            has_tool_calls = hasattr(msg, "tool_calls") and msg.tool_calls
            # Collect tool calls from this AI message
            if has_tool_calls:
                # #region debug log
                try:
                    with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"streamlit_app.py:157","message":"Found tool_calls in AIMessage","data":{"tool_count":len(msg.tool_calls),"has_content":bool(msg.content)},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
                except: pass
                # #endregion
                for tc in msg.tool_calls:
                    # Handle both dict and object-style tool calls
                    if isinstance(tc, dict):
                        all_tool_calls.append({
                            "name": tc.get("name", "unknown"),
                            "args": tc.get("args", {}),
                            "id": tc.get("id", "")
                        })
                    else:
                        # Handle object-style tool calls
                        get_method = getattr(tc, "get", None)
                        if get_method:
                            name = get_method("name", "unknown")
                            args = get_method("args", {})
                            tool_id = get_method("id", "")
                        else:
                            name = getattr(tc, "name", "unknown")
                            args = getattr(tc, "args", {})
                            tool_id = getattr(tc, "id", "")
                        
                        all_tool_calls.append({
                            "name": name,
                            "args": args,
                            "id": tool_id,
                        })
            
            # Only add AI message content if it has NO tool_calls (final response only)
            # Skip intermediate "let me check..." messages that have tool_calls
            if msg.content and not has_tool_calls:
                # Clean content - aggressively remove any raw JSON/tool_use structures
                import re
                cleaned_content = str(msg.content)
                
                # If content is a list or contains list-like structures, extract only text parts
                if isinstance(msg.content, list):
                    # Extract only text-type content from list
                    text_parts = []
                    for item in msg.content:
                        if isinstance(item, dict):
                            if item.get('type') == 'text' and 'text' in item:
                                text_parts.append(str(item['text']))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    # Join with newlines to preserve formatting, not spaces
                    cleaned_content = '\n'.join(text_parts)
                else:
                    cleaned_content = str(msg.content)
                
                # Remove all JSON-like structures aggressively - but preserve newlines
                # Remove patterns like {'text': '...', 'type': 'text'}
                cleaned_content = re.sub(r"\{[^}]*'text'[^}]*'type'[^}]*'text'[^}]*\}[,\s]*", "", cleaned_content, flags=re.MULTILINE)
                # Remove patterns like {'id': '...', 'name': '...', 'type': 'tool_use'}
                cleaned_content = re.sub(r"\{[^}]*'type'[^}]*'tool_use'[^}]*\}[,\s]*", "", cleaned_content, flags=re.MULTILINE)
                cleaned_content = re.sub(r"\{[^}]*'tool_use'[^}]*\}[,\s]*", "", cleaned_content, flags=re.MULTILINE)
                # Remove any remaining dictionary-like structures - but be careful not to remove markdown
                # Only remove if it looks like JSON (has quotes and colons)
                cleaned_content = re.sub(r"\{[^}]*'[^']*'\s*:\s*[^}]*\}[,\s]*", "", cleaned_content, flags=re.MULTILINE)
                # Remove debug text patterns
                cleaned_content = re.sub(r"key\.[^.\s]*", "", cleaned_content, flags=re.IGNORECASE)
                # Remove unrendered icon names
                cleaned_content = re.sub(r"key[_\s]*oard[_\s]*arrow[_\s]*right", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"key[_\s]*oard[_\s]*double[_\s]*arrow[_\s]*right", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"key[_\s]*oard[_\s]*arrow[_\s]*left", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"key[_\s]*oard[_\s]*double[_\s]*arrow[_\s]*left", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"key[_\s]*oard[_\s]*arrow[_\s]*down", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"key[_\s]*oard[_\s]*arrow[_\s]*up", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"\bkey[_\s]+[a-z_]+", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"oaralyzing[^.\s]*", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"oSwuright[^.\s]*", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"[a-zA-Z]+uright[^.\s]*", "", cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"Analyzing\.\.\.[^.]*", "", cleaned_content, flags=re.IGNORECASE | re.MULTILINE)
                # Clean up extra whitespace and commas - BUT preserve newlines for formatting
                cleaned_content = re.sub(r",\s*,+", ",", cleaned_content)
                # Replace multiple spaces/tabs with single space, but preserve newlines and markdown
                # Process line by line to preserve newlines and markdown syntax
                lines = cleaned_content.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Check if line starts with markdown syntax - preserve it carefully
                    if re.match(r'^\s*(##+|###+|\*\*|[-*]|\d+\.)', line):
                        # This is a markdown line - preserve as-is, only clean excessive spaces (3+)
                        cleaned_line = re.sub(r"[ \t]{3,}", " ", line)  # Only collapse 3+ spaces
                    else:
                        # Regular line - can collapse spaces/tabs
                        cleaned_line = re.sub(r"[ \t]+", " ", line)
                    cleaned_lines.append(cleaned_line)
                cleaned_content = '\n'.join(cleaned_lines)
                # Preserve newlines - they're important for markdown formatting
                cleaned_content = cleaned_content.strip()
                
                # If content was completely removed by cleaning, check if we can extract text from original
                if not cleaned_content or len(cleaned_content) < 5:
                    # Try to extract just the text part if it's structured
                    original = str(msg.content)
                    # Look for text after 'text': pattern
                    text_match = re.search(r"'text'\s*:\s*['\"]([^'\"]+)['\"]", original)
                    if text_match:
                        cleaned_content = text_match.group(1)
                    else:
                        # Last resort: use original but remove obvious JSON
                        cleaned_content = re.sub(r"\{[^}]*\}", "", original)
                        cleaned_content = re.sub(r"\[[^\]]*\]", "", cleaned_content)
                        cleaned_content = cleaned_content.strip()
                
                # Final cleanup - remove any remaining artifacts BUT preserve markdown syntax
                # Don't remove brackets that are part of markdown (like [text](url) or **text**)
                # Only remove standalone brackets at start/end that are clearly artifacts
                # Check if brackets are part of markdown before removing
                if not re.match(r'^\[.*?\]\(', cleaned_content):  # Not a markdown link
                    cleaned_content = re.sub(r"^[,\[\]]+", "", cleaned_content)
                if not re.search(r'\)$', cleaned_content):  # Not ending with markdown link
                    cleaned_content = re.sub(r"[,\[\]]+$", "", cleaned_content)
                cleaned_content = cleaned_content.strip()
                
                # #region debug log
                try:
                    with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"streamlit_app.py:186","message":"Adding AI message with content","data":{"tool_calls_count":len(all_tool_calls),"content_length":len(cleaned_content),"original_length":len(str(msg.content))},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
                except: pass
                # #endregion
                
                # Filter out intermediate thinking messages (ones that mention checking/searching)
                is_thinking_message = False
                thinking_patterns = [
                    r"let me (check|search|look|find|examine|review)",
                    r"i'll (check|search|look|find|examine|review)",
                    r"i'm (checking|searching|looking|finding|examining|reviewing)",
                    r"first let me",
                    r"let me first",
                    r"i'll start by",
                    r"i'll begin by"
                ]
                for pattern in thinking_patterns:
                    if re.search(pattern, cleaned_content, re.IGNORECASE):
                        is_thinking_message = True
                        break
                
                # Only add if we have meaningful content AND it's not a thinking message
                if cleaned_content and len(cleaned_content) > 3 and not is_thinking_message:
                    parsed.append({
                        "type": "ai",
                        "content": cleaned_content,
                        "id": id(msg),
                        "tool_calls": all_tool_calls.copy() if all_tool_calls else []
                    })
                all_tool_calls = []  # Reset for next response
        elif isinstance(msg, ToolMessage):
            # Tool results are not displayed separately, they're just used internally
            # But check for rate limit errors in tool responses
            tool_content = str(msg.content) if hasattr(msg, 'content') else str(msg)
            if any(keyword in tool_content.lower() for keyword in ['rate limit', '429', 'too many requests', 'quota']):
                # Store rate limit info from tool response
                from rate_limit_handler import extract_rate_limit_info, format_cooldown_message
                rate_limit_info = extract_rate_limit_info(tool_content)
                if rate_limit_info:
                    api_name, cooldown_seconds = rate_limit_info
                    # Store cooldown info for banner display
                    cooldown_end = datetime.now() + timedelta(seconds=cooldown_seconds)
                    api_key = api_name.replace(' ', '_').lower()
                    st.session_state[f"rate_limit_{api_key}"] = {
                        "cooldown_end": cooldown_end.timestamp(),
                        "cooldown_seconds": cooldown_seconds,
                        "api_name": api_name
                    }
                    # Add rate limit message to parsed messages so it shows in UI
                    parsed.append({
                        "type": "ai",
                        "content": format_cooldown_message(api_name, cooldown_seconds),
                        "id": id(msg),
                        "tool_calls": []
                    })
            pass
    
    # #region debug log
    try:
        with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"streamlit_app.py:198","message":"parse_agent_messages exit","data":{"parsed_count":len(parsed),"ai_messages":sum(1 for p in parsed if p["type"]=="ai"),"human_messages":sum(1 for p in parsed if p["type"]=="human")},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
    except: pass
    # #endregion
    return parsed


def render_thinking_accordion(tool_calls: List[Dict]) -> None:
    """Render collapsible tool usage display in a compact format."""
    # #region debug log
    try:
        with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"streamlit_app.py:201","message":"render_thinking_accordion entry","data":{"tool_calls_count":len(tool_calls) if tool_calls else 0},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
    except: pass
    # #endregion
    if not tool_calls:
        return
    
    # Group tool calls by type for cleaner display
    public_docs = []
    user_context = []
    live_instance = []
    other_tools = []
    
    for tc in tool_calls:
        tool_name = tc.get("name", "unknown")
        tool_args = tc.get("args", {})
        
        if tool_name == "consult_public_docs":
            query = tool_args.get("query", "")
            if query:
                public_docs.append(query)
        elif tool_name == "consult_user_context":
            query = tool_args.get("query", "")
            if query:
                user_context.append(query)
        elif tool_name == "check_live_instance":
            query = tool_args.get("query", "")
            table = tool_args.get("table_name", "")
            days = tool_args.get("days_ago", "")
            if query:
                live_instance.append({"query": query, "table": table, "days": days})
        else:
            other_tools.append({"name": tool_name, "args": tool_args})
    
    # Professional Workflow Cards - Show research phases
    with st.container():
        st.markdown("### 🔍 Research Process", unsafe_allow_html=True)
        
        # Phase 1: Public Documentation
        if public_docs:
            with st.container(border=True):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    st.markdown("""
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #4A90A4 0%, #0F172A 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: 600;
                        font-size: 1.2rem;
                    ">1</div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown("**📚 Researching Official ServiceNow Documentation**")
                    queries_str = ", ".join([f"`{q[:40]}...`" if len(q) > 40 else f"`{q}`" for q in public_docs[:2]])
                    if len(public_docs) > 2:
                        queries_str += f" (+{len(public_docs) - 2} more queries)"
                    st.caption(queries_str)
        
        # Phase 2: User Context
        if user_context:
            with st.container(border=True):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    st.markdown("""
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #4A90A4 0%, #0F172A 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: 600;
                        font-size: 1.2rem;
                    ">2</div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown("**📄 Checking Your Knowledge Base**")
                    queries_str = ", ".join([f"`{q[:40]}...`" if len(q) > 40 else f"`{q}`" for q in user_context[:2]])
                    if len(user_context) > 2:
                        queries_str += f" (+{len(user_context) - 2} more queries)"
                    st.caption(queries_str)
        
        # Phase 3: Live Instance (if applicable)
        if live_instance:
            with st.container(border=True):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    st.markdown("""
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #4A90A4 0%, #0F172A 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: 600;
                        font-size: 1.2rem;
                    ">3</div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown("**🔌 Checking Live Instance**")
                    instances_str = ", ".join([
                        f"`{item['query'][:30]}...`" + (f" (table: {item['table']})" if item['table'] else "")
                        for item in live_instance[:2]
                    ])
                    if len(live_instance) > 2:
                        instances_str += f" (+{len(live_instance) - 2} more)"
                    st.caption(instances_str)
        
        # Phase 4: Synthesis
        if public_docs or user_context or live_instance:
            with st.container(border=True):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    st.markdown("""
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: 600;
                        font-size: 1.2rem;
                    ">✓</div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown("**✨ Synthesizing Analysis**")
                    st.caption("Combining official documentation with your context to provide structured recommendations")
        
        if other_tools:
            for tool in other_tools:
                display_name = tool["name"].replace("_", " ").title()
                st.markdown(f"**{display_name}:** {tool['args']}")


def parse_structured_response(content: str) -> Dict[str, str]:
    """
    Parse consultant response to extract structured sections.
    Returns dict with: official_best_practice, your_context, analysis, recommendation
    """
    import re
    sections = {
        "official_best_practice": "",
        "your_context": "",
        "analysis": "",
        "recommendation": "",
        "other": ""
    }
    
    # Patterns to match structured sections - improved to capture full content without leaving markers
    patterns = {
        "official_best_practice": [
            r"\*\*Official Best Practice[:\*]*\*\*[:\s]*(.*?)(?=\*\*(?:Your Context|Analysis|Recommendation)|$)",
            r"##\s*Official Best Practice[:\s]*(.*?)(?=\n##|$)",
            r"Official Best Practice[:\s]*(.*?)(?=\*\*Your Context|\*\*Analysis|\*\*Recommendation|\n##|$)",
        ],
        "your_context": [
            r"\*\*Your Context[:\*]*\*\*[:\s]*(.*?)(?=\*\*(?:Analysis|Recommendation|Official Best Practice)|$)",
            r"##\s*Your Context[:\s]*(.*?)(?=\n##|$)",
            r"Your Context[:\s]*(.*?)(?=\*\*Analysis|\*\*Recommendation|\*\*Official Best Practice|\n##|$)",
        ],
        "analysis": [
            r"\*\*Analysis[:\*]*\*\*[:\s]*(.*?)(?=\*\*(?:Recommendation|Official Best Practice|Your Context)|$)",
            r"##\s*Analysis[:\s]*(.*?)(?=\n##|$)",
            r"Analysis[:\s]*(.*?)(?=\*\*Recommendation|\*\*Official Best Practice|\*\*Your Context|\n##|$)",
        ],
        "recommendation": [
            r"\*\*Recommendation[:\*]*\*\*[:\s]*(.*?)(?=\*\*(?:Official Best Practice|Your Context|Analysis)|$)",
            r"##\s*Recommendation[:\s]*(.*?)(?=\n##|$)",
            r"Recommendation[:\s]*(.*?)(?=\*\*Official Best Practice|\*\*Your Context|\*\*Analysis|\n##|$)",
        ],
    }
    
    # Try to extract sections
    for section_name, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(1).strip()
                break
    
    # If no structured sections found, return original content as "other"
    if not any(sections[k] for k in ["official_best_practice", "your_context", "analysis", "recommendation"]):
        sections["other"] = content
    
    return sections


def format_content_for_display(text: str, remove_structured_headers: bool = False) -> str:
    """Format content to preserve lists as proper markdown lists and remove sources. Applies to all responses."""
    import re
    if not text:
        return text
    
    # Remove structured section headers if requested (for subsequent chat messages)
    if remove_structured_headers:
        # Remove markdown headers (## Official Best Practice, etc.) - match entire line
        text = re.sub(r'^##+\s*(Official Best Practice|Your Context|Analysis|Recommendation)[:\s]*.*?\n', '', text, flags=re.IGNORECASE | re.MULTILINE)
        # Remove bold headers (**Official Best Practice**, etc.) - match entire line
        text = re.sub(r'^\*\*(Official Best Practice|Your Context|Analysis|Recommendation)[:\*]*\*\*[:\s]*.*?\n', '', text, flags=re.IGNORECASE | re.MULTILINE)
        # Remove plain text headers (Official Best Practice:, etc.) - match entire line
        text = re.sub(r'^(Official Best Practice|Your Context|Analysis|Recommendation)[:\s]+.*?\n', '', text, flags=re.IGNORECASE | re.MULTILINE)
        # Also remove inline occurrences (not just at start of line)
        text = re.sub(r'##+\s*(Official Best Practice|Your Context|Analysis|Recommendation)[:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*(Official Best Practice|Your Context|Analysis|Recommendation)[:\*]*\*\*[:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(Official Best Practice|Your Context|Analysis|Recommendation)[:\s]+', '', text, flags=re.IGNORECASE)
    
    # Remove sources/URLs and source headings first - more aggressive removal
    text = re.sub(r'\[.*?\]\(https?://[^\)]+\)', '', text)
    text = re.sub(r'https?://[^\s\)]+', '', text)
    # Remove source headings and everything after them on the same line (case insensitive)
    text = re.sub(r'(?i)(Sources?|Citations?|References?)[:\s]*.*', '', text)
    
    # Handle inline lists - convert "1. text 2. text 3. text" to separate lines
    # Pattern: number followed by period and space, but not at start of line
    text = re.sub(r'(\d+)\.\s+', r'\n\1. ', text)
    # Handle inline bullets - convert " - text - text" to separate lines  
    text = re.sub(r'\s+-\s+', r'\n- ', text)
    
    # Split into lines and process
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        if not line_stripped:
            if in_list:
                formatted_lines.append("")  # End of list
                in_list = False
            continue
        
        # Check if this is a numbered list item (1., 2., 3., etc.) - must be at start
        numbered_match = re.match(r'^(\d+)\.\s+(.+)$', line_stripped)
        # Check if this is a bullet list item (-, *, •) - must be at start
        bullet_match = re.match(r'^[-*]\s+(.+)$', line_stripped) or re.match(r'^[\u2022\u2023\u25E6]\s+(.+)$', line_stripped)
        
        if numbered_match:
            # Numbered list item - ensure it's on its own line with proper markdown
            if not in_list:
                if formatted_lines:  # Add blank line before list if there's previous content
                    formatted_lines.append("")
            formatted_lines.append(f"{numbered_match.group(1)}. {numbered_match.group(2).strip()}")
            in_list = True
        elif bullet_match:
            # Bullet list item - convert to markdown bullet
            if not in_list:
                if formatted_lines:  # Add blank line before list if there's previous content
                    formatted_lines.append("")
            bullet_content = bullet_match.group(1) if bullet_match.lastindex else line_stripped[1:].strip()
            formatted_lines.append(f"- {bullet_content}")
            in_list = True
        else:
            # Regular text
            if in_list:
                formatted_lines.append("")  # End of list
                in_list = False
            formatted_lines.append(line_stripped)
    
    # Join with proper spacing - single newline for list items, double for paragraphs
    result = []
    for i, line in enumerate(formatted_lines):
        if not line:
            result.append("")
        else:
            is_list_item = bool(re.match(r'^\d+\.\s+|^[-*]\s+', line))
            next_is_list = i < len(formatted_lines) - 1 and formatted_lines[i+1] and bool(re.match(r'^\d+\.\s+|^[-*]\s+', formatted_lines[i+1]))
            
            result.append(line)
            if is_list_item and next_is_list:
                result.append("")  # Single newline between list items
            elif not is_list_item:
                result.append("")  # Double newline for paragraphs
                result.append("")
    
    formatted = "\n".join(result)
    
    # Clean up excessive blank lines (max 2 consecutive) - preserve paragraph spacing
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    # Clean up any double spaces left after removing URLs (but preserve single spaces and newlines)
    formatted = re.sub(r' {2,}', ' ', formatted)
    
    # Ensure proper spacing around bold text and lists
    # Add space after bold if followed by text without space
    formatted = re.sub(r'\*\*([^*]+)\*\*([^\s\n])', r'**\1** \2', formatted)
    
    return formatted.strip()


def render_structured_response(content: str):
    """Render consultant response with all sections fully displayed."""
    import re
    
    # Clean content first - remove icon names and other artifacts
    # BUT preserve em-dashes, newlines, and other punctuation
    cleaned_content = content
    # Remove unrendered icon names
    cleaned_content = re.sub(r"key[_\s]*oard[_\s]*arrow[_\s]*right", "", cleaned_content, flags=re.IGNORECASE)
    cleaned_content = re.sub(r"key[_\s]*oard[_\s]*double[_\s]*arrow[_\s]*right", "", cleaned_content, flags=re.IGNORECASE)
    cleaned_content = re.sub(r"key[_\s]*oard[_\s]*arrow[_\s]*left", "", cleaned_content, flags=re.IGNORECASE)
    cleaned_content = re.sub(r"key[_\s]*oard[_\s]*double[_\s]*arrow[_\s]*left", "", cleaned_content, flags=re.IGNORECASE)
    cleaned_content = re.sub(r"key[_\s]*oard[_\s]*arrow[_\s]*down", "", cleaned_content, flags=re.IGNORECASE)
    cleaned_content = re.sub(r"key[_\s]*oard[_\s]*arrow[_\s]*up", "", cleaned_content, flags=re.IGNORECASE)
    # Remove any remaining "key" followed by underscores and text
    cleaned_content = re.sub(r"\bkey[_\s]+[a-z_]+", "", cleaned_content, flags=re.IGNORECASE)
    # Clean up multiple spaces/tabs but preserve newlines for markdown formatting
    # Replace 2+ spaces/tabs with single space, but don't touch newlines
    cleaned_content = re.sub(r"[ \t]+", " ", cleaned_content)  # Replace multiple spaces/tabs with single space, preserve newlines
    # Preserve newlines - only strip leading/trailing whitespace, not newlines
    cleaned_content = cleaned_content.strip()
    
    sections = parse_structured_response(cleaned_content)
    
    # Clean each section - preserve content, only remove icon artifacts and trailing ##
    for key in sections:
        if sections[key]:
            # Remove icon names from sections too
            sections[key] = re.sub(r"key[_\s]*oard[_\s]*arrow[_\s]*right", "", sections[key], flags=re.IGNORECASE)
            sections[key] = re.sub(r"key[_\s]*oard[_\s]*double[_\s]*arrow[_\s]*right", "", sections[key], flags=re.IGNORECASE)
            sections[key] = re.sub(r"\bkey[_\s]+[a-z_]+", "", sections[key], flags=re.IGNORECASE)
            # Remove trailing ## markers that might have been captured
            sections[key] = re.sub(r"\s*##+\s*$", "", sections[key])
            sections[key] = re.sub(r"##+\s*$", "", sections[key])
            # Only clean up multiple spaces/tabs, preserve newlines for markdown formatting
            sections[key] = re.sub(r"[ \t]+", " ", sections[key])  # Replace multiple spaces/tabs with single space, preserve newlines
            sections[key] = sections[key].strip()
            # Skip empty sections
            if len(sections[key]) < 5:
                sections[key] = ""
    
    # Show all sections fully (no summarization, no expanders)
    # Show in logical order: Official Best Practice, Your Context, Analysis, Recommendation
    # Use simple bold headings instead of markdown headings with icons
    
    if sections["official_best_practice"] and len(sections["official_best_practice"]) > 10:
        st.markdown("**Official Best Practice**")
        st.markdown("")  # Add spacing
        content = format_content_for_display(sections["official_best_practice"])
        # Use markdown with proper formatting - preserve newlines and bold
        st.markdown(content)
        st.markdown("")  # Add spacing between sections
    
    if sections["your_context"] and len(sections["your_context"]) > 10:
        st.markdown("**Your Context**")
        st.markdown("")  # Add spacing
        content = format_content_for_display(sections["your_context"])
        st.markdown(content)
        st.markdown("")  # Add spacing between sections
    
    if sections["analysis"] and len(sections["analysis"]) > 10:
        st.markdown("**Analysis**")
        st.markdown("")  # Add spacing
        content = format_content_for_display(sections["analysis"])
        st.markdown(content)
        st.markdown("")  # Add spacing between sections
    
    if sections["recommendation"] and len(sections["recommendation"]) > 10:
        st.markdown("**Recommendation**")
        st.markdown("")  # Add spacing
        content = format_content_for_display(sections["recommendation"])
        # Use st.markdown to render - Streamlit will automatically format markdown lists, bold, etc.
        st.markdown(content)
    
    # Fallback: if no structured sections, show original content
    if not any(sections[k] and len(sections[k]) > 10 for k in ["official_best_practice", "your_context", "analysis", "recommendation"]):
        if sections["other"]:
            st.markdown(sections["other"])


def render_context_badge():
    """Display connection status using Shadcn Badge - moved to navbar."""
    # This function is kept for potential future use but instance badge is now in navbar
    pass


def render_rate_limit_banner():
    """Display rate limit cooldown banner if any API is on cooldown."""
    rate_limit_keys = [key for key in st.session_state.keys() if key.startswith("rate_limit_")]
    if not rate_limit_keys:
        return
    
    for key in rate_limit_keys:
        rate_limit_info = st.session_state.get(key, {})
        cooldown_end = rate_limit_info.get("cooldown_end", 0)
        api_name = rate_limit_info.get("api_name", key.replace("rate_limit_", "").replace("_", " ").title())
        
        if cooldown_end > time.time():
            # Still on cooldown
            remaining_seconds = int(cooldown_end - time.time())
            
            if remaining_seconds < 60:
                time_str = f"{remaining_seconds} seconds"
            elif remaining_seconds < 3600:
                minutes = remaining_seconds // 60
                seconds = remaining_seconds % 60
                time_str = f"{minutes}m {seconds}s" if seconds > 0 else f"{minutes} minute{'s' if minutes > 1 else ''}"
            else:
                hours = remaining_seconds // 3600
                minutes = (remaining_seconds % 3600) // 60
                time_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours} hour{'s' if hours > 1 else ''}"
            
            st.warning(f"⏱️ **{api_name} Rate Limit**: Please wait **{time_str}** before making more requests.")
        else:
            # Cooldown expired, remove from session state
            if key in st.session_state:
                del st.session_state[key]


def render_consultant_interface():
    """Screen 1: Main chat interface."""
    # Display rate limit banner if any API is on cooldown
    render_rate_limit_banner()
    
    # Initialize agent if needed
    if st.session_state.agent is None:
        st.error(f"Agent initialization failed: {st.session_state.get('agent_error', 'Unknown error')}")
        if st.button("Retry Initialization"):
            st.session_state.agent = None
            init_session_state()
            st.rerun()
        return
    
    # Simple Welcome Screen - Just title and description
    if len(st.session_state.messages) == 0:
        st.title("💼 Your ServiceNow Solution Architect")
        st.markdown("Expert guidance on best practices, troubleshooting, and architecture.")
        st.caption("Powered by official ServiceNow documentation, your knowledge base, and live instance data")
        st.markdown("---")
    
    # Track if structured sections have been shown (once per conversation)
    if "structured_sections_shown" not in st.session_state:
        st.session_state.structured_sections_shown = False
    
    # Display chat history
    for idx, msg_data in enumerate(st.session_state.messages):
        if msg_data["type"] == "human":
            # Use default Streamlit user avatar (no custom avatar)
            with st.chat_message("user", avatar="👤"):
                st.write(msg_data["content"])
        elif msg_data["type"] == "ai":
            # Use default Streamlit assistant avatar (no custom avatar)
            with st.chat_message("assistant", avatar="🤖"):
                # Check if this is a final response (no tool_calls) or intermediate step
                has_tool_calls = msg_data.get("tool_calls") and len(msg_data.get("tool_calls", [])) > 0
                
                # Show response content - structured format for consultant responses
                content = str(msg_data.get("content", ""))
                if content and len(content.strip()) > 3:
                    # Check if content has structured sections
                    has_structured_sections = any(keyword in content for keyword in ["Official Best Practice", "Your Context", "Analysis", "Recommendation"])
                    
                    # Only show structured format if this is the first structured response in the conversation
                    # After that, always show as regular chat
                    if has_structured_sections and not st.session_state.structured_sections_shown:
                        # Render structured response - full content (first time only)
                        render_structured_response(content)
                        st.session_state.structured_sections_shown = True
                        # Don't render again - skip the else block
                    elif not has_structured_sections or st.session_state.structured_sections_shown:
                        # Display as regular chat (either no structured sections, or already shown structured sections)
                        # CRITICAL: Pass content directly to st.markdown() to preserve ALL markdown syntax
                        # Only remove structured section headers if they exist, but preserve everything else
                        import re
                        formatted_content = content
                        
                        # Only remove structured headers if this is a subsequent message (already shown structured format)
                        if has_structured_sections:
                            # Remove structured headers but preserve ALL other markdown (##, ###, **, lists, etc.)
                            formatted_content = re.sub(
                                r'^(##+\s*)?\*\*(Official Best Practice|Your Context|Analysis|Recommendation)[:\*]*\*\*[:\s]*\n?',
                                '',
                                formatted_content,
                                flags=re.IGNORECASE | re.MULTILINE
                            )
                            formatted_content = re.sub(
                                r'^(##+\s*)?(Official Best Practice|Your Context|Analysis|Recommendation)[:\s]+\n?',
                                '',
                                formatted_content,
                                flags=re.IGNORECASE | re.MULTILINE
                            )
                        
                        # Pass directly to st.markdown() - it will properly render ##, ###, **, lists, etc.
                        # DO NOT use format_content_for_display() here as it may corrupt markdown
                        st.markdown(formatted_content)
                elif not has_tool_calls:
                    # Only show fallback if it's not an intermediate step
                    st.markdown("Processing your request...")
                
                # Only show feedback button on final synthesized response (no tool_calls)
                if not has_tool_calls and content and len(content.strip()) > 3:
                    msg_id = msg_data.get("id", idx)
                    unique_key = f"correct_{idx}_{msg_id}"
                    col1, col2 = st.columns([10, 1])
                    with col2:
                        if st.button("👎", key=unique_key, help="Report an error or provide correction"):
                            st.session_state[f"correcting_{idx}"] = True
                            st.rerun()
                    
                    # Correction dialog
                    if st.session_state.get(f"correcting_{idx}", False):
                        with st.form(key=f"correction_form_{idx}"):
                            correction = st.text_area(
                                "What did I get wrong? How should I correct this?",
                                key=f"correction_input_{idx}"
                            )
                            col1, col2 = st.columns(2)
                            with col1:
                                submit = st.form_submit_button("Save Correction")
                            with col2:
                                cancel = st.form_submit_button("Cancel")
                            
                            if submit and correction:
                                # Save preference
                                result = save_learned_preference(correction)
                                st.success("✅ Preference saved. I'll remember this for future conversations.")
                                st.session_state[f"correcting_{idx}"] = False
                                st.rerun()
                            elif cancel:
                                st.session_state[f"correcting_{idx}"] = False
                                st.rerun()
    
    # Process the prompt if one is queued (do this BEFORE rendering chat input to prevent duplicates)
    if "processing_prompt" in st.session_state:
        prompt = st.session_state["processing_prompt"]
        # #region debug log
        try:
            with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"streamlit_app.py:374","message":"Processing prompt found","data":{"prompt_length":len(prompt),"messages_before_processing":len(st.session_state.messages)},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
        except: pass
        # #endregion
        del st.session_state["processing_prompt"]  # Clear the flag
        
        # Simple spinner - no hover collision issues
        with st.spinner("🔍 Consultant is researching..."):
            # Run agent
            result = run_agent_sync(prompt, st.session_state.agent_state)
        
        try:
            # #region debug log
            try:
                with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"streamlit_app.py:382","message":"Agent result received","data":{"has_error":"error" in result,"result_keys":list(result.keys()) if isinstance(result,dict) else "not_dict"},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
            except: pass
            # #endregion
            
            if "error" in result:
                st.session_state.messages.append({
                    "type": "ai",
                    "content": f"❌ **Error:** {result['error']}\n\nPlease try again or check your configuration in the Admin Console.",
                    "id": id(result),
                    "tool_calls": []
                })
            else:
                # Update agent state
                st.session_state.agent_state = result
                
                # Parse messages
                parsed = parse_agent_messages(result.get("messages", []))
                # #region debug log
                try:
                    with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"streamlit_app.py:396","message":"Parsed messages before adding","data":{"parsed_count":len(parsed),"ai_count":sum(1 for m in parsed if m["type"]=="ai"),"human_count":sum(1 for m in parsed if m["type"]=="human"),"messages_before":len(st.session_state.messages)},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
                except: pass
                # #endregion
                # Add to display messages (only AI messages, skip human as it's already added)
                # Tool calls are now combined with AI messages
                # SIMPLE FIX: Only add the LAST AI message from parsed (the final response)
                # Remove any existing AI messages that were added in this same turn
                ai_messages = [msg for msg in parsed if msg["type"] == "ai"]
                if ai_messages:
                    # Remove the last AI message from session_state if it exists (from previous incomplete render)
                    # This prevents duplicates when the same response is processed multiple times
                    if st.session_state.messages and st.session_state.messages[-1].get("type") == "ai":
                        # Check if it's from the same turn (recently added)
                        st.session_state.messages.pop()
                    
                    # Add only the last (most complete) AI message
                    last_ai_msg = ai_messages[-1]
                    # #region debug log
                    try:
                        with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"streamlit_app.py:401","message":"Adding AI message to session_state","data":{"has_tool_calls":bool(last_ai_msg.get("tool_calls")),"tool_calls_count":len(last_ai_msg.get("tool_calls",[])) if last_ai_msg.get("tool_calls") else 0},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
                    except: pass
                    # #endregion
                    st.session_state.messages.append(last_ai_msg)
                # #region debug log
                try:
                    with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"streamlit_app.py:404","message":"Messages after adding AI response","data":{"messages_count_after":len(st.session_state.messages)},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
                except: pass
                # #endregion
        except Exception as e:
            # #region debug log
            try:
                with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"streamlit_app.py:404","message":"Exception during processing","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
            except: pass
            # #endregion
            
            # Check if this is a rate limit error
            rate_limit_info = get_rate_limit_info_from_exception(e)
            if rate_limit_info:
                api_name, cooldown_seconds = rate_limit_info
                error_message = format_cooldown_message(api_name, cooldown_seconds)
                # Store cooldown end time for UI display
                cooldown_end = datetime.now() + timedelta(seconds=cooldown_seconds)
                st.session_state[f"rate_limit_{api_name.replace(' ', '_').lower()}"] = {
                    "cooldown_end": cooldown_end.timestamp(),
                    "cooldown_seconds": cooldown_seconds
                }
            else:
                error_message = f"❌ **Unexpected Error:** {str(e)}\n\nPlease try again or check the Admin Console for configuration issues."
            
            st.session_state.messages.append({
                "type": "ai",
                "content": error_message,
                "id": id(e),
                "tool_calls": []
            })
        st.rerun()
    
    # Chat input area with file upload option - only render if NOT processing
    # Check if we're processing by looking for processing_prompt (it's deleted above, so this is safe)
    is_processing = "processing_prompt" in st.session_state
    
    if not is_processing:
        # Create a container for the input area
        input_container = st.container()
        
        with input_container:
            # File upload button and chat input in same row
            upload_col, chat_col = st.columns([0.1, 0.9])
            
            with upload_col:
                # Paperclip button for file upload
                if st.button("📎", key="quick_upload_btn", help="Upload file to knowledge base"):
                    st.session_state["show_quick_upload"] = True
            
            with chat_col:
                # Chat input (sticky by default in Streamlit)
                prompt = st.chat_input("Ask me about ServiceNow...")
            
            # Quick file upload dialog
            if st.session_state.get("show_quick_upload", False):
                upload_expander_title = "📎 Quick File Upload"
                with st.expander(upload_expander_title, expanded=True):
                    uploaded_file = st.file_uploader(
                        "Choose a file to add to knowledge base",
                        type=["pdf", "txt", "csv"],
                        key="quick_upload_file"
                    )
                    
                    if uploaded_file:
                        upload_dir = Path("./uploads")
                        upload_dir.mkdir(exist_ok=True)
                        
                        file_path = upload_dir / uploaded_file.name
                        try:
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            with st.spinner(f"📄 Processing {uploaded_file.name}..."):
                                chunks = ingest_user_file(str(file_path))
                                if chunks > 0:
                                    st.success(f"✅ **{uploaded_file.name}** indexed successfully ({chunks} chunks created)")
                                else:
                                    st.warning(f"⚠️ **{uploaded_file.name}** processed but no content found")
                        except ValueError as e:
                            st.error(f"❌ **{uploaded_file.name}**: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Error processing **{uploaded_file.name}**: {str(e)}")
                        finally:
                            if file_path.exists():
                                try:
                                    file_path.unlink()
                                except Exception:
                                    pass
                            st.session_state["show_quick_upload"] = False
                            st.rerun()
                    
                    if st.button("Cancel", key="cancel_quick_upload"):
                        st.session_state["show_quick_upload"] = False
                        st.rerun()
            
            # Caption below chat input
            st.caption(
                '⚠️ AI can make mistakes. Verify with [official ServiceNow Documentation](https://docs.servicenow.com/).',
                help="Always verify AI responses with official documentation"
            )
        
        # Handle chat input
        if prompt:
            # #region debug log
            try:
                with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"streamlit_app.py:360","message":"User input received","data":{"prompt_length":len(prompt),"current_messages_count":len(st.session_state.messages)},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
            except: pass
            # #endregion
            # Add user message to session state immediately so it remains visible
            # The chat_input will clear, but the message stays in the chat history
            st.session_state.messages.append({
                "type": "human",
                "content": prompt,
                "id": id(prompt)
            })
            # #region debug log
            try:
                with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"streamlit_app.py:367","message":"User message added to session_state","data":{"messages_count_after":len(st.session_state.messages)},"timestamp":int(datetime.now().timestamp()*1000)})+"\n")
            except: pass
            # #endregion
            # Store prompt for processing (since chat_input clears after rerun)
            st.session_state["processing_prompt"] = prompt
            st.rerun()


def render_knowledge_locker():
    """Screen 2: Professional Knowledge Base management."""
    st.title("📚 Knowledge Base")
    st.caption("Upload your ServiceNow design docs, naming conventions, and customizations")
    
    # Simple Upload Section
    with st.container(border=True):
        st.markdown("### 📤 Upload Files")
        st.caption("Drag & Drop or select files to add to the knowledge base")
        st.caption("Supported formats: PDF, TXT, CSV")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["pdf", "txt", "csv"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
    
    if uploaded_files:
        upload_dir = Path("./uploads")
        upload_dir.mkdir(exist_ok=True)
        
        for uploaded_file in uploaded_files:
            with st.spinner(f"📄 Processing {uploaded_file.name}..."):
                # Save file temporarily
                file_path = upload_dir / uploaded_file.name
                try:
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Ingest file
                    chunks = ingest_user_file(str(file_path))
                    if chunks > 0:
                        st.success(f"✅ **{uploaded_file.name}** indexed successfully ({chunks} chunks created)")
                    else:
                        st.warning(f"⚠️ **{uploaded_file.name}** processed but no content found")
                except ValueError as e:
                    st.error(f"❌ **{uploaded_file.name}**: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error processing **{uploaded_file.name}**: {str(e)}")
                finally:
                    # Clean up temp file
                    if file_path.exists():
                        try:
                            file_path.unlink()
                        except Exception:
                            pass  # Ignore cleanup errors
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Simple File Management
    with st.container(border=True):
        st.markdown("### 📋 Indexed Files")
        st.caption("Files currently available in the knowledge base")
    
    try:
        files = get_indexed_files()
        
        if files:
            for i, file_info in enumerate(files):
                col1, col2, col3, col4 = st.columns([3, 1.5, 1, 1])
                with col1:
                    st.write(f"**{file_info['filename']}**")
                with col2:
                    st.write(f"{file_info['chunk_count']} chunks")
                with col3:
                    st.write("✅ Indexed")
                with col4:
                    if st.button("🗑️ Delete", key=f"delete_file_{i}", use_container_width=True):
                        if remove_file_from_kb(file_info["filename"]):
                            st.success(f"✅ {file_info['filename']} removed")
                            st.rerun()
                        else:
                            st.error(f"❌ Error removing {file_info['filename']}")
        else:
            st.info("No files indexed yet. Upload files above to get started.")
    except Exception as e:
        st.error(f"Error loading files: {str(e)}")
    
    st.markdown("---")
    
    # Simple Consultant Memory Section
    with st.container(border=True):
        st.markdown("### 🧠 Consultant Memory")
        st.caption("Preferences and rules the consultant has learned from your feedback")
    
    try:
        rules = get_learned_rules()
        
        if rules:
            for i, rule in enumerate(rules):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**Rule {i+1}**")
                    st.write(rule['rule'])
                    st.caption(f"Learned on {rule['timestamp']}")
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_rule_{i}", use_container_width=True):
                        if delete_learned_rule(rule['timestamp']):
                            st.success("✅ Rule deleted")
                            st.rerun()
                        else:
                            st.error("❌ Error deleting rule")
        else:
            st.info("No learned preferences yet. Provide feedback on consultant responses to build personalized knowledge.")
    except Exception as e:
        st.error(f"Error loading rules: {str(e)}")


def render_admin_console():
    """Screen 3: Professional Settings and Configuration."""
    st.title("⚙️ Settings")
    st.caption("Configure your ServiceNow connection and consultant preferences")
    
    # Use tabs for better organization with enhanced styling
    tab1, tab2, tab3 = st.tabs(["🔌 Connection", "🎯 Search Scope", "⚙️ Preferences"])
    
    with tab1:
        # Professional Connection Section
        with st.container(border=True):
            st.markdown("### 🔌 Instance Connection")
            st.caption("Connect to your ServiceNow instance to enable live data queries")
    
            config = load_config()
            sn_creds = config.get("servicenow", {})
            
            # Connection status card at top - use health check status
            check_and_update_connection_status()
            health_status = st.session_state.get("connection_health_status", "not_configured")
            health_message = st.session_state.get("connection_health_message", "")
            last_check_time = st.session_state.get("connection_last_check_time", None)
            manual_status = st.session_state.get("connection_status", "not_tested")
            
            # Use health check status if available, otherwise use manual test status
            if health_status == "connected":
                st.success("🟢 **Connected** - Live instance access enabled")
                if last_check_time:
                    st.caption(f"Last health check: {last_check_time} (checks every 15 minutes)")
            elif health_status == "failed":
                st.error("🔴 **Connection Failed** - Please check your credentials")
                if health_message:
                    st.caption(f"Error: {health_message}")
                if last_check_time:
                    st.caption(f"Last checked: {last_check_time}")
            elif manual_status == "connected":
                st.warning("🟡 **Previously Connected** - Health check pending (checks every 15 minutes)")
            elif manual_status == "failed":
                st.error("🔴 **Connection Failed** - Please check your credentials")
            else:
                st.info("🟡 **Not Tested** - Configure and test your connection")
            
            st.markdown("---")
            
            # Get saved instance URL and extract name for display
            saved_instance_url = sn_creds.get("instance", "")
            instance_display_value = extract_instance_name_for_display(saved_instance_url) if saved_instance_url else ""
            
            instance = st.text_input(
                "Instance Name",
                value=instance_display_value,
                help="Enter just the instance name (e.g., dev12345). The full URL will be saved automatically.",
                placeholder="dev12345"
            )
            username = st.text_input(
                "Username",
                value=sn_creds.get("username", ""),
                placeholder="admin"
            )
            password = st.text_input(
                "Password",
                type="password",
                value="",
                help="Leave empty to keep current password",
                placeholder="Enter password"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Test Connection", use_container_width=True):
                    if instance and username and (password or sn_creds.get("password")):
                        instance_url = format_instance_for_save(instance)
                        test_pwd = password if password else sn_creds.get("password", "")
                        with st.spinner("Testing connection..."):
                            success, message = test_sn_connection(instance_url, username, test_pwd)
                            if success:
                                st.success(f"✅ {message}")
                                st.session_state.connection_status = "connected"
                                # Also update health check status
                                st.session_state.connection_health_status = "connected"
                                st.session_state.connection_health_message = message
                                st.session_state.last_health_check = time.time()
                                st.session_state.connection_last_check_time = datetime.now().strftime("%H:%M:%S")
                                st.session_state.connection_instance_url = instance_url
                            else:
                                st.error(f"❌ {message}")
                                st.session_state.connection_status = "failed"
                                # Also update health check status
                                st.session_state.connection_health_status = "failed"
                                st.session_state.connection_health_message = message
                                st.session_state.last_health_check = time.time()
                                st.session_state.connection_last_check_time = datetime.now().strftime("%H:%M:%S")
                                st.session_state.connection_instance_url = instance_url
                    else:
                        st.warning("Please fill in all connection fields")
            
            with col2:
                if st.button("Save Settings", type="primary", use_container_width=True):
                    if instance and username:
                        instance_url = format_instance_for_save(instance)
                        if not instance_url:
                            st.error("Please enter a valid instance name")
                        else:
                            if not password:
                                password = sn_creds.get("password", "")
                            update_sn_credentials(instance_url, username, password)
                            st.success("✅ Connection settings saved")
                    else:
                        st.error("Please fill in instance and username")
    
    with tab2:
        # Simple Search Scope Section
        with st.container(border=True):
            st.markdown("### 🎯 Search Scope")
            st.caption("Manage whitelisted domains for public documentation search")
            
            domains = get_search_domains()
            
            st.markdown("**Current Domains**")
            if domains:
                for i, domain in enumerate(domains):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• {domain}")
                    with col2:
                        if st.button("Remove", key=f"remove_domain_{i}", use_container_width=True):
                            remove_search_domain(domain)
                            st.success(f"✅ {domain} removed")
                            st.rerun()
            else:
                st.info("No domains configured")
            
            st.markdown("---")
            st.markdown("**Add New Domain**")
            col1, col2 = st.columns([3, 1])
            with col1:
                new_domain = st.text_input(
                    "Domain",
                    placeholder="e.g., support.vendor.com",
                    key="new_domain_input",
                    label_visibility="collapsed"
                )
            with col2:
                if st.button("Add", use_container_width=True, type="primary"):
                    if new_domain:
                        if "." in new_domain and not new_domain.startswith("http"):
                            add_search_domain(new_domain)
                            st.success(f"✅ {new_domain} added")
                            st.rerun()
                        else:
                            st.error("Please enter a valid domain (e.g., example.com)")
                    else:
                        st.warning("Please enter a domain")
    
    with tab3:
        # Simple Preferences Section
        with st.container(border=True):
            st.markdown("### ⚙️ Preferences")
            st.caption("Configure consultant behavior and safety settings")
            
            current_level = get_safety_level()
            
            st.markdown("**Safety Level**")
            st.caption("Control how the consultant interacts with your ServiceNow instance")
            
            safety_level = st.select_slider(
                "Safety Level",
                options=["strict", "open"],
                value=current_level,
                help="Strict: Always ask permission. Open: Auto-check read-only tables (future)"
            )
            
            if safety_level != current_level:
                update_safety_level(safety_level)
                st.warning(f"⚠️ Safety level changed to '{safety_level}'. This feature is not yet fully implemented.")


def check_and_update_connection_status():
    """
    Check connection health if 15 minutes have passed since last check.
    Updates session state with current connection status.
    Runs immediately on first load if credentials are configured.
    """
    # Initialize session state for connection health tracking
    if "last_health_check" not in st.session_state:
        st.session_state.last_health_check = 0
    if "connection_health_status" not in st.session_state:
        st.session_state.connection_health_status = "not_configured"
    if "connection_health_message" not in st.session_state:
        st.session_state.connection_health_message = ""
    if "connection_last_check_time" not in st.session_state:
        st.session_state.connection_last_check_time = None
    
    # Get credentials from config
    config = load_config()
    sn_creds = config.get("servicenow", {})
    instance_url = sn_creds.get("instance", "")
    username = sn_creds.get("username", "")
    password = sn_creds.get("password", "")
    
    # Check if 15 minutes (900 seconds) have passed since last check
    current_time = time.time()
    time_since_last_check = current_time - st.session_state.last_health_check
    
    # Health check interval: 15 minutes = 900 seconds
    HEALTH_CHECK_INTERVAL = 900
    
    # Run health check if:
    # 1. Never checked before (last_health_check == 0) AND credentials are configured
    # 2. 15 minutes have passed since last check
    should_check = (
        (st.session_state.last_health_check == 0 and instance_url and username and password) or
        (time_since_last_check >= HEALTH_CHECK_INTERVAL and instance_url and username and password)
    )
    
    if should_check:
        # Perform health check
        success, message, status = check_connection_health(instance_url, username, password)
        
        # Update session state
        st.session_state.connection_health_status = status
        st.session_state.connection_health_message = message
        st.session_state.last_health_check = current_time
        st.session_state.connection_last_check_time = datetime.now().strftime("%H:%M:%S")
        
        # Store instance URL for display
        st.session_state.connection_instance_url = instance_url
    elif not instance_url or not username or not password:
        # No credentials configured
        st.session_state.connection_health_status = "not_configured"
        st.session_state.connection_health_message = ""
        st.session_state.connection_instance_url = ""


def render_header():
    """Render simple header with title, connection status, and clear chat button."""
    # Check and update connection status if needed
    check_and_update_connection_status()
    
    with st.container(border=True):
        header_cols = st.columns([3, 1, 1], gap="medium")
        
        with header_cols[0]:
            st.markdown("### 💼 ServiceNow Consultant")
            st.caption("Expert Solution Architecture & Best Practices")
        
        with header_cols[1]:
            # Display actual connection status based on health check
            status = st.session_state.get("connection_health_status", "not_configured")
            instance_url = st.session_state.get("connection_instance_url", "")
            
            if status == "connected" and instance_url:
                instance_display = extract_instance_name_for_display(instance_url)
                st.markdown(f"**🟢 Connected: {instance_display[:18]}**")
            elif status == "failed":
                st.markdown("**🔴 Connection Failed**")
            elif status == "not_configured":
                st.markdown("**⚪ Offline**")
            else:
                # Fallback to checking if instance URL exists
                config = load_config()
                sn_creds = config.get("servicenow", {})
                instance_url = sn_creds.get("instance", "")
                if instance_url:
                    instance_display = extract_instance_name_for_display(instance_url)
                    st.markdown(f"**🟡 Checking: {instance_display[:18]}**")
                else:
                    st.markdown("**⚪ Offline**")
        
        with header_cols[2]:
            # Clear chat button
            if st.button("🗑️ Clear Chat", use_container_width=True, help="Clear chat history and start a fresh session"):
                st.session_state.messages = []
                st.session_state.structured_sections_shown = False
                st.rerun()


def render_tabs():
    """Render tabs for navigation - replaces sidebar."""
    tab1, tab2, tab3 = st.tabs(["💬 Consultant", "📚 Knowledge Base", "⚙️ Settings"])
    
    with tab1:
        st.session_state.current_page = "Consultant"
        render_consultant_interface()
    
    with tab2:
        st.session_state.current_page = "Knowledge Locker"
        render_knowledge_locker()
    
    with tab3:
        st.session_state.current_page = "Admin Console"
        render_admin_console()


def main():
    """Main application entry point."""
    init_session_state()
    
    # Simple header with title and connection status (boxed in container)
    render_header()
    
    # Use tabs instead of sidebar navigation
    render_tabs()
    


if __name__ == "__main__":
    main()
