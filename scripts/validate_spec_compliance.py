#!/usr/bin/env python3
"""
Spec Compliance Validator

This script validates that generated code complies with the specifications
defined in the /specs directory.
"""

import os
import sys
import json
import ast
from pathlib import Path
from typing import Dict, List, Tuple
import re

class SpecValidator:
    def __init__(self, specs_dir: str = "specs", src_dir: str = "src"):
        self.specs_dir = Path(specs_dir)
        self.src_dir = Path(src_dir)
        self.validation_results = {
            "compliant": [],
            "warnings": [],
            "errors": [],
            "summary": {}
        }
    
    def load_architecture_spec(self) -> Dict:
        """Load and parse the architecture specification."""
        arch_file = self.specs_dir / "ARCHITECTURE.md"
        if not arch_file.exists():
            return {}
        
        with open(arch_file, 'r') as f:
            content = f.read()
        
        # Extract component definitions from architecture
        components = {}
        current_component = None
        
        for line in content.split('\n'):
            if '### ' in line and 'Layer' in line:
                # Extract layer name
                match = re.search(r'### \d+\.\s+(.+?)(?:\s+Layer)?', line)
                if match:
                    current_component = match.group(1).lower().replace(' ', '_')
                    components[current_component] = {
                        'required_modules': [],
                        'required_classes': [],
                        'dependencies': []
                    }
            elif current_component and '**Components**:' in line:
                # Start capturing components
                capturing = True
            elif current_component and '**Technologies**:' in line:
                # Start capturing technologies
                capturing_tech = True
        
        return components
    
    def load_technical_stack(self) -> Dict:
        """Load and parse the technical stack specification."""
        tech_file = self.specs_dir / "TECHNICAL_STACK.md"
        if not tech_file.exists():
            return {}
        
        with open(tech_file, 'r') as f:
            content = f.read()
        
        # Extract required libraries
        libraries = []
        for line in content.split('\n'):
            if line.strip().startswith('- ') and ('==' in line or '>=' in line):
                # Extract library name
                lib_match = re.search(r'- ([a-zA-Z0-9_-]+)', line)
                if lib_match:
                    libraries.append(lib_match.group(1))
        
        return {'required_libraries': libraries}
    
    def validate_project_structure(self) -> None:
        """Validate that the project structure matches specifications."""
        required_dirs = ['src', 'tests', 'specs', 'docs']
        
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                self.validation_results['compliant'].append(
                    f"✅ Required directory '{dir_name}' exists"
                )
            else:
                self.validation_results['warnings'].append(
                    f"⚠️ Required directory '{dir_name}' not found"
                )
    
    def validate_module_structure(self, architecture: Dict) -> None:
        """Validate that source modules match architecture specification."""
        if not self.src_dir.exists():
            self.validation_results['warnings'].append(
                "⚠️ Source directory not found - no code generated yet"
            )
            return
        
        # Check for expected module directories based on architecture
        expected_modules = {
            'input_processing': 'Input Processing Layer',
            'classification': 'Classification & Extraction Layer',
            'knowledge': 'Knowledge Representation Layer',
            'reasoning': 'Reasoning Engine Layer',
            'output': 'Output Generation Layer'
        }
        
        for module_name, layer_name in expected_modules.items():
            module_path = self.src_dir / module_name
            if module_path.exists():
                self.validation_results['compliant'].append(
                    f"✅ Module '{module_name}' exists for {layer_name}"
                )
                # Check for __init__.py
                if (module_path / "__init__.py").exists():
                    self.validation_results['compliant'].append(
                        f"✅ Module '{module_name}' properly initialized"
                    )
                else:
                    self.validation_results['warnings'].append(
                        f"⚠️ Module '{module_name}' missing __init__.py"
                    )
            else:
                self.validation_results['warnings'].append(
                    f"⚠️ Expected module '{module_name}' not found for {layer_name}"
                )
    
    def validate_dependencies(self, tech_stack: Dict) -> None:
        """Validate that requirements.txt matches technical stack."""
        req_file = Path("requirements.txt")
        if not req_file.exists():
            self.validation_results['warnings'].append(
                "⚠️ requirements.txt not found"
            )
            return
        
        with open(req_file, 'r') as f:
            installed_libs = [line.split('==')[0].split('>=')[0].strip() 
                            for line in f if line.strip() and not line.startswith('#')]
        
        required_libs = tech_stack.get('required_libraries', [])
        
        for lib in required_libs:
            if lib in installed_libs:
                self.validation_results['compliant'].append(
                    f"✅ Required library '{lib}' is listed in requirements.txt"
                )
            else:
                self.validation_results['errors'].append(
                    f"❌ Required library '{lib}' missing from requirements.txt"
                )
    
    def validate_test_coverage(self) -> None:
        """Validate that tests exist for source modules."""
        if not self.src_dir.exists():
            return
        
        test_dir = Path("tests")
        if not test_dir.exists():
            self.validation_results['warnings'].append(
                "⚠️ Tests directory not found"
            )
            return
        
        # Check for test files corresponding to source modules
        for module_path in self.src_dir.iterdir():
            if module_path.is_dir() and not module_path.name.startswith('__'):
                test_file = test_dir / f"test_{module_path.name}.py"
                if test_file.exists():
                    self.validation_results['compliant'].append(
                        f"✅ Tests exist for module '{module_path.name}'"
                    )
                else:
                    self.validation_results['warnings'].append(
                        f"⚠️ No tests found for module '{module_path.name}'"
                    )
    
    def generate_report(self) -> str:
        """Generate a validation report."""
        report = ["# 📋 Specification Compliance Report\n"]
        
        # Summary
        total_checks = (len(self.validation_results['compliant']) + 
                       len(self.validation_results['warnings']) + 
                       len(self.validation_results['errors']))
        
        if total_checks > 0:
            compliance_rate = (len(self.validation_results['compliant']) / total_checks) * 100
        else:
            compliance_rate = 0
        
        report.append(f"## Summary")
        report.append(f"- **Compliance Rate**: {compliance_rate:.1f}%")
        report.append(f"- **Total Checks**: {total_checks}")
        report.append(f"- ✅ Compliant: {len(self.validation_results['compliant'])}")
        report.append(f"- ⚠️ Warnings: {len(self.validation_results['warnings'])}")
        report.append(f"- ❌ Errors: {len(self.validation_results['errors'])}\n")
        
        # Compliant items
        if self.validation_results['compliant']:
            report.append("## ✅ Compliant Items")
            for item in self.validation_results['compliant']:
                report.append(f"- {item}")
            report.append("")
        
        # Warnings
        if self.validation_results['warnings']:
            report.append("## ⚠️ Warnings")
            for warning in self.validation_results['warnings']:
                report.append(f"- {warning}")
            report.append("")
        
        # Errors
        if self.validation_results['errors']:
            report.append("## ❌ Errors")
            for error in self.validation_results['errors']:
                report.append(f"- {error}")
            report.append("")
        
        # Recommendations
        report.append("## 📝 Recommendations")
        if self.validation_results['errors']:
            report.append("1. **Fix critical errors** - Address missing required libraries")
        if self.validation_results['warnings']:
            report.append("2. **Address warnings** - Create missing directories and test files")
        if compliance_rate < 100:
            report.append("3. **Improve compliance** - Generate missing components from specs")
        else:
            report.append("✨ **Excellent!** - Code fully complies with specifications")
        
        return "\n".join(report)
    
    def run_validation(self) -> Tuple[bool, str]:
        """Run all validation checks."""
        print("🔍 Starting specification compliance validation...")
        
        # Load specifications
        architecture = self.load_architecture_spec()
        tech_stack = self.load_technical_stack()
        
        # Run validation checks
        self.validate_project_structure()
        self.validate_module_structure(architecture)
        self.validate_dependencies(tech_stack)
        self.validate_test_coverage()
        
        # Generate report
        report = self.generate_report()
        
        # Determine success
        success = len(self.validation_results['errors']) == 0
        
        return success, report


def main():
    """Main entry point for the validation script."""
    validator = SpecValidator()
    success, report = validator.run_validation()
    
    # Print report
    print("\n" + report)
    
    # Save report to file
    report_file = Path("validation_report.md")
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\n📄 Report saved to {report_file}")
    
    # Exit with appropriate code
    if not success:
        print("\n❌ Validation failed - please address the errors above")
        sys.exit(1)
    else:
        print("\n✅ Validation passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()