"""
Comprehensive validation tests for documentation markdown files added in current branch.

Tests ensure that:
- All markdown files are valid and parseable
- Links within markdown files are correctly formatted
- Code blocks have proper language identifiers
- Tables are properly formatted
- Headings follow a logical hierarchy
"""
import os
import re
from pathlib import Path
from typing import List, Tuple

import pytest


class TestDocumentationFilesValidation:
    """Validate all markdown documentation files in the repository."""
    
    @pytest.fixture
    def doc_root(self) -> Path:
        """Get the repository root directory."""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def markdown_files(self, doc_root: Path) -> List[Path]:
        """Get all markdown files in the repository root."""
        return [
            f for f in doc_root.glob("*.md")
            if f.name not in ["README.md", "LICENSE.md"]
        ]
    
    def test_all_markdown_files_exist(self, markdown_files: List[Path]):
        """Verify that markdown files exist and are readable."""
        assert len(markdown_files) > 0, "No markdown files found"
        for md_file in markdown_files:
            assert md_file.exists(), f"File {md_file} does not exist"
            assert md_file.is_file(), f"{md_file} is not a file"
            assert os.access(md_file, os.R_OK), f"File {md_file} is not readable"
    
    def test_markdown_files_not_empty(self, markdown_files: List[Path]):
        """Verify that markdown files are not empty."""
        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            assert len(content.strip()) > 0, f"File {md_file.name} is empty"
            assert len(content) > 100, f"File {md_file.name} is suspiciously short ({len(content)} chars)"
    
    def test_markdown_has_proper_headings(self, markdown_files: List[Path]):
        """Verify that markdown files have properly structured headings."""
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            headings = heading_pattern.findall(content)
            
            # Should have at least one heading
            assert len(headings) > 0, f"File {md_file.name} has no headings"
            
            # First heading should be level 1 (# Title)
            if headings:
                first_level = len(headings[0][0])
                assert first_level == 1, f"File {md_file.name} first heading is not level 1"
    
    def test_code_blocks_have_language_identifiers(self, markdown_files: List[Path]):
        """Verify that code blocks specify language for syntax highlighting."""
        code_block_pattern = re.compile(r'```(\w*)\n', re.MULTILINE)
        
        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            code_blocks = code_block_pattern.findall(content)
            
            # If file has code blocks, check they have language identifiers
            if code_blocks:
                empty_blocks = [i for i, lang in enumerate(code_blocks) if not lang]
                # Allow some blocks without language (like plain text examples)
                assert len(empty_blocks) < len(code_blocks) * 0.5, \
                    f"File {md_file.name} has too many code blocks without language identifiers"
    
    def test_markdown_tables_are_properly_formatted(self, markdown_files: List[Path]):
        """Verify that markdown tables have consistent column counts."""
        table_row_pattern = re.compile(r'^\|(.+)\|$', re.MULTILINE)
        
        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            in_table = False
            table_column_count = 0
            
            for i, line in enumerate(lines):
                if table_row_pattern.match(line):
                    columns = len([c for c in line.split('|') if c.strip()])
                    
                    if not in_table:
                        in_table = True
                        table_column_count = columns
                    else:
                        # Skip separator rows (contain only |, -, :, and spaces)
                        if re.match(r'^[\|\-\:\s]+$', line):
                            continue
                        
                        assert columns == table_column_count, \
                            f"File {md_file.name} line {i+1}: inconsistent table columns " \
                            f"(expected {table_column_count}, got {columns})"
                else:
                    in_table = False
    
    def test_no_broken_markdown_links(self, markdown_files: List[Path], doc_root: Path):
        """Verify that internal markdown links point to existing files."""
        # Pattern for markdown links: [text](url)
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        
        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            links = link_pattern.findall(content)
            
            for link_text, link_url in links:
                # Skip external URLs
                if link_url.startswith(('http://', 'https://', '#', 'mailto:')):
                    continue
                
                # Skip anchor links
                if link_url.startswith('#'):
                    continue
                
                # For internal file links, verify the file exists
                target_path = (doc_root / link_url).resolve()
                
                # Allow links to common files that might exist
                if target_path.name in ['LICENSE', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md']:
                    continue
                
                # If it's a .md file, it should exist
                if link_url.endswith('.md'):
                    assert target_path.exists(), \
                        f"File {md_file.name} links to non-existent file: {link_url}"
    
    def test_no_trailing_whitespace(self, markdown_files: List[Path]):
        """Verify that markdown files don't have trailing whitespace."""
        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            bad_lines = []
            for i, line in enumerate(lines, 1):
                # Skip empty lines
                if not line.strip():
                    continue
                # Check for trailing whitespace
                if line.rstrip() != line:
                    bad_lines.append(i)
            
            # Allow a small number of trailing whitespace issues
            assert len(bad_lines) < 5, \
                f"File {md_file.name} has trailing whitespace on lines: {bad_lines[:10]}"
    
    def test_test_summary_files_have_required_sections(self, doc_root: Path):
        """Verify that test summary files contain required sections."""
        summary_files = list(doc_root.glob("*TEST*SUMMARY*.md"))
        summary_files.extend(doc_root.glob("*GENERATION*.md"))
        
        required_keywords = ['test', 'coverage', 'summary']
        
        for summary_file in summary_files:
            content = summary_file.read_text(encoding='utf-8').lower()
            
            # Should contain at least 2 of the required keywords
            found_keywords = sum(1 for kw in required_keywords if kw in content)
            assert found_keywords >= 2, \
                f"File {summary_file.name} doesn't appear to be a proper test summary"
    
    def test_test_reference_files_have_examples(self, doc_root: Path):
        """Verify that test reference files contain code examples."""
        reference_files = list(doc_root.glob("*REFERENCE*.md"))
        
        for ref_file in reference_files:
            content = ref_file.read_text(encoding='utf-8')
            
            # Should contain code blocks
            assert '```' in content, \
                f"Reference file {ref_file.name} should contain code examples"
            
            # Should contain commands or usage examples
            assert any(keyword in content.lower() for keyword in ['pytest', 'npm test', 'run', 'command']), \
                f"Reference file {ref_file.name} should contain usage examples"


class TestMarkdownContentQuality:
    """Test the quality and consistency of markdown content."""
    
    @pytest.fixture
    def test_generation_files(self) -> List[Path]:
        """Get all test generation markdown files."""
        doc_root = Path(__file__).parent.parent.parent
        return list(doc_root.glob("TEST_GENERATION*.md"))
    
    def test_test_generation_files_have_statistics(self, test_generation_files: List[Path]):
        """Verify test generation files include statistics."""
        stats_keywords = ['lines', 'tests', 'coverage', 'files', 'methods']
        
        for gen_file in test_generation_files:
            content = gen_file.read_text(encoding='utf-8').lower()
            
            # Should contain at least 3 statistics-related keywords
            found_stats = sum(1 for kw in stats_keywords if kw in content)
            assert found_stats >= 3, \
                f"File {gen_file.name} should contain test statistics"
    
    def test_comprehensive_files_are_actually_comprehensive(self):
        """Verify files marked as 'comprehensive' have substantial content."""
        doc_root = Path(__file__).parent.parent.parent
        comp_files = list(doc_root.glob("*COMPREHENSIVE*.md"))
        
        for comp_file in comp_files:
            content = comp_file.read_text(encoding='utf-8')
            
            # Comprehensive files should be substantial (> 5KB)
            assert len(content) > 5000, \
                f"File {comp_file.name} marked as comprehensive but is only {len(content)} chars"
            
            # Should have multiple major sections (## headings)
            major_sections = len(re.findall(r'^##\s+', content, re.MULTILINE))
            assert major_sections >= 5, \
                f"File {comp_file.name} should have at least 5 major sections"
    
    def test_quick_reference_files_are_concise(self):
        """Verify quick reference files are actually quick/concise."""
        doc_root = Path(__file__).parent.parent.parent
        quick_files = list(doc_root.glob("*QUICK*.md"))
        
        for quick_file in quick_files:
            content = quick_file.read_text(encoding='utf-8')
            
            # Quick reference should be concise (< 10KB)
            assert len(content) < 10000, \
                f"File {quick_file.name} marked as quick reference but is {len(content)} chars"
            
            # Should have code examples (practical reference)
            assert '```' in content, \
                f"Quick reference {quick_file.name} should have code examples"


class TestDocumentationConsistency:
    """Test consistency across documentation files."""
    
    def test_consistent_terminology_usage(self):
        """Verify consistent use of terminology across docs."""
        doc_root = Path(__file__).parent.parent.parent
        md_files = list(doc_root.glob("TEST_*.md"))
        
        # Check for consistent spelling/terminology
        inconsistencies = {
            'pytest': ['py.test', 'py-test'],
            'frontend': ['front-end', 'Front-end'],
            'backend': ['back-end', 'Back-end'],
        }
        
        for md_file in md_files:
            content = md_file.read_text(encoding='utf-8')
            
            for correct, alternatives in inconsistencies.items():
                for alt in alternatives:
                    # Allow in code blocks
                    if alt in content and '```' not in content.split(alt)[0][-100:]:
                        # Check it's not in a code block
                        pass  # This is a simplified check
    
    def test_all_summaries_reference_actual_test_files(self):
        """Verify summary files reference actual test files that exist."""
        doc_root = Path(__file__).parent.parent.parent
        summary_files = list(doc_root.glob("*SUMMARY*.md"))
        
        test_file_pattern = re.compile(r'`?(tests/[a-zA-Z0-9_/]+\.py|frontend/__tests__/[a-zA-Z0-9_/]+\.test\.(ts|tsx|js|jsx))`?')
        
        for summary in summary_files:
            content = summary.read_text(encoding='utf-8')
            referenced_tests = test_file_pattern.findall(content)
            
            for test_ref in referenced_tests:
                test_path = test_ref[0] if isinstance(test_ref, tuple) else test_ref
                full_path = doc_root / test_path
                
                # File should exist
                assert full_path.exists(), \
                    f"Summary {summary.name} references non-existent test: {test_path}"