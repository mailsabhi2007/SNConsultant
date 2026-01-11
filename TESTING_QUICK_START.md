# Quick Start Guide - Alpha Testing

## 🚀 Getting Started

### 1. Initialize Test Framework (Already Done ✅)
The test framework has been initialized with all 108 test cases from the alpha testing plan.

### 2. View Current Status
```bash
# View the test report
cat alpha_test_report.txt

# Or view the checklist
cat alpha_test_checklist.md
```

### 3. Start Manual Testing

#### Option A: Use the Manual Testing Guide
1. Open `manual_testing_guide.md`
2. Follow step-by-step instructions for each test
3. Update results after each test (see below)

#### Option B: Start with Critical Path Tests
These 9 tests MUST pass for alpha release:
- CRITICAL_001 through CRITICAL_009

See `manual_testing_guide.md` section "Phase 1: Critical Path Testing"

### 4. Update Test Results

After completing a test, update the result:

```python
from test_execution_framework import TestExecutionFramework

framework = TestExecutionFramework()

# Record a passing test
framework.record_result(
    test_id="CRITICAL_001",
    category="Critical Path",
    name="Agent successfully searches public docs and user context",
    status="PASS",
    notes="Tested successfully - workflow order verified"
)

# Record a failing test
framework.record_result(
    test_id="CRITICAL_002",
    category="Critical Path",
    name="Structured responses render correctly with all sections",
    status="FAIL",
    notes="Missing 'Analysis' section in response",
    error_message="Response only showed 3 of 4 required sections"
)
```

### 5. Generate Updated Reports
```bash
python test_execution_framework.py
```

This will:
- Update `alpha_test_report.txt`
- Update `alpha_test_checklist.md`
- Save results to `alpha_test_results.json`

## 📊 Current Status

**25/108 tests verified** (23.1%)
- ✅ 11 UI/UX features verified in code
- ✅ 6 Core functionality features verified
- ✅ 4 Settings features verified
- ✅ 2 Security features verified
- ⏳ 83 tests require manual testing

## 🎯 Priority Testing Order

1. **Critical Path (9 tests)** - Day 1 - MUST PASS
2. **Core Functionality (12 remaining)** - Day 2
3. **Settings & Configuration (8 remaining)** - Day 3
4. **Real-World Scenarios (6 tests)** - Day 4
5. **Error Handling & Edge Cases (17 tests)** - Day 5
6. **Performance & Polish (7 tests)** - Ongoing

## 🔧 Running the App for Testing

```bash
# Start Streamlit app
streamlit run streamlit_app.py

# App will open in browser at http://localhost:8501
```

## 📝 Test Result Status Codes

- **PASS** ✅ - Test passed
- **FAIL** ❌ - Test failed (include error details)
- **BLOCKED** 🚫 - Test blocked by another issue
- **SKIP** ⏭️ - Test skipped (not applicable)
- **PENDING** ⏳ - Test not yet executed

## 🐛 Reporting Issues

When a test fails:
1. Take a screenshot (save to `screenshots/` directory)
2. Note exact steps that led to failure
3. Record error message
4. Update test result with `status="FAIL"` and error details

## 📚 Documentation Files

- **ALPHA_TESTING_SUMMARY.md** - Overall testing summary
- **manual_testing_guide.md** - Detailed manual testing instructions
- **alpha_test_report.txt** - Current test status report
- **alpha_test_checklist.md** - Markdown checklist
- **alpha_test_results.json** - Machine-readable results

## ⚡ Quick Commands

```bash
# Run automated verification (updates code-verified tests)
python run_automated_verifications.py

# Run existing pytest suite
pytest tests/ -v

# Generate fresh reports
python test_execution_framework.py

# View test report
cat alpha_test_report.txt | less
```

## 🎓 Example: Testing a Critical Path Test

1. **Start the app:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Test CRITICAL_001:**
   - Navigate to Consultant tab
   - Ask: "How should I configure a Business Rule for auto-assignment?"
   - Observe the "Research Process" section
   - Verify Phase 1 appears first, Phase 2 second, Phase 3 last

3. **Record result:**
   ```python
   from test_execution_framework import TestExecutionFramework
   f = TestExecutionFramework()
   f.record_result("CRITICAL_001", "Critical Path", 
                  "Agent successfully searches public docs and user context",
                  "PASS", "Workflow order verified correctly")
   ```

4. **Generate updated report:**
   ```bash
   python test_execution_framework.py
   ```

## 💡 Tips

1. **Test in order** - Critical Path tests first
2. **Document everything** - Include screenshots for failures
3. **Update frequently** - Run the framework after each test session
4. **Check existing tests** - Some functionality may already be tested
5. **Use the guide** - `manual_testing_guide.md` has detailed steps

## 🎯 Success Criteria for Alpha

- ✅ All 9 Critical Path tests PASS
- ✅ 80%+ of Core Functionality tests PASS
- ✅ 80%+ of UI/UX tests PASS
- ✅ All Security tests PASS
- ✅ 70%+ overall test coverage

---

**Ready to start?** Begin with `manual_testing_guide.md` → "Phase 1: Critical Path Testing"
