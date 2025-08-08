# Example Issue for Code Generation

Copy and paste this into a new GitHub issue to start generating code:

---

## Title: [GENERATE] Phase 1 Week 1 - Data Preprocessing Pipeline

## Body:

### Component to Generate
Data preprocessing pipeline for CFPB complaints (Phase 1, Week 1)

### Specification References
- Architecture: `specs/ARCHITECTURE.md#1-input-processing-layer`
- Technical Stack: `specs/TECHNICAL_STACK.md`
- Implementation Phase: `specs/IMPLEMENTATION_PLAN.md#week-1-environment-setup--data-preparation`

### Requirements
- [x] Follow exact specification structure
- [x] Include comprehensive unit tests
- [x] Add inline documentation
- [x] Create usage examples
- [x] Implement error handling

### Claude Generation Request

@claude Based on the specifications listed above, please generate the Phase 1 Week 1 deliverables:

1. **Environment Setup** (`src/setup/`):
   - Create `requirements.txt` with all dependencies from specs/TECHNICAL_STACK.md
   - Create `setup.py` for package installation
   - Add `.env.example` for configuration

2. **Data Ingestion Module** (`src/input_processing/data_ingestion.py`):
   - CFPB complaint loader class
   - Support for CSV and JSON formats
   - Batch processing capabilities
   - Data validation and error handling

3. **Text Preprocessing Pipeline** (`src/input_processing/preprocessing.py`):
   - Text cleaning (remove HTML, special characters)
   - CFPB-specific normalizers (financial terms, product names)
   - Document chunking for long narratives
   - Tokenization using spaCy

4. **Tests** (`tests/test_input_processing.py`):
   - Unit tests for data ingestion
   - Tests for preprocessing functions
   - Edge cases and error handling tests
   - Mock CFPB data for testing

5. **Example Usage** (`examples/preprocessing_example.py`):
   - Complete example loading CFPB data
   - Demonstrating preprocessing pipeline
   - Sample output visualization

Please ensure:
- All code follows PEP 8 style guidelines
- Functions have comprehensive docstrings
- Error messages are informative
- Logging is implemented for debugging

Place the generated code in the appropriate directories as specified above.

### Validation Criteria
- [ ] Code matches specification structure
- [ ] All tests pass
- [ ] No linting errors
- [ ] Documentation complete
- [ ] Examples run successfully

---

## After Creating the Issue:

1. **Wait for Claude to respond** - Claude will create a PR with the generated code
2. **Check the PR** - Review the generated code in the pull request
3. **Test locally**:
   ```bash
   gh pr checkout [PR-NUMBER]
   pytest tests/test_input_processing.py
   python scripts/validate_spec_compliance.py
   ```
4. **Merge if satisfied**:
   ```bash
   gh pr merge [PR-NUMBER]
   ```

## Alternative Simpler Request:

For a simpler start, you can also just comment:

```
@claude Please generate the data preprocessing module from specs/IMPLEMENTATION_PLAN.md#week-1 with tests
```

Claude will understand the context and generate appropriate code.