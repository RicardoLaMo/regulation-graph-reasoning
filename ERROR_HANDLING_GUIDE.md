# Error Handling Guide

## Common GitHub Actions Errors and Solutions

### 1. Missing requirements.txt Error
**Error**: `ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'`

**Solution**:
- ✅ Already fixed: Created initial `requirements.txt`
- ✅ Workflow updated to handle missing files gracefully
- Future: Claude should always generate requirements.txt when creating Python code

### 2. Test Failures in PRs

**Systematic Approach**:

#### Step 1: Check PR Status
```bash
# View PR checks on GitHub
# Or locally:
gh pr checks [PR-NUMBER]
```

#### Step 2: Fix in PR Comments
If tests fail, comment on the PR:
```markdown
@claude The tests are failing with this error:
[paste error message]
Please fix the failing tests.
```

#### Step 3: Local Debugging
```bash
# Pull the PR locally
gh pr checkout [PR-NUMBER]

# Run tests to see detailed errors
pytest tests/ -v

# Fix issues manually if needed
# Then push fixes
git add .
git commit -m "Fix failing tests"
git push
```

### 3. Claude Not Responding

**Troubleshooting Checklist**:

1. **Check GitHub Actions**:
   - Go to: https://github.com/[your-repo]/actions
   - Look for failed workflows
   - Click to see error details

2. **Common Issues**:
   - ❌ Missing permissions → Check workflow has `contents: write`
   - ❌ Missing specs → Ensure specs are in main branch
   - ❌ Token issues → Verify CLAUDE_CODE_OAUTH_TOKEN secret is set
   - ❌ Complex request → Simplify to smaller chunks

3. **Debug with Simple Request**:
   ```markdown
   @claude Please create a simple hello.py file that prints "Hello World"
   ```

### 4. Spec Validation Failures

**When `validate_spec_compliance.py` fails**:

```bash
# Run validation locally
python scripts/validate_spec_compliance.py

# Common fixes:
# 1. Missing directories
mkdir -p src tests docs

# 2. Missing __init__.py files
touch src/__init__.py
touch src/module_name/__init__.py

# 3. Update requirements.txt with missing libraries
echo "library_name>=version" >> requirements.txt
```

### 5. Systematic Error Prevention

#### Pre-PR Checklist
Before creating issues for Claude:
- [ ] Specs exist in main branch
- [ ] Previous PRs are merged
- [ ] Request is specific and references specs
- [ ] Request is not too complex (break into smaller parts)

#### Post-PR Checklist
After Claude creates PR:
- [ ] Check GitHub Actions status
- [ ] Review generated code
- [ ] Run tests locally before merging
- [ ] Validate against specs

### 6. Automated Error Recovery

#### Set Up Error Notifications
Add to `.github/workflows/test-generated-code.yml`:

```yaml
- name: Notify on Failure
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: '❌ Tests failed! Check the [Actions tab](https://github.com/${{ github.repository }}/actions) for details.'
      })
```

### 7. Common Claude Fixes

#### Request Pattern for Fixes
```markdown
@claude The GitHub Action is failing with:
[error message]

Please:
1. Fix the error
2. Add error handling to prevent this in future
3. Update tests if needed
```

#### Batch Fix Request
```markdown
@claude Please fix these issues from the test run:
1. Missing import in src/module.py line 5
2. Type error in tests/test_module.py line 23
3. Add requirements.txt if missing
```

### 8. Error Prevention Best Practices

1. **Always Include in Claude Requests**:
   - "Include error handling"
   - "Add requirements.txt with all dependencies"
   - "Create tests that pass"
   - "Follow PEP 8 style"

2. **Use Templates**:
   - Always use issue templates from `.github/ISSUE_TEMPLATE/`
   - They include validation criteria

3. **Progressive Development**:
   - Start with simple components
   - Build complexity gradually
   - Test each component before moving on

### 9. Quick Fix Commands

```bash
# Fix formatting issues
black src/ tests/

# Fix import sorting
isort src/ tests/

# Type checking
mypy src/ --ignore-missing-imports

# Run all checks locally
pytest && black --check . && flake8 . && mypy .

# Auto-fix common issues
autopep8 --in-place --recursive .
```

### 10. Emergency Fixes

If Claude is completely stuck:

1. **Cancel stuck workflow**:
   ```bash
   gh run cancel [RUN-ID]
   ```

2. **Close and reopen issue**:
   ```bash
   gh issue close [NUMBER]
   gh issue reopen [NUMBER]
   ```

3. **Create simpler request**:
   - Break complex requests into smaller parts
   - Remove spec references if they're causing issues
   - Ask for one file at a time

## Monitoring and Alerts

### Set Up Status Badge
Add to README.md:
```markdown
![Tests](https://github.com/[username]/[repo]/workflows/Test%20Generated%20Code/badge.svg)
```

### View All Workflow Runs
```bash
# List recent workflow runs
gh run list

# View specific run details
gh run view [RUN-ID]

# Watch a run in progress
gh run watch [RUN-ID]
```

## Getting Help

1. **Check Claude Code Documentation**: https://github.com/anthropics/claude-code-action
2. **GitHub Actions Documentation**: https://docs.github.com/en/actions
3. **Create Discussion**: Use GitHub Discussions for non-urgent questions
4. **Report Issues**: File issues in the claude-code-action repository for bugs