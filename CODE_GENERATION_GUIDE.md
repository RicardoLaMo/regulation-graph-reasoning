# Code Generation Guide

## Overview
This guide explains how to use Claude to generate code from the specification documents.

## Workflow

### 1. Specification-Driven Development
All code should be generated based on the specifications in the `/specs` folder:
- `ARCHITECTURE.md` - System design and component structure
- `TECHNICAL_STACK.md` - Technology choices and dependencies
- `IMPLEMENTATION_PLAN.md` - Development phases and milestones

### 2. How to Request Code Generation

When creating issues or PRs, use these patterns:

#### Generate Initial Code Structure
```
@claude Based on specs/ARCHITECTURE.md, create the initial project structure with:
- Python package setup
- Core module directories
- Configuration files
```

#### Generate Specific Components
```
@claude Following the Input Processing Layer design in specs/ARCHITECTURE.md, 
implement the text preprocessing module with:
- Text cleaning functions
- CFPB-specific normalizers
- Document chunking logic
```

#### Generate From Technical Stack
```
@claude Using the technologies listed in specs/TECHNICAL_STACK.md, 
create the requirements.txt and setup.py files
```

### 3. Best Practices

1. **Reference Specific Sections**: Always reference the specific section of the spec
2. **Incremental Generation**: Generate one component at a time
3. **Test-Driven**: Ask Claude to generate tests alongside implementation
4. **Review and Iterate**: Review generated code and request refinements

### 4. Example Requests

#### Phase 1: Foundation
```
@claude Create the foundation layer from specs/IMPLEMENTATION_PLAN.md Phase 1:
- Set up project structure
- Implement data ingestion for CFPB complaints
- Create basic preprocessing pipeline
```

#### Phase 2: Classification Models
```
@claude Implement the Classification Layer from specs/ARCHITECTURE.md section 2:
- Product/Issue classifier using the specified Hugging Face model
- Legal entity extraction
- Financial NER components
```

### 5. Code Organization

Generated code will be organized as:
```
src/
├── input_processing/      # From Architecture Layer 1
├── classification/        # From Architecture Layer 2
├── knowledge/            # From Architecture Layer 3
├── reasoning/            # From Architecture Layer 4
└── output/               # From Architecture Layer 5
```

## Tips for Claude Interactions

1. **Be Specific**: Reference exact sections and line numbers from specs
2. **Provide Context**: Mention which phase or component you're working on
3. **Request Documentation**: Ask for docstrings and inline comments
4. **Verify Against Specs**: Ask Claude to verify implementation matches specs