---
name: Generate Code from Specs
about: Request Claude to generate code based on specifications
title: '[GENERATE] '
labels: code-generation, claude-bot
assignees: ''

---

## Component to Generate
<!-- Specify which component or module to generate -->

## Specification References
<!-- Link to specific sections in the specs -->
- Architecture: `specs/ARCHITECTURE.md#section-name`
- Technical Stack: `specs/TECHNICAL_STACK.md#dependencies`
- Implementation Phase: `specs/IMPLEMENTATION_PLAN.md#phase-number`

## Requirements
<!-- List specific requirements for the generated code -->
- [ ] Follow exact specification structure
- [ ] Include comprehensive unit tests
- [ ] Add inline documentation
- [ ] Create usage examples
- [ ] Implement error handling

## Claude Generation Request
<!-- This is the actual request to Claude. Modify as needed -->
@claude Please generate the [COMPONENT_NAME] based on the specifications listed above. Ensure the code:
1. Follows the architecture defined in specs/ARCHITECTURE.md
2. Uses the technology stack from specs/TECHNICAL_STACK.md
3. Includes unit tests in the tests/ directory
4. Has proper error handling and logging
5. Includes docstrings for all functions and classes

Place the generated code in:
- Source code: `src/[module_name]/`
- Tests: `tests/test_[module_name].py`
- Examples: `examples/[module_name]_example.py`

## Validation Criteria
<!-- How to validate the generated code -->
- [ ] Code matches specification structure
- [ ] All tests pass
- [ ] No linting errors
- [ ] Documentation complete
- [ ] Examples run successfully