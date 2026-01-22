# Feature Request Template (TDD Approach)

## Feature Information

### Feature Name

**[Feature Name Here]**

### Feature Location

- [ ] Settings Frame
- [ ] Main Tracker Window
- [ ] Analysis Frame
- [ ] Completion Frame
- [ ] Other: ****\_\_\_****

### User Story

As a **[user type]**,  
I want **[goal/feature]**  
So that **[benefit/value]**.

**Example:**

> As a time tracker user,  
> I want to export all my data to CSV format  
> So that I can analyze my time patterns in Excel.

## Test Planning

### 1. UI/Button Tests

Create tests to verify user interface elements:

- [ ] Button/widget exists in the UI
- [ ] Button has correct text/label
- [ ] Button has a command/callback assigned
- [ ] Button is in the correct location
- [ ] Button is enabled/disabled appropriately

**Test file location:** `tests/test_[feature_name].py`

### 2. Function/Method Tests

Create tests to verify core functionality:

- [ ] Function/method exists
- [ ] Function has correct signature
- [ ] Function handles valid inputs correctly
- [ ] Function handles invalid inputs (error cases)
- [ ] Function returns expected output type
- [ ] Function has no side effects (if pure function)

### 3. Data Flow Tests

Create tests to verify data handling:

- [ ] Data is read from correct source
- [ ] Data is validated before processing
- [ ] Data is transformed correctly
- [ ] Data is saved to correct destination
- [ ] Data integrity is maintained
- [ ] Data handles special characters/edge cases

### 4. Integration Tests

Create tests to verify end-to-end functionality:

- [ ] Complete workflow works from start to finish
- [ ] Multiple components work together correctly
- [ ] Error handling works across components
- [ ] Performance is acceptable with realistic data

## Expected Test Categories

Check all that apply to this feature:

- [ ] **UI Tests** - Buttons, forms, displays
- [ ] **Data Tests** - Reading, writing, transforming data
- [ ] **File Tests** - File creation, reading, writing
- [ ] **Dialog Tests** - User dialogs, confirmations
- [ ] **Validation Tests** - Input validation, error checking
- [ ] **Format Tests** - Data format conversion
- [ ] **Integration Tests** - End-to-end workflows

## Specific Test Cases to Create

List specific test cases for this feature:

1. **Test:** [Name]  
   **Purpose:** [What it tests]  
   **Expected:** [Expected result]

2. **Test:** [Name]  
   **Purpose:** [What it tests]  
   **Expected:** [Expected result]

3. **Test:** [Name]  
   **Purpose:** [What it tests]  
   **Expected:** [Expected result]

**Example for CSV Export:**

1. **Test:** `test_csv_export_button_exists`  
   **Purpose:** Verify export button is in settings UI  
   **Expected:** Button found with text "Save All Data to CSV"

2. **Test:** `test_export_function_exists`  
   **Purpose:** Verify export function is available  
   **Expected:** SettingsFrame has save_all_data_to_csv method

3. **Test:** `test_csv_file_created`  
   **Purpose:** Verify CSV file is created  
   **Expected:** File exists and has .csv extension

## Implementation Checklist

### Phase 1: RED (Write Failing Tests)

- [ ] Create test file: `tests/test_[feature_name].py`
- [ ] Import necessary test utilities from `test_helpers.py`
- [ ] Create test class(es) with descriptive names
- [ ] Write all test methods (should fail initially)
- [ ] Run tests: `python -m unittest tests.test_[feature_name] -v`
- [ ] **Verify all tests FAIL** (expected at this stage)
- [ ] Document any tests that unexpectedly pass

### Phase 2: GREEN (Implement to Pass Tests)

- [ ] Identify which file(s) to modify
- [ ] Add minimal code to make first test pass
- [ ] Run tests after each small change
- [ ] Continue until all tests pass
- [ ] **Verify all tests PASS**
- [ ] Document any tests that unexpectedly fail

### Phase 3: REFACTOR (Improve Code)

- [ ] Review code for clarity
- [ ] Add comments and docstrings
- [ ] Improve variable names
- [ ] Extract repeated code into functions
- [ ] Optimize performance if needed
- [ ] Run tests again
- [ ] **Verify tests STILL PASS** after refactoring

### Phase 4: Documentation

- [ ] Add feature to README.md
- [ ] Create/update user documentation
- [ ] Add code comments
- [ ] Document any edge cases
- [ ] Update CHANGELOG (if applicable)

## Test Review Questions

Before implementing, answer these questions:

### Test Coverage

1. **Are all major behaviors tested?**
   - [ ] Yes
   - [ ] No - Missing: ****\_\_\_****

2. **Are edge cases covered?**
   - [ ] Empty data
   - [ ] Invalid data
   - [ ] Large datasets
   - [ ] Special characters
   - [ ] Missing files
   - [ ] Other: ****\_\_\_****

3. **Are error conditions tested?**
   - [ ] File not found
   - [ ] Permission denied
   - [ ] Invalid format
   - [ ] Network errors (if applicable)
   - [ ] Other: ****\_\_\_****

### Test Quality

1. **Are tests independent?**
   - [ ] Yes - Each test can run alone
   - [ ] No - Some tests depend on others

2. **Are tests fast?**
   - [ ] Yes - Complete in < 1 second each
   - [ ] No - Some are slow because: ****\_\_\_****

3. **Are test names descriptive?**
   - [ ] Yes - Clear what each test does
   - [ ] No - Need to improve names

## Unnecessary Tests?

Review your test list. Are any tests:

- [ ] **Redundant** - Testing the same thing as another test
- [ ] **Too granular** - Testing trivial implementation details
- [ ] **Too broad** - Testing multiple things at once
- [ ] **Implementation-specific** - Will break if code structure changes

**If yes, list which tests and why:**

---

## Additional Tests Needed?

After reviewing the test plan, are additional tests needed for:

- [ ] **Security** - Input sanitization, injection prevention
- [ ] **Performance** - Speed with large datasets
- [ ] **Concurrency** - Multiple simultaneous operations
- [ ] **Compatibility** - Different OS, Python versions
- [ ] **Accessibility** - Keyboard navigation, screen readers
- [ ] **Localization** - Different languages/character sets

**Specific additional tests:**

---

## TDD Workflow Execution

### Step 1: Run Tests (Should FAIL)

```bash
python -m unittest tests.test_[feature_name] -v
```

**Expected output:** FAILED (X tests)

**Actual output:**

```
[Paste output here]
```

### Step 2: Implement Feature

**Files modified:**

1. [filename.py] - [what was added/changed]
2. [filename.py] - [what was added/changed]

### Step 3: Run Tests (Should PASS)

```bash
python -m unittest tests.test_[feature_name] -v
```

**Expected output:** OK (X tests passed)

**Actual output:**

```
[Paste output here]
```

### Step 4: Run All Tests (Ensure No Regression)

```bash
python -m unittest discover tests -v
```

**Result:**

- [ ] All tests pass
- [ ] Some tests fail - List: ****\_\_\_****

## Success Criteria

Feature is complete when:

- [ ] All planned tests are written
- [ ] All tests initially failed (RED phase verified)
- [ ] All tests now pass (GREEN phase verified)
- [ ] Code has been refactored and tests still pass
- [ ] Integration test(s) pass
- [ ] No regression in existing tests
- [ ] Documentation is updated
- [ ] Code is committed to version control

## Example: Completed Template

See `CSV_EXPORT_IMPLEMENTATION.md` for a complete example of this template filled out for the CSV export feature.

---

## How to Use This Template

1. **Copy this template** to a new file when planning a feature
2. **Fill out all sections** before writing any code
3. **Use as checklist** during implementation
4. **Keep updated** as you discover new test cases
5. **Reference** when reviewing or debugging

## Tips for Success

- **Start small** - Begin with simplest test case
- **One test at a time** - Write test, make it pass, move on
- **Keep tests simple** - Test one thing per test method
- **Run tests frequently** - After every small change
- **Don't skip RED phase** - Always verify tests fail first
- **Refactor confidently** - Tests protect you from breaking things

---

**Remember:** The goal of TDD is not just passing tests, but having confidence that your code works correctly and will continue to work as you make changes.
