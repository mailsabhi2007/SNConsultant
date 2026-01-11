"""
Alpha Testing Execution Framework for ServiceNow Consultant App

This script provides automated testing capabilities and test result tracking
for the comprehensive alpha testing plan.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pytest


class TestResult:
    """Represents a single test result."""
    
    def __init__(self, test_id: str, category: str, name: str):
        self.test_id = test_id
        self.category = category
        self.name = name
        self.status: Optional[str] = None  # "PASS", "FAIL", "BLOCKED", "SKIP"
        self.notes: str = ""
        self.screenshot_path: Optional[str] = None
        self.error_message: Optional[str] = None
        self.timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_id": self.test_id,
            "category": self.category,
            "name": self.name,
            "status": self.status,
            "notes": self.notes,
            "screenshot_path": self.screenshot_path,
            "error_message": self.error_message,
            "timestamp": self.timestamp
        }


class TestExecutionFramework:
    """Framework for executing and tracking alpha tests."""
    
    def __init__(self, results_file: str = "alpha_test_results.json"):
        self.results_file = results_file
        self.results: Dict[str, TestResult] = {}
        self.load_results()
    
    def load_results(self):
        """Load existing test results from file."""
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r') as f:
                    data = json.load(f)
                    for test_id, test_data in data.items():
                        result = TestResult(
                            test_data['test_id'],
                            test_data['category'],
                            test_data['name']
                        )
                        result.status = test_data.get('status')
                        result.notes = test_data.get('notes', '')
                        result.screenshot_path = test_data.get('screenshot_path')
                        result.error_message = test_data.get('error_message')
                        result.timestamp = test_data.get('timestamp')
                        self.results[test_id] = result
            except Exception as e:
                print(f"Error loading results: {e}")
    
    def save_results(self):
        """Save test results to file."""
        data = {test_id: result.to_dict() for test_id, result in self.results.items()}
        with open(self.results_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_result(self, test_id: str, category: str, name: str, 
                     status: str, notes: str = "", error_message: str = None):
        """Record a test result."""
        if test_id not in self.results:
            self.results[test_id] = TestResult(test_id, category, name)
        
        result = self.results[test_id]
        result.status = status
        result.notes = notes
        result.error_message = error_message
        result.timestamp = datetime.now().isoformat()
        self.save_results()
    
    def run_automated_tests(self) -> Dict[str, int]:
        """Run pytest suite and return summary."""
        print("Running automated test suite...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            # Parse output for summary
            output = result.stdout + result.stderr
            passed = output.count("PASSED")
            failed = output.count("FAILED")
            errors = output.count("ERROR")
            skipped = output.count("SKIPPED")
            
            return {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "total": passed + failed + errors + skipped,
                "exit_code": result.returncode
            }
        except Exception as e:
            print(f"Error running tests: {e}")
            return {"error": str(e)}
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("=" * 80)
        report.append("ALPHA TESTING REPORT - ServiceNow Consultant App")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary by category
        categories = {}
        status_counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIP": 0, "PENDING": 0}
        
        for result in self.results.values():
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
            
            if result.status:
                status_counts[result.status] = status_counts.get(result.status, 0) + 1
            else:
                status_counts["PENDING"] += 1
        
        # Overall summary
        report.append("OVERALL SUMMARY")
        report.append("-" * 80)
        total = len(self.results)
        for status, count in status_counts.items():
            if count > 0:
                percentage = (count / total * 100) if total > 0 else 0
                report.append(f"  {status}: {count} ({percentage:.1f}%)")
        report.append(f"  Total Tests: {total}")
        report.append("")
        
        # Results by category
        for category, tests in sorted(categories.items()):
            report.append(f"{category.upper()}")
            report.append("-" * 80)
            for test in sorted(tests, key=lambda x: x.test_id):
                status = test.status or "PENDING"
                report.append(f"  [{status}] {test.test_id}: {test.name}")
                if test.notes:
                    report.append(f"      Notes: {test.notes}")
                if test.error_message:
                    report.append(f"      Error: {test.error_message}")
            report.append("")
        
        return "\n".join(report)
    
    def export_checklist(self, output_file: str = "alpha_test_checklist.md"):
        """Export test checklist in markdown format matching the plan."""
        checklist = []
        checklist.append("# Alpha Testing Checklist - ServiceNow Consultant App")
        checklist.append("")
        checklist.append(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        checklist.append("")
        
        # Group by category from the plan
        categories = {
            "UI/UX Testing": [],
            "Core Functionality": [],
            "Settings & Configuration": [],
            "Error Handling & Edge Cases": [],
            "Integration Testing": [],
            "Performance Testing": [],
            "Security & Privacy": [],
            "Real-World Scenarios": [],
            "Critical Path": []
        }
        
        for result in self.results.values():
            # Map to plan categories
            if "UI" in result.category or "UX" in result.category:
                categories["UI/UX Testing"].append(result)
            elif "Core" in result.category or "Functionality" in result.category:
                categories["Core Functionality"].append(result)
            elif "Settings" in result.category or "Configuration" in result.category:
                categories["Settings & Configuration"].append(result)
            elif "Error" in result.category or "Edge" in result.category:
                categories["Error Handling & Edge Cases"].append(result)
            elif "Integration" in result.category:
                categories["Integration Testing"].append(result)
            elif "Performance" in result.category:
                categories["Performance Testing"].append(result)
            elif "Security" in result.category or "Privacy" in result.category:
                categories["Security & Privacy"].append(result)
            elif "Scenario" in result.category or "Real-World" in result.category:
                categories["Real-World Scenarios"].append(result)
            elif "Critical" in result.category:
                categories["Critical Path"].append(result)
            else:
                categories["Core Functionality"].append(result)
        
        for category_name, tests in categories.items():
            if not tests:
                continue
                
            checklist.append(f"## {category_name}")
            checklist.append("")
            
            for test in sorted(tests, key=lambda x: x.test_id):
                status_icon = {
                    "PASS": "✅",
                    "FAIL": "❌",
                    "BLOCKED": "🚫",
                    "SKIP": "⏭️",
                    "PENDING": "⏳"
                }.get(test.status, "⏳")
                
                checklist.append(f"- {status_icon} **{test.name}**")
                if test.notes:
                    checklist.append(f"  - Notes: {test.notes}")
                if test.error_message:
                    checklist.append(f"  - Error: {test.error_message}")
            checklist.append("")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(checklist))
        
        print(f"Checklist exported to {output_file}")


def initialize_test_cases_from_plan(framework: TestExecutionFramework):
    """Initialize test cases from the alpha testing plan."""
    
    # UI/UX Testing
    ui_tests = [
        ("UI_001", "UI/UX", "Tab Navigation - Switch between Consultant, Knowledge Base, and Settings tabs"),
        ("UI_002", "UI/UX", "Header Display - Verify header shows title, connection status, and Clear Chat button"),
        ("UI_003", "UI/UX", "Welcome Screen - Confirm welcome screen appears on fresh session"),
        ("UI_004", "UI/UX", "Responsive Design - Test on different screen sizes"),
        ("UI_005", "UI/UX", "Clear Chat Button - Verify button clears chat history and resets session state"),
        ("UI_006", "UI/UX", "Message Display - Verify user and assistant messages render correctly with avatars"),
        ("UI_007", "UI/UX", "Structured Responses - Test first structured response shows all sections"),
        ("UI_008", "UI/UX", "Subsequent Responses - Verify subsequent responses show as regular chat"),
        ("UI_009", "UI/UX", "List Formatting - Test numbered lists and bullet points render correctly"),
        ("UI_010", "UI/UX", "Source Removal - Confirm sources/URLs are removed from displayed content"),
        ("UI_011", "UI/UX", "Feedback Button - Verify thumbs down button appears only on final responses"),
        ("UI_012", "UI/UX", "Feedback Dialog - Test correction form opens, submits, and saves preferences"),
        ("UI_013", "UI/UX", "Input Field - Verify chat input is visible and functional"),
        ("UI_014", "UI/UX", "Disabled During Processing - Confirm chat input is hidden/disabled when processing"),
        ("UI_015", "UI/UX", "Single Input Field - Verify only one chat input appears"),
        ("UI_016", "UI/UX", "File Upload Button - Test paperclip button opens quick upload dialog"),
        ("UI_017", "UI/UX", "Input Persistence - Verify input clears after submission"),
        ("UI_018", "UI/UX", "No Garbled Text - Check for absence of icon names in text"),
        ("UI_019", "UI/UX", "No Overlapping Elements - Verify expander labels don't overlap"),
        ("UI_020", "UI/UX", "Proper Spacing - Confirm adequate spacing between sections and messages"),
        ("UI_021", "UI/UX", "Loading States - Verify spinner shows during agent processing"),
    ]
    
    # Core Functionality
    core_tests = [
        ("CORE_001", "Core Functionality", "Phase 1 (Public Docs) - Verify agent starts by searching public ServiceNow documentation"),
        ("CORE_002", "Core Functionality", "Phase 2 (User Context) - Confirm agent checks user's knowledge base after public docs"),
        ("CORE_003", "Core Functionality", "Phase 3 (Synthesis) - Verify structured response format with all sections"),
        ("CORE_004", "Core Functionality", "Phase 4 (Live Instance) - Test that agent asks permission before checking live instance"),
        ("CORE_005", "Core Functionality", "Workflow Order - Confirm phases execute in correct sequence"),
        ("CORE_006", "Core Functionality", "Best Practices Questions - Test questions about best practices"),
        ("CORE_007", "Core Functionality", "Troubleshooting Questions - Test troubleshooting scenarios"),
        ("CORE_008", "Core Functionality", "Architecture Questions - Test architecture-related queries"),
        ("CORE_009", "Core Functionality", "Technical Questions - Test technical implementation questions"),
        ("CORE_010", "Core Functionality", "Upload Files - Test uploading PDF, TXT, and CSV files"),
        ("CORE_011", "Core Functionality", "File Processing - Verify files are chunked and indexed correctly"),
        ("CORE_012", "Core Functionality", "Context Search - Confirm agent queries user's knowledge base when relevant"),
        ("CORE_013", "Core Functionality", "Conflict Detection - Test questions where user's docs conflict with official best practices"),
        ("CORE_014", "Core Functionality", "No Context Found - Verify behavior when no relevant user context exists"),
        ("CORE_015", "Core Functionality", "Save Preference - Test submitting correction via thumbs down button"),
        ("CORE_016", "Core Functionality", "Preference Retrieval - Verify saved preferences appear in Knowledge Base tab"),
        ("CORE_017", "Core Functionality", "Preference Application - Test that agent applies learned preferences in subsequent questions"),
        ("CORE_018", "Core Functionality", "Delete Preference - Verify deletion of learned rules works correctly"),
    ]
    
    # Settings & Configuration
    settings_tests = [
        ("SETTINGS_001", "Settings", "Instance Name Input - Test entering instance name (should save as full URL)"),
        ("SETTINGS_002", "Settings", "Instance Display - Verify header shows only instance name (not full URL)"),
        ("SETTINGS_003", "Settings", "Connection Test - Test successful connection with valid credentials"),
        ("SETTINGS_004", "Settings", "Connection Failure - Test error handling for invalid credentials"),
        ("SETTINGS_005", "Settings", "Save Settings - Verify credentials are saved and persisted"),
        ("SETTINGS_006", "Settings", "Password Persistence - Test that leaving password empty keeps existing password"),
        ("SETTINGS_007", "Settings", "View Domains - Verify current domains are displayed"),
        ("SETTINGS_008", "Settings", "Add Domain - Test adding new search domain"),
        ("SETTINGS_009", "Settings", "Remove Domain - Test removing a domain"),
        ("SETTINGS_010", "Settings", "Domain Validation - Test adding invalid domain formats"),
        ("SETTINGS_011", "Settings", "Safety Level - Test changing safety level (strict/open)"),
        ("SETTINGS_012", "Settings", "Setting Persistence - Verify preferences are saved"),
    ]
    
    # Error Handling & Edge Cases
    error_tests = [
        ("ERROR_001", "Error Handling", "Agent Initialization Failure - Test behavior when agent fails to initialize"),
        ("ERROR_002", "Error Handling", "API Errors - Test behavior when API calls fail"),
        ("ERROR_003", "Error Handling", "Empty Responses - Test handling when agent returns empty response"),
        ("ERROR_004", "Error Handling", "Malformed Responses - Test handling of unexpected response formats"),
        ("ERROR_005", "Error Handling", "Empty Input - Submit empty message (should be ignored)"),
        ("ERROR_006", "Error Handling", "Very Long Input - Test with very long questions (>1000 characters)"),
        ("ERROR_007", "Error Handling", "Special Characters - Test with special characters, emojis, unicode"),
        ("ERROR_008", "Error Handling", "Multiple Questions - Submit message with multiple questions"),
        ("ERROR_009", "Error Handling", "Unsupported Format - Try uploading unsupported file type"),
        ("ERROR_010", "Error Handling", "Very Large File - Test with large PDF (>10MB)"),
        ("ERROR_011", "Error Handling", "Empty File - Try uploading empty file"),
        ("ERROR_012", "Error Handling", "Corrupted File - Test with corrupted PDF"),
        ("ERROR_013", "Error Handling", "File with No Text - Test PDF with only images"),
        ("ERROR_014", "Error Handling", "Page Refresh - Test behavior after browser refresh"),
        ("ERROR_015", "Error Handling", "Multiple Tabs - Test opening app in multiple browser tabs"),
        ("ERROR_016", "Error Handling", "Session Timeout - Test behavior after extended inactivity"),
        ("ERROR_017", "Error Handling", "Clear Chat - Verify chat history clears but settings persist"),
    ]
    
    # Integration Testing
    integration_tests = [
        ("INT_001", "Integration", "Successful Search - Verify public docs search returns relevant results"),
        ("INT_002", "Integration", "No Results Found - Test query with no matching public documentation"),
        ("INT_003", "Integration", "API Failure - Test behavior when Tavily API is unavailable"),
        ("INT_004", "Integration", "Live Query with Permission - Test checking live instance after user confirms"),
        ("INT_005", "Integration", "Permission Denied - Test when user says 'no' to live instance check"),
        ("INT_006", "Integration", "Connection Timeout - Test handling of slow/unresponsive ServiceNow instance"),
        ("INT_007", "Integration", "Authentication Expiry - Test handling when ServiceNow session expires"),
        ("INT_008", "Integration", "Vector Search - Verify knowledge base search finds relevant chunks"),
        ("INT_009", "Integration", "Empty Knowledge Base - Test behavior with no uploaded files"),
        ("INT_010", "Integration", "Large Knowledge Base - Test with 10+ indexed files"),
        ("INT_011", "Integration", "Chunk Retrieval - Verify correct chunks are retrieved for queries"),
    ]
    
    # Performance Testing
    perf_tests = [
        ("PERF_001", "Performance", "Simple Query - Measure response time for simple question (<30 seconds)"),
        ("PERF_002", "Performance", "Complex Query - Measure response time for complex multi-phase query (<90 seconds)"),
        ("PERF_003", "Performance", "With Knowledge Base - Test response time with knowledge base search"),
        ("PERF_004", "Performance", "With Live Instance - Test response time when querying live instance"),
        ("PERF_005", "Performance", "Message Rendering - Verify messages render quickly (<1 second)"),
        ("PERF_006", "Performance", "Long Conversations - Test with 20+ message conversation (no slowdown)"),
        ("PERF_007", "Performance", "File Upload - Test upload and processing time for typical files"),
    ]
    
    # Security & Privacy
    security_tests = [
        ("SEC_001", "Security", "Password Security - Verify passwords are not logged or exposed"),
        ("SEC_002", "Security", "Instance Credentials - Confirm credentials are stored securely"),
        ("SEC_003", "Security", "File Content - Verify uploaded file content is handled securely"),
        ("SEC_004", "Security", "Session Data - Confirm no sensitive data in session state or URLs"),
        ("SEC_005", "Security", "Live Instance Guard - Verify agent never calls check_live_instance without explicit permission"),
        ("SEC_006", "Security", "User Confirmation - Test that agent asks before accessing live instance"),
        ("SEC_007", "Security", "Safety Level - Verify safety level settings are respected"),
    ]
    
    # Real-World Scenarios
    scenario_tests = [
        ("SCENARIO_001", "Real-World", "New Developer Onboarding - Complete scenario workflow"),
        ("SCENARIO_002", "Real-World", "Troubleshooting Production Issue - Complete scenario workflow"),
        ("SCENARIO_003", "Real-World", "Best Practice Compliance Check - Complete scenario workflow"),
        ("SCENARIO_004", "Real-World", "Multi-Turn Conversation - Complete scenario workflow"),
        ("SCENARIO_005", "Real-World", "Configuration & Setup - Complete scenario workflow"),
        ("SCENARIO_006", "Real-World", "Knowledge Base Management - Complete scenario workflow"),
    ]
    
    # Critical Path
    critical_tests = [
        ("CRITICAL_001", "Critical Path", "Agent successfully searches public docs and user context"),
        ("CRITICAL_002", "Critical Path", "Structured responses render correctly with all sections"),
        ("CRITICAL_003", "Critical Path", "Chat input is disabled during processing"),
        ("CRITICAL_004", "Critical Path", "Clear chat button works and resets state"),
        ("CRITICAL_005", "Critical Path", "File upload and indexing works"),
        ("CRITICAL_006", "Critical Path", "ServiceNow connection test works"),
        ("CRITICAL_007", "Critical Path", "Feedback mechanism saves preferences"),
        ("CRITICAL_008", "Critical Path", "No garbled text or UI glitches"),
        ("CRITICAL_009", "Critical Path", "Agent respects permission guards (never auto-calls live instance)"),
    ]
    
    # Initialize all test cases
    all_tests = (ui_tests + core_tests + settings_tests + error_tests + 
                 integration_tests + perf_tests + security_tests + 
                 scenario_tests + critical_tests)
    
    for test_id, category, name in all_tests:
        if test_id not in framework.results:
            framework.record_result(test_id, category, name, "PENDING", 
                                  "Test case initialized from plan")
    
    print(f"Initialized {len(all_tests)} test cases from alpha testing plan")


if __name__ == "__main__":
    framework = TestExecutionFramework()
    
    print("Alpha Testing Framework for ServiceNow Consultant App")
    print("=" * 80)
    print()
    
    # Initialize test cases from plan
    print("Initializing test cases from alpha testing plan...")
    initialize_test_cases_from_plan(framework)
    print()
    
    # Run automated tests
    print("Running automated test suite...")
    test_summary = framework.run_automated_tests()
    print(f"Test Summary: {test_summary}")
    print()
    
    # Generate report
    print("Generating test report...")
    report = framework.generate_report()
    print(report)
    
    # Save report to file
    with open("alpha_test_report.txt", "w") as f:
        f.write(report)
    print("\nReport saved to alpha_test_report.txt")
    
    # Export checklist
    framework.export_checklist()
    
    print("\nFramework ready for manual testing. Use framework.record_result() to update test status.")
