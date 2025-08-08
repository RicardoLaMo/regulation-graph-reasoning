---
name: Validate Code Against Specs
about: Request validation of existing code against specifications
title: '[VALIDATE] '
labels: validation, claude-bot
assignees: ''

---

## Code to Validate
<!-- Specify which code/module to validate -->
Module/Component: 

## Specification to Validate Against
<!-- Link to specs that should be validated -->
- [ ] Architecture compliance: `specs/ARCHITECTURE.md`
- [ ] Technical stack compliance: `specs/TECHNICAL_STACK.md`
- [ ] Implementation plan compliance: `specs/IMPLEMENTATION_PLAN.md`

## Validation Request
@claude Please validate the code in `src/[module_name]` against the specifications. Check for:

1. **Architecture Compliance**
   - Component structure matches specs/ARCHITECTURE.md
   - Correct layer separation
   - Proper interfaces between components

2. **Technical Stack Compliance**
   - Uses specified libraries and versions
   - Follows technology choices in specs/TECHNICAL_STACK.md

3. **Implementation Compliance**
   - Follows the plan in specs/IMPLEMENTATION_PLAN.md
   - Meets the defined success criteria
   - Includes all required deliverables

Please provide a detailed report with:
- ✅ What complies with specs
- ⚠️ What partially complies (with details)
- ❌ What doesn't comply (with recommendations)

## Expected Output
- Compliance report as PR comment
- Specific line references for issues
- Recommendations for fixes