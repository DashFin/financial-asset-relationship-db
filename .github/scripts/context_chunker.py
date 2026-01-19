#!/usr/bin/env python3
"""
Context chunker for PR Agent.

This module provides intelligent context chunking to handle large PRs
without hitting token limits. It implements priority-based processing,
smart chunking, and automatic summarization.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class ContextChunker:
    """
    Handles intelligent context chunking for large PRs.

    Provides priority-based processing, smart chunking with overlap,
    and automatic summarization when content exceeds token limits.
    """

    def __init__(self, config_path: str = ".github/pr-agent-config.yml"):
        """
        Initialize the ContextChunker by loading configuration and applying defaults.
        
        Loads configuration from the given YAML path (when present) and configures token-related limits (max tokens, chunk size, overlap, summarization threshold), establishes the priority order and a mapping for chunk types, and initializes an optional tokenizer/encoder.
        
        Parameters:
            config_path (str): Path to a YAML configuration file that can override defaults (default: ".github/pr-agent-config.yml").
        """
        self.config: Dict = self._load_config(config_path)

        # Read agent context settings with safe defaults
        agent_cfg = (self.config.get("agent") or {}).get("context") or {}
        self.max_tokens = int(agent_cfg.get("max_tokens", 32000))
        self.chunk_size = int(agent_cfg.get("chunk_size", max(1, self.max_tokens - 4000)))
        self.overlap_tokens = int(agent_cfg.get("overlap_tokens", 2000))
        self.summarization_threshold = int(
            agent_cfg.get("summarization_threshold", int(self.max_tokens * 0.9))
        )

        # Prepare priority order
        limits_cfg = (self.config.get("limits") or {}).get("fallback") or {}
        self.priority_order = limits_cfg.get(
            "priority_order",
            ["review_comments", "test_failures", "changed_files", "ci_logs", "full_diff"],
        )
        # Map chunk type to priority index (lower is higher priority)
        self.priority_map = {name: i for i, name in enumerate(self.priority_order)}

        # Setup tokenizer/encoder if tiktoken available
        self._encoder = self._init_encoder()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load and parse a YAML configuration file from the given path.
        
        If the file does not exist or PyYAML is unavailable, returns an empty dict.
        If parsing fails, emits a warning to stderr and returns an empty dict.
        
        Parameters:
            config_path (str): Filesystem path to the YAML config file.
        
        Returns:
            Dict[str, Any]: Parsed configuration as a dictionary, or an empty dict on missing/unavailable/failed load.
        """
        cfg_file = Path(config_path)
        if not (cfg_file.exists() and yaml is not None):
            return {}

        try:
            with cfg_file.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: failed to load config from {config_path}: {e}", file=sys.stderr)
            return {}

    def _init_encoder(self):
        """
        Initialize the token encoder and configure agent context defaults.
        
        This method attempts to obtain the "cl100k_base" tiktoken encoder when tiktoken is available. It also loads (and stores) configuration into `self.config` when a config file is present and sets the following agent context attributes with safe defaults: `self.max_tokens`, `self.chunk_size`, `self.overlap_tokens`, and `self.summarization_threshold`. It also establishes `self.priority_order` and `self.priority_map` for chunk prioritization and assigns the encoder (or None) to `self._encoder`.
        
        Returns:
            encoder: The initialized encoder instance if available, otherwise `None`.
        """
        if not TIKTOKEN_AVAILABLE:
            return None
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"Warning: failed to initialize tiktoken encoder: {e}", file=sys.stderr)
            return None
        self.config: Dict = {}

        # Load configuration if available
        cfg_file = Path(config_path)
        if cfg_file.exists() and yaml is not None:
            try:
                with cfg_file.open("r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: failed to load config from {config_path}: {e}", file=sys.stderr)
                self.config = {}

        # Read agent context settings with safe defaults
        agent_cfg = (self.config.get("agent") or {}).get("context") or {}
        self.max_tokens: int = int(agent_cfg.get("max_tokens", 32000))
        self.chunk_size: int = int(agent_cfg.get("chunk_size", max(1, self.max_tokens - 4000)))
        self.overlap_tokens: int = int(agent_cfg.get("overlap_tokens", 2000))
        self.summarization_threshold: int = int(
            agent_cfg.get("summarization_threshold", int(self.max_tokens * 0.9))
        )

        # Prepare priority order
        limits_cfg = (self.config.get("limits") or {}).get("fallback") or {}
        self.priority_order: List[str] = limits_cfg.get("priority_order", [
            "review_comments",
            "test_failures",
            "changed_files",
            "ci_logs",
            "full_diff",
        ])
        # Map chunk type to priority index (lower is higher priority)
        self.priority_map: Dict[str, int] = {name: i for i, name in enumerate(self.priority_order)}

        # Setup tokenizer/encoder if tiktoken available
        self._encoder = None
        if TIKTOKEN_AVAILABLE:
            try:
                self._encoder = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                print(f"Warning: failed to initialize tiktoken encoder: {e}", file=sys.stderr)
                self._encoder = None

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the token count of the given text.
        
        Uses the initialized encoder when available for an accurate count; otherwise applies a conservative heuristic to estimate tokens.
        
        Parameters:
            text (str): The input text to estimate tokens for.
        
        Returns:
            int: Estimated number of tokens in the input text.
        """
        if not text:
            return 0

        if self._encoder is not None:
            try:
                return len(self._encoder.encode(text))
            except Exception as e:
                # Log encoding failure and fall back to heuristic
                print(f"Warning: tiktoken encoding failed: {e}", file=sys.stderr)
                pass

        # Heuristic fallback: ~4 chars per token with adjustments
        base_tokens = len(text) / 4.0

        # Adjust for code structural characters
        structural_chars = sum(1 for c in text if c in "{}()[];")
        base_tokens += structural_chars * 0.5

        # Adjust for whitespace sequences
        whitespace_count = sum(
            1 for i, c in enumerate(text)
            if c.isspace() and (i == 0 or not text[i - 1].isspace())
        )
        base_tokens += whitespace_count * 0.25

        # Adjust for markdown formatting
        format_chars = sum(1 for c in text if c in "*_`#-")
        base_tokens += format_chars * 0.3

        # Add 10% safety margin
        return int(base_tokens * 1.1)

    def process_context(self, pr_data: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Produce a combined PR context string that fits within token limits, applying priority-based chunking, truncation, or omission as needed.
        
        Parameters:
            pr_data (Dict[str, Any]): PR data containing keys such as reviews, files, test_failures, ci_logs, and diff.
        
        Returns:
            Tuple[str, bool]: The processed content string and a boolean that is `True` if chunking/truncation was applied, `False` otherwise.
        """
        chunks = self._extract_chunks(pr_data)
        total_tokens = sum(self.estimate_tokens(chunk.get("content", "")) for chunk in chunks)

        if total_tokens <= self.max_tokens:
            # No chunking needed
            content = self._combine_chunks(chunks)
            return content, False

        # Apply chunking

    def _extract_chunks(self, pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Builds prioritized content chunks extracted from provided pull request data.
        
        Parameters:
            pr_data (Dict[str, Any]): PR data mapping used to build chunks. Expected keys include
                "reviews", "files", "test_failures", "ci_logs", and "diff".
        
        Returns:
            List[Dict[str, Any]]: A list of chunk dictionaries sorted by priority (lower number = higher priority).
                Each chunk has the keys:
                - "type": chunk category (e.g., "review_comments", "changed_files", "test_failures", "ci_logs", "full_diff")
                - "content": the formatted text for that chunk
                - "priority": numeric priority value
        """
        chunks: List[Dict[str, Any]] = []

        # Extract review comments
        reviews = pr_data.get("reviews", [])
        if reviews:
            review_content = self._format_reviews(reviews)
            chunks.append({
                "type": "review_comments",
                "content": review_content,
                "priority": self.priority_map.get("review_comments", 0),
            })

        # Extract changed files
        files = pr_data.get("files", [])
        if files:
            files_content = self._format_files(files)
            chunks.append({
                "type": "changed_files",
                "content": files_content,
                "priority": self.priority_map.get("changed_files", 2),
            })

        # Extract test failures
        test_failures = pr_data.get("test_failures", [])
        if test_failures:
            failures_content = self._format_test_failures(test_failures)
            chunks.append({
                "type": "test_failures",
                "content": failures_content,
                "priority": self.priority_map.get("test_failures", 1),
            })

        # Extract CI logs
        ci_logs = pr_data.get("ci_logs", "")
        if ci_logs:
            chunks.append({
                "type": "ci_logs",
                "content": ci_logs,
                "priority": self.priority_map.get("ci_logs", 3),
            })

        # Extract full diff
        full_diff = pr_data.get("diff", "")
        if full_diff:
            chunks.append({
                "type": "full_diff",
                "content": full_diff,
                "priority": self.priority_map.get("full_diff", 4),
            })

        # Sort by priority (lower number = higher priority)
        chunks.sort(key=lambda x: x.get("priority", 999))
        return chunks

    def _format_reviews(self, reviews: List[Dict[str, Any]]) -> str:
        """
        Format review comments into readable content.

        Parameters:
            reviews: List of review dictionaries.

        Returns:
            str: Formatted review content.
        """
        lines = ["## Review Comments\n"]
        for review in reviews:
            user = review.get("user", {}).get("login", "unknown")
            state = review.get("state", "unknown")
            body = review.get("body", "")
            lines.append(f"### @{user} ({state})\n{body}\n")
        return "\n".join(lines)

    def _format_files(self, files: List[Dict[str, Any]]) -> str:
        """
        Create a Markdown-formatted section describing changed files and their diffs.
        
        Each file becomes a "### filename (+additions/-deletions)" subsection. If a file dict includes a "patch" value, the patch is included in a fenced "```diff" code block. The function tolerates missing keys by using sensible defaults.
        
        Parameters:
            files (List[Dict[str, Any]]): List of file-change dictionaries. Expected keys:
                - "filename" (str): file path or name (defaults to "unknown")
                - "additions" (int): number of added lines (defaults to 0)
                - "deletions" (int): number of deleted lines (defaults to 0)
                - "patch" (str): diff/patch text to include (optional)
        
        Returns:
            str: Markdown string starting with "## Changed Files" and containing per-file sections; diffs are included in fenced `diff` blocks when present.
        """
        lines = ["## Changed Files\n"]
        for f in files:
            filename = f.get("filename", "unknown")
            additions = f.get("additions", 0)
            deletions = f.get("deletions", 0)
            patch = f.get("patch", "")
            lines.append(f"### {filename} (+{additions}/-{deletions})\n")
            if patch:
                lines.append(f"```diff\n{patch}\n```\n")
        return "\n".join(lines)

    def _format_test_failures(self, failures: List[Dict[str, Any]]) -> str:
        """
        Format a list of test failure records into a Markdown string.
        
        Parameters:
            failures (List[Dict[str, Any]]): List of failure records; each record may include a "name" (test name) and "message" (failure details). Missing "name" defaults to "unknown test".
        
        Returns:
            str: Markdown-formatted content starting with "## Test Failures" and a "### <test name>" subsection for each failure containing its message.
        """
        lines = ["## Test Failures\n"]
        for failure in failures:
            test_name = failure.get("name", "unknown test")
            message = failure.get("message", "")
            lines.append(f"### {test_name}\n{message}\n")
        return "\n".join(lines)

    def _combine_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Combine a list of content chunks into a single string separated by two newlines.
        
        Joins each chunk's "content" value in order; missing or absent "content" entries are treated as empty strings.
        
        Returns:
            str: Combined content string with chunks separated by two newlines.
        """
        return "\n\n".join(chunk.get("content", "") for chunk in chunks)

    def _build_limited_content(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Build content limited to max_tokens by prioritizing chunks.

        This method processes chunks in priority order, including as much
        content as possible while staying within token limits. Higher priority
        chunks are included first, and lower priority chunks are truncated
        or omitted if necessary.

        Parameters:
            chunks: Collection of content chunks to process, each containing
                   'type', 'content', and 'priority' keys.

        Returns:
            str: The processed content, limited to max_tokens.
        """
        if not chunks:
            return ""

        # Sort chunks by priority (already sorted, but ensure)
        sorted_chunks = sorted(chunks, key=lambda x: x.get("priority", 999))

        result_parts: List[str] = []
        remaining_tokens = self.max_tokens

        for chunk in sorted_chunks:
            content = chunk.get("content", "")
            chunk_type = chunk.get("type", "unknown")

            if not content:
                continue

            chunk_tokens = self.estimate_tokens(content)
            processed_chunk, tokens_used, should_break = self._process_chunk(
                content, chunk_type, chunk_tokens, remaining_tokens
            )

            if processed_chunk:
                result_parts.append(processed_chunk)
                remaining_tokens -= tokens_used

            if should_break:
                break

        return "\n\n".join(result_parts)

    def _process_chunk(
        self, content: str, chunk_type: str, chunk_tokens: int, remaining_tokens: int
    ) -> Tuple[str, int, bool]:
        """
        Decide how to include a single content chunk given the remaining token budget.
        
        Parameters:
            content (str): The chunk text to consider.
            chunk_type (str): Identifier used when generating truncation or omission notes.
            chunk_tokens (int): Estimated tokens required to include the full chunk.
            remaining_tokens (int): Tokens still available in the budget.
        
        Returns:
            processed_content (str): The content to include (possibly truncated or an omission note).
            tokens_used (int): Number of tokens accounted for by the returned content.
            stop_processing (bool): `True` if no further chunks should be processed, `False` otherwise.
        """
        if chunk_tokens <= remaining_tokens:
            return content, chunk_tokens, False

        if remaining_tokens > 500:
            return self._handle_truncation(content, chunk_type, remaining_tokens)

        return self._handle_omission(chunk_type, chunk_tokens)

    def _handle_truncation(
        self, content: str, chunk_type: str, remaining_tokens: int
    ) -> Tuple[str, int, bool]:
        """
        Attempt to truncate a chunk to fit within the remaining token budget and append a truncation notice.
        
        Parameters:
            content (str): Chunk content to truncate.
            chunk_type (str): Identifier included in the truncation notice.
            remaining_tokens (int): Available token budget for this chunk.
        
        Returns:
            truncated_content (str): Truncated content with a trailing note when truncation succeeded, or an empty string if truncation produced no content.
            tokens_used (int): Estimated token count of the returned content.
            continue_processing (bool): `False` to indicate processing should continue (truncation does not stop the overall assembly).
        """
        truncated = self._truncate_to_tokens(content, remaining_tokens - 100)
        if truncated:
            truncated_with_note = truncated + f"\n\n[{chunk_type} truncated due to token limit]"
            truncated_tokens = self.estimate_tokens(truncated_with_note)
            return truncated_with_note, truncated_tokens, False
        return "", 0, False

    def _handle_omission(self, chunk_type: str, chunk_tokens: int) -> Tuple[str, int, bool]:
        """
        Create an omission note for a chunk that cannot be included due to token limits.
        
        Returns:
            omission_note (str): Message indicating the chunk type was omitted and its estimated token count.
            tokens_used (int): 0.
            stop_processing (bool): True to indicate processing should stop.
        """
        omission_note = (
            f"\n[{chunk_type} omitted due to token limit - "
            f"contained {chunk_tokens} tokens]"
        )
        return omission_note, 0, True

    def _find_natural_boundary(self, text: str) -> str:
        """
        Truncates text at the last newline if that newline occurs in the latter half of the text.
        
        Returns:
            The text up to the last newline when that newline is after the midpoint of `text`; otherwise the original `text`.
        """
        last_newline = text.rfind('\n')
        if last_newline > len(text) // 2:
            return text[:last_newline]
        return text

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to approximately max_tokens.

        Attempts to truncate at natural boundaries (newlines, sentences).
        Re-checks token count after truncation to ensure it doesn't exceed the limit.

        Parameters:
            text: The text to truncate.
            max_tokens: Maximum number of tokens to allow.

        Returns:
            str: Truncated text.
        """
        if not text or max_tokens <= 0:
            return ""

        current_tokens = self.estimate_tokens(text)
        if current_tokens <= max_tokens:
            return text

        # Estimate character count for target tokens
        # Using conservative estimate of 3 chars per token (lower than the 4.0
        # used in heuristic estimation to ensure we don't exceed the limit)
        chars_per_token_conservative = 3
        target_chars = max_tokens * chars_per_token_conservative

        if target_chars >= len(text):
            return text

        # Try to truncate at a natural boundary
        truncated = self._find_natural_boundary(text[:target_chars])

        # Re-check token count and further trim if necessary
        while self.estimate_tokens(truncated) > max_tokens and len(truncated) > 0:
            # Trim by 10% of current length or at least 100 characters
            trim_amount = max(100, len(truncated) // 10)
            truncated = self._find_natural_boundary(truncated[:-trim_amount])

        return truncated


def main():
    """Example usage of the ContextChunker."""
    chunker = ContextChunker()

    # Example PR data
    example_pr = {
        'reviews': [
            {
                'user': {'login': 'reviewer1'},
                'state': 'changes_requested',
                'body': 'Please fix the bug in the database connection and add tests.'
            }
        ],
        'files': [
            {
                'filename': 'src/data/database.py',
                'additions': 50,
                'deletions': 20,
                'patch': '@@ -1,5 +1,10 @@\n-old code\n+new code'
            }
        ]
    }

    processed, chunked = chunker.process_context(example_pr)
    print(f"Chunked: {chunked}")
    print(f"\nProcessed content:\n{processed}")


if __name__ == "__main__":
    main()