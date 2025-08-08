# regulation-graph-reasoning

![Tests](https://github.com/RicardoLaMo/regulation-graph-reasoning/workflows/Test%20Generated%20Code/badge.svg)
![Claude Bot](https://github.com/RicardoLaMo/regulation-graph-reasoning/workflows/Claude%20PR%20Assistant/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Specialized LLM for regulation reasoning path and graph/ontology.

## 🚀 Quick Start

### Using Claude Bot for Code Generation

1. **Create an issue** using our templates:
   ```bash
   gh issue create --template generate-code.md
   ```

2. **Mention Claude** in the issue:
   ```markdown
   @claude Generate [component] from specs/[spec-file].md
   ```

3. **Claude creates a PR** with the generated code

4. **Tests run automatically** - check the status badges above

5. **Merge when ready**:
   ```bash
   gh pr merge [PR-NUMBER]
   ```

## 📚 Documentation

- [Code Generation Guide](CODE_GENERATION_GUIDE.md) - Complete workflow for using Claude
- [Error Handling Guide](ERROR_HANDLING_GUIDE.md) - Troubleshooting common issues
- [Example Issue](EXAMPLE_ISSUE.md) - Template for your first code generation request
- [Specifications](specs/) - Technical specifications and architecture

## 🛠️ Setup

### Prerequisites
- Python 3.9+
- GitHub CLI (`gh`)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/RicardoLaMo/regulation-graph-reasoning.git
cd regulation-graph-reasoning

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/
```

## 🤖 Claude Bot Commands

Use these in issues, PRs, or discussions:
- `@claude generate [component]` - Generate new code
- `@claude validate [module]` - Validate against specs
- `@claude fix tests` - Fix failing tests
- `@claude review` - Review existing code

## 📊 Project Status

- Phase 1: Foundation ⏳ (In Progress)
- Phase 2: Legal Reasoning 📅 (Planned)
- Phase 3: API Development 📅 (Planned)
- Phase 4: Production Ready 📅 (Planned)

See [Implementation Plan](specs/IMPLEMENTATION_PLAN.md) for details.
