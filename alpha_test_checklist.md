# Alpha Testing Checklist - ServiceNow Consultant App

**Last Updated:** 2026-01-11 19:10:32

## UI/UX Testing

- ⏳ **Tab Navigation - Switch between Consultant, Knowledge Base, and Settings tabs**
  - Notes: Test case initialized from plan
- ✅ **Header Display - Verify header shows title, connection status, and Clear Chat button**
  - Notes: Code contains render_header function with Clear Chat button
- ✅ **Welcome Screen - Confirm welcome screen appears on fresh session**
  - Notes: Code checks for empty messages and shows welcome screen
- ⏳ **Responsive Design - Test on different screen sizes**
  - Notes: Test case initialized from plan
- ✅ **Clear Chat Button - Verify button clears chat history and resets session state**
  - Notes: Code contains clear chat functionality
- ✅ **Message Display - Verify user and assistant messages render correctly with avatars**
  - Notes: Code uses st.chat_message with avatar parameter
- ✅ **Structured Responses - Test first structured response shows all sections**
  - Notes: Code contains render_structured_response with all required sections
- ⏳ **Subsequent Responses - Verify subsequent responses show as regular chat**
  - Notes: Test case initialized from plan
- ⏳ **List Formatting - Test numbered lists and bullet points render correctly**
  - Notes: Test case initialized from plan
- ✅ **Source Removal - Confirm sources/URLs are removed from displayed content**
  - Notes: Code contains source/URL removal logic
- ✅ **Feedback Button - Verify thumbs down button appears only on final responses**
  - Notes: Code contains feedback button implementation
- ⏳ **Feedback Dialog - Test correction form opens, submits, and saves preferences**
  - Notes: Test case initialized from plan
- ✅ **Input Field - Verify chat input is visible and functional**
  - Notes: Code uses st.chat_input
- ✅ **Disabled During Processing - Confirm chat input is hidden/disabled when processing**
  - Notes: Code checks processing state before showing input
- ⏳ **Single Input Field - Verify only one chat input appears**
  - Notes: Test case initialized from plan
- ✅ **File Upload Button - Test paperclip button opens quick upload dialog**
  - Notes: Code contains file upload button and dialog
- ⏳ **Input Persistence - Verify input clears after submission**
  - Notes: Test case initialized from plan
- ✅ **No Garbled Text - Check for absence of icon names in text**
  - Notes: Code contains text cleaning logic for icon names
- ⏳ **No Overlapping Elements - Verify expander labels don't overlap**
  - Notes: Test case initialized from plan
- ⏳ **Proper Spacing - Confirm adequate spacing between sections and messages**
  - Notes: Test case initialized from plan
- ✅ **Loading States - Verify spinner shows during agent processing**
  - Notes: Code uses st.spinner for loading states

## Core Functionality

- ✅ **Phase 1 (Public Docs) - Verify agent starts by searching public ServiceNow documentation**
  - Notes: Code contains Phase 1 workflow for public docs
- ✅ **Phase 2 (User Context) - Confirm agent checks user's knowledge base after public docs**
  - Notes: Code contains Phase 2 workflow for user context
- ✅ **Phase 3 (Synthesis) - Verify structured response format with all sections**
  - Notes: Code contains Phase 3 synthesis with structured format
- ✅ **Phase 4 (Live Instance) - Test that agent asks permission before checking live instance**
  - Notes: Code contains Phase 4 with permission guard
- ⏳ **Workflow Order - Confirm phases execute in correct sequence**
  - Notes: Test case initialized from plan
- ⏳ **Best Practices Questions - Test questions about best practices**
  - Notes: Test case initialized from plan
- ⏳ **Troubleshooting Questions - Test troubleshooting scenarios**
  - Notes: Test case initialized from plan
- ⏳ **Architecture Questions - Test architecture-related queries**
  - Notes: Test case initialized from plan
- ⏳ **Technical Questions - Test technical implementation questions**
  - Notes: Test case initialized from plan
- ✅ **Upload Files - Test uploading PDF, TXT, and CSV files**
  - Notes: Code supports PDF, TXT, and CSV file uploads
- ✅ **File Processing - Verify files are chunked and indexed correctly**
  - Notes: Unit tests for knowledge base file processing are passing
- ⏳ **Context Search - Confirm agent queries user's knowledge base when relevant**
  - Notes: Test case initialized from plan
- ⏳ **Conflict Detection - Test questions where user's docs conflict with official best practices**
  - Notes: Test case initialized from plan
- ⏳ **No Context Found - Verify behavior when no relevant user context exists**
  - Notes: Test case initialized from plan
- ✅ **Save Preference - Test submitting correction via thumbs down button**
  - Notes: Code contains save preference functionality
- ⏳ **Preference Retrieval - Verify saved preferences appear in Knowledge Base tab**
  - Notes: Test case initialized from plan
- ⏳ **Preference Application - Test that agent applies learned preferences in subsequent questions**
  - Notes: Test case initialized from plan
- ⏳ **Delete Preference - Verify deletion of learned rules works correctly**
  - Notes: Test case initialized from plan

## Settings & Configuration

- ✅ **Instance Name Input - Test entering instance name (should save as full URL)**
  - Notes: Code contains instance name normalization
- ⏳ **Instance Display - Verify header shows only instance name (not full URL)**
  - Notes: Test case initialized from plan
- ✅ **Connection Test - Test successful connection with valid credentials**
  - Notes: Code contains connection test functionality
- ⏳ **Connection Failure - Test error handling for invalid credentials**
  - Notes: Test case initialized from plan
- ✅ **Save Settings - Verify credentials are saved and persisted**
  - Notes: Code contains save settings functionality
- ⏳ **Password Persistence - Test that leaving password empty keeps existing password**
  - Notes: Test case initialized from plan
- ⏳ **View Domains - Verify current domains are displayed**
  - Notes: Test case initialized from plan
- ✅ **Add Domain - Test adding new search domain**
  - Notes: Code contains add domain functionality
- ⏳ **Remove Domain - Test removing a domain**
  - Notes: Test case initialized from plan
- ⏳ **Domain Validation - Test adding invalid domain formats**
  - Notes: Test case initialized from plan
- ⏳ **Safety Level - Test changing safety level (strict/open)**
  - Notes: Test case initialized from plan
- ⏳ **Setting Persistence - Verify preferences are saved**
  - Notes: Test case initialized from plan

## Error Handling & Edge Cases

- ⏳ **Agent Initialization Failure - Test behavior when agent fails to initialize**
  - Notes: Test case initialized from plan
- ⏳ **API Errors - Test behavior when API calls fail**
  - Notes: Test case initialized from plan
- ⏳ **Empty Responses - Test handling when agent returns empty response**
  - Notes: Test case initialized from plan
- ⏳ **Malformed Responses - Test handling of unexpected response formats**
  - Notes: Test case initialized from plan
- ⏳ **Empty Input - Submit empty message (should be ignored)**
  - Notes: Test case initialized from plan
- ⏳ **Very Long Input - Test with very long questions (>1000 characters)**
  - Notes: Test case initialized from plan
- ⏳ **Special Characters - Test with special characters, emojis, unicode**
  - Notes: Test case initialized from plan
- ⏳ **Multiple Questions - Submit message with multiple questions**
  - Notes: Test case initialized from plan
- ⏳ **Unsupported Format - Try uploading unsupported file type**
  - Notes: Test case initialized from plan
- ⏳ **Very Large File - Test with large PDF (>10MB)**
  - Notes: Test case initialized from plan
- ⏳ **Empty File - Try uploading empty file**
  - Notes: Test case initialized from plan
- ⏳ **Corrupted File - Test with corrupted PDF**
  - Notes: Test case initialized from plan
- ⏳ **File with No Text - Test PDF with only images**
  - Notes: Test case initialized from plan
- ⏳ **Page Refresh - Test behavior after browser refresh**
  - Notes: Test case initialized from plan
- ⏳ **Multiple Tabs - Test opening app in multiple browser tabs**
  - Notes: Test case initialized from plan
- ⏳ **Session Timeout - Test behavior after extended inactivity**
  - Notes: Test case initialized from plan
- ⏳ **Clear Chat - Verify chat history clears but settings persist**
  - Notes: Test case initialized from plan

## Integration Testing

- ⏳ **Successful Search - Verify public docs search returns relevant results**
  - Notes: Test case initialized from plan
- ⏳ **No Results Found - Test query with no matching public documentation**
  - Notes: Test case initialized from plan
- ⏳ **API Failure - Test behavior when Tavily API is unavailable**
  - Notes: Test case initialized from plan
- ⏳ **Live Query with Permission - Test checking live instance after user confirms**
  - Notes: Test case initialized from plan
- ⏳ **Permission Denied - Test when user says 'no' to live instance check**
  - Notes: Test case initialized from plan
- ⏳ **Connection Timeout - Test handling of slow/unresponsive ServiceNow instance**
  - Notes: Test case initialized from plan
- ⏳ **Authentication Expiry - Test handling when ServiceNow session expires**
  - Notes: Test case initialized from plan
- ⏳ **Vector Search - Verify knowledge base search finds relevant chunks**
  - Notes: Test case initialized from plan
- ⏳ **Empty Knowledge Base - Test behavior with no uploaded files**
  - Notes: Test case initialized from plan
- ⏳ **Large Knowledge Base - Test with 10+ indexed files**
  - Notes: Test case initialized from plan
- ⏳ **Chunk Retrieval - Verify correct chunks are retrieved for queries**
  - Notes: Test case initialized from plan

## Performance Testing

- ⏳ **Simple Query - Measure response time for simple question (<30 seconds)**
  - Notes: Test case initialized from plan
- ⏳ **Complex Query - Measure response time for complex multi-phase query (<90 seconds)**
  - Notes: Test case initialized from plan
- ⏳ **With Knowledge Base - Test response time with knowledge base search**
  - Notes: Test case initialized from plan
- ⏳ **With Live Instance - Test response time when querying live instance**
  - Notes: Test case initialized from plan
- ⏳ **Message Rendering - Verify messages render quickly (<1 second)**
  - Notes: Test case initialized from plan
- ⏳ **Long Conversations - Test with 20+ message conversation (no slowdown)**
  - Notes: Test case initialized from plan
- ⏳ **File Upload - Test upload and processing time for typical files**
  - Notes: Test case initialized from plan

## Security & Privacy

- ⏳ **Password Security - Verify passwords are not logged or exposed**
  - Notes: Test case initialized from plan
- ⏳ **Instance Credentials - Confirm credentials are stored securely**
  - Notes: Test case initialized from plan
- ⏳ **File Content - Verify uploaded file content is handled securely**
  - Notes: Test case initialized from plan
- ⏳ **Session Data - Confirm no sensitive data in session state or URLs**
  - Notes: Test case initialized from plan
- ✅ **Live Instance Guard - Verify agent never calls check_live_instance without explicit permission**
  - Notes: Code contains permission guard for live instance
- ✅ **User Confirmation - Test that agent asks before accessing live instance**
  - Notes: Code asks for user confirmation before live instance access
- ⏳ **Safety Level - Verify safety level settings are respected**
  - Notes: Test case initialized from plan

## Real-World Scenarios

- ⏳ **New Developer Onboarding - Complete scenario workflow**
  - Notes: Test case initialized from plan
- ⏳ **Troubleshooting Production Issue - Complete scenario workflow**
  - Notes: Test case initialized from plan
- ⏳ **Best Practice Compliance Check - Complete scenario workflow**
  - Notes: Test case initialized from plan
- ⏳ **Multi-Turn Conversation - Complete scenario workflow**
  - Notes: Test case initialized from plan
- ⏳ **Configuration & Setup - Complete scenario workflow**
  - Notes: Test case initialized from plan
- ⏳ **Knowledge Base Management - Complete scenario workflow**
  - Notes: Test case initialized from plan

## Critical Path

- ⏳ **Agent successfully searches public docs and user context**
  - Notes: Test case initialized from plan
- ⏳ **Structured responses render correctly with all sections**
  - Notes: Test case initialized from plan
- ⏳ **Chat input is disabled during processing**
  - Notes: Test case initialized from plan
- ⏳ **Clear chat button works and resets state**
  - Notes: Test case initialized from plan
- ⏳ **File upload and indexing works**
  - Notes: Test case initialized from plan
- ⏳ **ServiceNow connection test works**
  - Notes: Test case initialized from plan
- ⏳ **Feedback mechanism saves preferences**
  - Notes: Test case initialized from plan
- ⏳ **No garbled text or UI glitches**
  - Notes: Test case initialized from plan
- ⏳ **Agent respects permission guards (never auto-calls live instance)**
  - Notes: Test case initialized from plan
