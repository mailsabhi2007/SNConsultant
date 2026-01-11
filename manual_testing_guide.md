# Manual Testing Guide - ServiceNow Consultant App

This guide provides step-by-step instructions for manually testing the ServiceNow Consultant App according to the alpha testing plan.

## Prerequisites

1. **Environment Setup**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Set required environment variables:
     - `ANTHROPIC_API_KEY` - For Claude API
     - `OPENAI_API_KEY` - For embeddings
     - `TAVILY_API_KEY` - For public docs search
   - Start the Streamlit app: `streamlit run streamlit_app.py`

2. **Test Data Preparation**
   - Prepare sample PDF, TXT, and CSV files for upload testing
   - Have valid ServiceNow instance credentials ready (optional, for live instance testing)
   - Prepare test questions for different categories

## Testing Workflow

### Phase 1: Critical Path Testing (Must Pass for Alpha)

These tests must pass before proceeding to other tests.

#### CRITICAL_001: Agent searches public docs and user context
**Steps:**
1. Open the app in browser
2. Navigate to "Consultant" tab
3. Ask: "How should I configure a Business Rule for auto-assignment?"
4. Observe the "Research Process" section
5. Verify Phase 1 (Public Docs) appears first
6. Verify Phase 2 (User Context) appears second
7. Verify Phase 3 (Synthesis) appears last

**Expected:** Agent follows workflow order: Phase 1 → Phase 2 → Phase 3

#### CRITICAL_002: Structured responses render correctly
**Steps:**
1. Ask a question that triggers structured response
2. Check for presence of these sections:
   - **Official Best Practice**
   - **Your Context**
   - **Analysis**
   - **Recommendation**
3. Verify sections are clearly separated
4. Verify content is readable (not garbled)

**Expected:** All four sections appear in first structured response

#### CRITICAL_003: Chat input disabled during processing
**Steps:**
1. Submit a question
2. Immediately check if chat input is visible
3. Look for "Consultant is researching..." message
4. Try to type in chat input (if visible)

**Expected:** Chat input is hidden/disabled when spinner is shown

#### CRITICAL_004: Clear chat button works
**Steps:**
1. Have at least 2-3 messages in chat
2. Click "🗑️ Clear Chat" button in header
3. Verify all messages disappear
4. Verify welcome screen appears
5. Check Settings tab - verify settings are still there

**Expected:** Chat clears but settings persist

#### CRITICAL_005: File upload and indexing works
**Steps:**
1. Navigate to "Knowledge Base" tab
2. Upload a PDF file
3. Wait for processing to complete
4. Verify success message appears
5. Check "Indexed Files" section - verify file appears
6. Note the chunk count

**Expected:** File uploads, processes, and appears in indexed files list

#### CRITICAL_006: ServiceNow connection test works
**Steps:**
1. Navigate to "Settings" tab
2. Go to "🔌 Connection" sub-tab
3. Enter instance name (e.g., "dev12345")
4. Enter username
5. Enter password
6. Click "Test Connection"
7. Verify connection status updates

**Expected:** Connection test succeeds with valid credentials, fails with invalid

#### CRITICAL_007: Feedback mechanism saves preferences
**Steps:**
1. Ask a question and get a response
2. Click thumbs down (👎) button on the response
3. Enter correction in the form
4. Click "Save Correction"
5. Navigate to "Knowledge Base" tab
6. Check "Consultant Memory" section
7. Verify preference appears

**Expected:** Preference is saved and appears in Knowledge Base tab

#### CRITICAL_008: No garbled text or UI glitches
**Steps:**
1. Navigate through all tabs
2. Submit several questions
3. Check all responses for:
   - Icon names like "keyboard_arrow_right"
   - Overlapping text
   - Broken formatting
   - Missing spacing

**Expected:** No garbled text, proper formatting throughout

#### CRITICAL_009: Agent respects permission guards
**Steps:**
1. Ask a question that might require live instance check
2. Verify agent asks: "Would you like me to connect to your live instance..."
3. Reply "No" or "Don't check"
4. Verify agent does NOT call check_live_instance
5. Reply "Yes" or "please check"
6. Verify agent proceeds with live instance check

**Expected:** Agent never auto-calls live instance without explicit permission

---

### Phase 2: UI/UX Testing

#### UI_001: Tab Navigation
**Steps:**
1. Click "💬 Consultant" tab
2. Click "📚 Knowledge Base" tab
3. Click "⚙️ Settings" tab
4. Switch between tabs multiple times

**Expected:** Tabs switch smoothly, content loads correctly

#### UI_002: Header Display
**Steps:**
1. Check header at top of page
2. Verify title: "💼 ServiceNow Consultant"
3. Verify connection status (🟢 Connected or ⚪ Offline)
4. Verify "🗑️ Clear Chat" button

**Expected:** All header elements visible and functional

#### UI_003: Welcome Screen
**Steps:**
1. Clear chat (if messages exist)
2. Verify welcome screen appears with:
   - Title: "💼 Your ServiceNow Solution Architect"
   - Description text
   - Caption about data sources

**Expected:** Welcome screen appears when no messages

#### UI_004: Responsive Design
**Steps:**
1. Open browser DevTools (F12)
2. Test different viewport sizes:
   - Desktop (1920x1080)
   - Tablet (768x1024)
   - Mobile (375x667)
3. Check for:
   - Text overflow
   - Button visibility
   - Layout breaking

**Expected:** App works on all screen sizes

#### UI_005: Clear Chat Button
**Steps:**
1. Add 3-4 messages
2. Click "🗑️ Clear Chat"
3. Verify messages disappear
4. Verify welcome screen appears

**Expected:** Chat clears completely

#### UI_006: Message Display
**Steps:**
1. Submit a question
2. Verify user message appears with 👤 avatar
3. Wait for response
4. Verify assistant message appears with 🤖 avatar
5. Check message alignment and spacing

**Expected:** Messages display correctly with proper avatars

#### UI_007: Structured Responses
**Steps:**
1. Ask first question in new session
2. Verify structured response with sections:
   - Official Best Practice
   - Your Context
   - Analysis
   - Recommendation
3. Verify sections are clearly labeled

**Expected:** First response shows structured format

#### UI_008: Subsequent Responses
**Steps:**
1. After first structured response, ask follow-up question
2. Verify response shows as regular chat (no section headers)
3. Verify content is still readable

**Expected:** Subsequent responses are regular chat format

#### UI_009: List Formatting
**Steps:**
1. Ask question that should return numbered list
2. Verify list items appear on separate lines
3. Ask question that should return bullet points
4. Verify bullets render correctly

**Expected:** Lists format properly with line breaks

#### UI_010: Source Removal
**Steps:**
1. Get a response that includes sources
2. Check response text for:
   - URLs (https://...)
   - Source citations
   - Reference links

**Expected:** Sources/URLs are removed from displayed content

#### UI_011: Feedback Button
**Steps:**
1. Get a final response (no tool calls in progress)
2. Verify 👎 button appears
3. Check intermediate responses (with tool calls)
4. Verify 👎 button does NOT appear on intermediate responses

**Expected:** Feedback button only on final responses

#### UI_012: Feedback Dialog
**Steps:**
1. Click 👎 button
2. Verify correction form opens
3. Enter correction text
4. Click "Save Correction"
5. Verify success message
6. Check Knowledge Base tab for saved preference

**Expected:** Feedback form works and saves preferences

#### UI_013: Input Field
**Steps:**
1. Check chat input at bottom
2. Type a message
3. Verify text appears in input
4. Submit message

**Expected:** Input field is visible and functional

#### UI_014: Disabled During Processing
**Steps:**
1. Submit a question
2. Immediately check if input is visible
3. Look for spinner/processing message
4. Wait for response to complete
5. Verify input reappears

**Expected:** Input hidden/disabled during processing

#### UI_015: Single Input Field
**Steps:**
1. Check page for duplicate chat inputs
2. Submit a message
3. Check again for duplicates

**Expected:** Only one chat input appears

#### UI_016: File Upload Button
**Steps:**
1. Click 📎 button next to chat input
2. Verify quick upload dialog opens
3. Verify file uploader appears
4. Click "Cancel"
5. Verify dialog closes

**Expected:** File upload button opens dialog correctly

#### UI_017: Input Persistence
**Steps:**
1. Type a message in chat input
2. Submit message
3. Verify input clears after submission

**Expected:** Input clears after submission

#### UI_018: No Garbled Text
**Steps:**
1. Navigate through app
2. Check all text for:
   - "keyboard_arrow_right"
   - "keyboard_arrow_left"
   - Other icon names
3. Check responses for garbled characters

**Expected:** No icon names or garbled text

#### UI_019: No Overlapping Elements
**Steps:**
1. Check expanders and collapsible sections
2. Verify labels don't overlap
3. Check header elements
4. Check message alignment

**Expected:** No overlapping elements

#### UI_020: Proper Spacing
**Steps:**
1. Check spacing between:
   - Messages
   - Sections in structured responses
   - Buttons and inputs
   - Header elements

**Expected:** Adequate spacing throughout

#### UI_021: Loading States
**Steps:**
1. Submit a question
2. Verify spinner appears with "🔍 Consultant is researching..."
3. Verify spinner disappears when response arrives

**Expected:** Loading spinner shows during processing

---

### Phase 3: Core Functionality Testing

#### CORE_001-CORE_005: Agent Workflow
Follow the workflow order tests from CRITICAL_001, but test with different question types.

#### CORE_006: Best Practices Questions
**Test Questions:**
- "How should I configure a Business Rule for auto-assignment?"
- "What's the best practice for client scripts on the Incident form?"
- "How do I implement proper ACL configuration?"

**Expected:** Agent provides best practice guidance

#### CORE_007: Troubleshooting Questions
**Test Questions:**
- "Why is my workflow not triggering?"
- "My scheduled job is failing, what could be wrong?"
- "Performance issue: report is taking 30 seconds to load"

**Expected:** Agent provides troubleshooting steps

#### CORE_010-CORE_011: File Upload
**Steps:**
1. Upload PDF file
2. Upload TXT file
3. Upload CSV file
4. Verify all process correctly
5. Check chunk counts

**Expected:** All file types upload and index correctly

#### CORE_012: Context Search
**Steps:**
1. Upload a document about Business Rules
2. Ask: "How should I create a Business Rule?"
3. Verify agent references uploaded document

**Expected:** Agent queries knowledge base and references user context

---

### Phase 4: Settings & Configuration

#### SETTINGS_001-SETTINGS_006: ServiceNow Connection
Follow steps from CRITICAL_006, but test:
- Instance name normalization (dev12345 → https://dev12345.service-now.com)
- Password persistence (leave empty, verify old password kept)
- Invalid credentials handling

#### SETTINGS_007-SETTINGS_010: Search Domains
**Steps:**
1. Navigate to Settings → Search Scope
2. View current domains
3. Add a new domain (e.g., "support.vendor.com")
4. Verify domain appears in list
5. Try adding invalid domain (should show error)
6. Remove a domain
7. Verify domain removed

**Expected:** Domain management works correctly

---

### Phase 5: Error Handling

#### ERROR_005: Empty Input
**Steps:**
1. Try to submit empty message
2. Verify message is ignored or shows error

**Expected:** Empty messages are handled gracefully

#### ERROR_009: Unsupported Format
**Steps:**
1. Try to upload .docx or .xlsx file
2. Verify error message appears

**Expected:** Unsupported formats are rejected with clear error

---

## Test Result Recording

After completing each test, update the test results using the framework:

```python
from test_execution_framework import TestExecutionFramework

framework = TestExecutionFramework()
framework.record_result(
    test_id="CRITICAL_001",
    category="Critical Path",
    name="Agent successfully searches public docs and user context",
    status="PASS",  # or "FAIL", "BLOCKED", "SKIP"
    notes="Tested successfully, workflow order verified",
    error_message=None  # if failed, include error details
)
```

Or use the command-line interface:
```bash
python -c "from test_execution_framework import TestExecutionFramework; f = TestExecutionFramework(); f.record_result('CRITICAL_001', 'Critical Path', 'Agent successfully searches...', 'PASS', 'Tested successfully')"
```

## Reporting Issues

When a test fails:
1. Take a screenshot (save to `screenshots/` directory)
2. Note the exact steps that led to failure
3. Record error message if any
4. Update test result with status="FAIL" and error details

## Test Priority

1. **Day 1:** Critical Path tests (must pass for alpha)
2. **Day 2:** Core Functionality tests
3. **Day 3:** Settings & Configuration tests
4. **Day 4:** Real-World Scenarios
5. **Day 5:** Edge Cases & Error Handling
6. **Ongoing:** Performance & Polish
