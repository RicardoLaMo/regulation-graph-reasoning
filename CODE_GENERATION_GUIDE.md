# Code Generation Guide

## Overview
This guide explains how to use Claude GitHub Bot to generate, test, and validate code from specification documents.

## Complete Workflow

### 1. Repository Structure
```
regulation-graph-reasoning/
├── .github/
│   ├── workflows/          # GitHub Actions
│   │   ├── claude-code.yml # Claude bot configuration
│   │   └── test-generated-code.yml # Auto-testing
│   └── ISSUE_TEMPLATE/     # Issue templates
│       ├── generate-code.md
│       └── validate-spec.md
├── specs/                  # Technical specifications
│   ├── ARCHITECTURE.md
│   ├── TECHNICAL_STACK.md
│   └── IMPLEMENTATION_PLAN.md
├── src/                    # Generated source code
├── tests/                  # Test files
├── scripts/                # Utility scripts
│   └── validate_spec_compliance.py
└── docs/                   # Documentation
```

### 2. Code Generation Process

#### Step 1: Create a GitHub Issue
Use the "Generate Code from Specs" template or create manually:

```markdown
Title: [GENERATE] Input Processing Module

@claude Based on specs/ARCHITECTURE.md#input-processing-layer, please generate:
1. Text preprocessing module in src/input_processing/
2. Unit tests in tests/test_input_processing.py
3. Example usage in examples/input_processing_example.py

Requirements:
- Follow the exact architecture specification
- Use spaCy as specified in specs/TECHNICAL_STACK.md
- Include CFPB-specific text normalizers
- Add comprehensive error handling
```

#### Step 2: Claude Creates Pull Request
Claude will:
1. Read the referenced specifications
2. Generate code following the specs
3. Create a PR with the changes
4. Include tests and documentation

#### Step 3: Automated Testing
When PR is created, GitHub Actions automatically:
1. Run Python tests (pytest)
2. Check code formatting (black, flake8)
3. Validate against specifications
4. Post results as PR comment

#### Step 4: Local Testing (Optional)
```bash
# Fetch and checkout the PR
gh pr checkout [PR-NUMBER]
# OR
git fetch origin pull/[PR-NUMBER]/head:pr-[NUMBER]
git checkout pr-[NUMBER]

# Run tests locally
python -m pytest tests/
python scripts/validate_spec_compliance.py

# Check code quality
black src/
flake8 src/
mypy src/
```

### 3. Progressive Implementation Strategy

Follow the phases defined in `specs/IMPLEMENTATION_PLAN.md`:

#### Phase 1: Foundation (Weeks 1-4)
```markdown
Issue 1: @claude Generate Week 1 deliverables from specs/IMPLEMENTATION_PLAN.md#week-1
Issue 2: @claude Generate Week 2 product classification from specs/IMPLEMENTATION_PLAN.md#week-2
```

#### Phase 2: Advanced Features
```markdown
Issue: @claude Implement knowledge graph from specs/ARCHITECTURE.md#knowledge-representation-layer
```

### 4. Validation Workflow

#### Automatic Validation
Every PR triggers validation against specs:
```bash
python scripts/validate_spec_compliance.py
```

This checks:
- ✅ Project structure compliance
- ✅ Module organization
- ✅ Required dependencies
- ✅ Test coverage
- ⚠️ Warnings for missing components
- ❌ Errors for spec violations

#### Manual Validation Request
Create issue with "Validate Code Against Specs" template:
```markdown
@claude Please validate src/classification/ against specs/ARCHITECTURE.md#classification
```

### 5. Testing Strategy

#### Automated Tests (GitHub Actions)
- Runs on every PR to `src/` or `tests/`
- Tests Python 3.9, 3.10, 3.11
- Generates coverage reports
- Posts results to PR

#### Local Testing Commands
```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_input_processing.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Validate specifications
python scripts/validate_spec_compliance.py
```

### 6. Best Practices

#### For Code Generation
1. **One Component at a Time**: Generate incrementally
2. **Reference Specific Specs**: Use section anchors (#section-name)
3. **Include Tests**: Always request tests with code
4. **Verify First**: Run validation before merging

#### For Testing
1. **Test Locally First**: Pull PR and test before merging
2. **Check CI Status**: Ensure GitHub Actions pass
3. **Review Coverage**: Aim for >80% test coverage
4. **Validate Specs**: Run compliance checker

#### For Claude Interactions
1. **Be Specific**: Reference exact spec sections
2. **Provide Context**: Mention current phase/component
3. **Request Documentation**: Ask for docstrings
4. **Iterative Refinement**: Request improvements in PR comments

### 7. Example Complete Workflow

```bash
# 1. Create issue on GitHub
# Title: [GENERATE] Data Preprocessing Pipeline

# 2. Comment on issue:
# @claude Based on specs/IMPLEMENTATION_PLAN.md#week-1 and 
# specs/ARCHITECTURE.md#input-processing-layer, generate:
# - Data ingestion module
# - Text preprocessing pipeline
# - CFPB-specific normalizers
# - Tests and examples

# 3. Claude creates PR #3

# 4. Check PR status on GitHub
# - See test results
# - Review generated code

# 5. Test locally
gh pr checkout 3
pytest tests/
python scripts/validate_spec_compliance.py

# 6. If tests pass, merge PR
gh pr merge 3

# 7. Create next issue for next component
```

### 8. Troubleshooting

#### Claude Not Responding
- Check @claude mention is correct
- Verify CLAUDE_CODE_OAUTH_TOKEN secret is set
- Check Actions tab for workflow runs

#### Tests Failing
- Review test output in PR checks
- Run tests locally for debugging
- Ask Claude to fix in PR comment: "@claude fix the failing tests"

#### Spec Validation Errors
- Run `python scripts/validate_spec_compliance.py`
- Address missing requirements
- Update specs if needed

### 9. Advanced Features

#### Multi-Component Generation
```markdown
@claude Generate all Phase 1 components from specs/IMPLEMENTATION_PLAN.md#phase-1:
1. Create each as separate commits
2. Include all tests
3. Add integration examples
```

#### Code Review Request
```markdown
@claude Review the code in src/classification/ and suggest improvements based on specs/ARCHITECTURE.md
```

#### Documentation Generation
```markdown
@claude Generate API documentation for all modules in src/ based on the implementations
```

## Quick Reference

### Key Commands
```bash
# Create issue from template
gh issue create --template generate-code.md

# Check PR locally  
gh pr checkout [NUMBER]

# Run tests
pytest tests/

# Validate specs
python scripts/validate_spec_compliance.py

# Merge PR
gh pr merge [NUMBER]
```

### Claude Commands in Issues/PRs
- `@claude generate [component]` - Generate new code
- `@claude validate [module]` - Validate against specs  
- `@claude fix tests` - Fix failing tests
- `@claude review` - Review existing code
- `@claude document` - Generate documentation