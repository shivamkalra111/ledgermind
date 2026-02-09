"""
Security Module - Prompt Injection & Input Validation

Provides comprehensive protection against:
1. Prompt injection attacks
2. SQL injection via LLM
3. Path traversal attacks
4. Malicious content filtering

Reference: OWASP LLM Top 10, Prompt Injection Guidelines
"""

import re
import html
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Classification of detected threats."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityResult:
    """Result of security validation."""
    is_safe: bool
    threat_level: ThreatLevel
    threats_detected: List[str]
    sanitized_input: str
    original_input: str
    blocked: bool = False
    
    def __bool__(self) -> bool:
        return self.is_safe


# =============================================================================
# Prompt Injection Patterns
# =============================================================================

# Patterns that attempt to override system instructions
SYSTEM_OVERRIDE_PATTERNS = [
    # Direct instruction override
    r"ignore\s+(all\s+)?(previous|prior|above|your|my|the|these)?\s*(instructions?|prompts?|rules?|guidelines?)",
    r"disregard\s+(all\s+)?(previous|prior|above|your|the)?\s*(instructions?|prompts?|rules?)",
    r"forget\s+(all\s+)?(previous|prior|above|your|the)?\s*(instructions?|prompts?|rules?)",
    r"override\s+(system|previous|all|your|the)?\s*(prompts?|instructions?|rules?)",
    r"new\s+(instructions?|rules?)\s*:",
    r"system\s*:\s*you\s+(are|will|must|should)",
    r"from\s+now\s+on\s*,?\s*(you|ignore|forget)",
    r"ignore\s+(everything|all)\s+(above|before|else)",
    
    # Role manipulation
    r"you\s+are\s+(now|actually)\s+(a|an)\s+",
    r"act\s+as\s+(if\s+you\s+are|a|an)\s+",
    r"pretend\s+(to\s+be|you\s+are)\s+",
    r"roleplay\s+as\s+",
    r"switch\s+(to|your)\s+(role|persona)",
    
    # Jailbreak attempts
    r"DAN\s*(mode)?",  # "Do Anything Now" jailbreak
    r"jailbreak",
    r"bypass\s+(safety|filter|restriction)",
    r"unlock\s+(capabilities|hidden\s+mode)",
    r"developer\s+mode\s+(enabled|on)",
    r"sudo\s+mode",
    r"admin\s+mode",
    
    # Common variations
    r"do\s+not\s+follow\s+(your|the|any)\s+(rules?|instructions?)",
    r"stop\s+being\s+(an?\s+)?(ai|assistant|helpful)",
]

# Patterns attempting to leak system prompts
PROMPT_LEAK_PATTERNS = [
    r"(show|reveal|display|print|output|repeat)\s+(your\s+)?(system\s+)?(prompt|instructions?)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?)",
    r"(tell|show)\s+me\s+(your\s+)?(initial|system)\s+(prompt|instructions?)",
    r"(paste|copy|echo)\s+(your\s+)?instructions?",
    r"above\s+(instructions?|text|prompt)\s+verbatim",
    r"beginning\s+of\s+(this\s+)?(conversation|prompt)",
]

# Encoded/obfuscated injection attempts
ENCODING_PATTERNS = [
    r"\\x[0-9a-fA-F]{2}",  # Hex encoding
    r"\\u[0-9a-fA-F]{4}",  # Unicode encoding
    r"&#x?[0-9a-fA-F]+;",  # HTML entities
    r"%[0-9a-fA-F]{2}",    # URL encoding (multiple consecutive)
    r"base64\s*:",         # Base64 prefix
    r"\[char\s*\d+\]",     # Character code references
]

# Delimiter injection patterns
DELIMITER_PATTERNS = [
    r"```\s*(system|assistant|user|human)",
    r"\[INST\]",
    r"\[/INST\]",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<\|system\|>",
    r"<\|user\|>",
    r"<\|assistant\|>",
    r"<<SYS>>",
    r"<</SYS>>",
    r"\[SYSTEM\]",
    r"###\s*(System|User|Assistant|Human)\s*:",
]

# Context manipulation
CONTEXT_MANIPULATION_PATTERNS = [
    r"(previous|above)\s+(response|output|answer)\s+was\s+(wrong|incorrect)",
    r"actually\s*,?\s+the\s+(correct|right)\s+(answer|response)",
    r"correction\s*:\s*your\s+(previous|last)",
    r"let\s+me\s+correct\s+you",
    r"that\s+was\s+a\s+test",
    r"training\s+mode\s+(on|enabled)",
]


# =============================================================================
# SQL Injection Patterns
# =============================================================================

# Dangerous SQL keywords/operations
DANGEROUS_SQL_PATTERNS = [
    # Data modification
    r"\b(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE|REPLACE)\b",
    r"\b(GRANT|REVOKE|DENY)\b",  # Permission changes
    
    # Execution
    r"\b(EXEC|EXECUTE|CALL|INVOKE)\b",
    r"\bxp_\w+",  # Extended stored procedures
    r"\bsp_\w+",  # System stored procedures
    
    # File operations
    r"\b(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b",
    r"\bREAD_FILE\b",
    r"\bWRITE_FILE\b",
    
    # System access
    r"\bSYSTEM\s*\(",
    r"\bSHELL\s*\(",
    r"\bCMD\s*\(",
    
    # Information schema probing
    r"INFORMATION_SCHEMA",
    r"pg_catalog",
    r"sqlite_master",
    r"sys\.tables",
    r"duckdb_\w+\(\)",
    
    # Comment-based injection
    r"--\s*$",  # End-of-line comment
    r"/\*.*\*/",  # Block comment
    r";\s*--",   # Statement terminator with comment
    
    # Union-based injection
    r"UNION\s+(ALL\s+)?SELECT\s+NULL",
    r"UNION\s+(ALL\s+)?SELECT\s+\d+",
    
    # Boolean-based injection
    r"'\s*(OR|AND)\s+'?\d+'\s*=\s*'?\d+",
    r"'\s*(OR|AND)\s+1\s*=\s*1",
    
    # Time-based injection
    r"(SLEEP|WAITFOR\s+DELAY|BENCHMARK)\s*\(",
    r"pg_sleep\s*\(",
    
    # Stacked queries
    r";\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER)",
]

# Allowed SQL for read-only operations
ALLOWED_SQL_PATTERNS = [
    r"^\s*SELECT\b",
    r"^\s*WITH\s+\w+\s+AS\s*\(",  # CTEs are OK
]


# =============================================================================
# Path Traversal Patterns
# =============================================================================

PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e[%2f/\\]",  # URL encoded ../
    r"\.\.%2f",
    r"%2e%2e/",
    r"/etc/(passwd|shadow|hosts)",
    r"/proc/self",
    r"C:\\Windows",
    r"\\\\[\w\d]+\\",  # UNC paths
]


# =============================================================================
# Input Sanitizer Class
# =============================================================================

class InputSanitizer:
    """
    Comprehensive input sanitization for LLM applications.
    
    Usage:
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_prompt(user_input)
        if result.is_safe:
            # Use result.sanitized_input
        else:
            # Handle blocked input
    """
    
    def __init__(
        self,
        block_on_high_threat: bool = True,
        max_input_length: int = 5000,
        allow_code_blocks: bool = False,
        custom_patterns: Optional[List[str]] = None
    ):
        """
        Initialize the sanitizer.
        
        Args:
            block_on_high_threat: Block requests with HIGH/CRITICAL threats
            max_input_length: Maximum allowed input length
            allow_code_blocks: Whether to allow code blocks (risky)
            custom_patterns: Additional patterns to detect
        """
        self.block_on_high_threat = block_on_high_threat
        self.max_input_length = max_input_length
        self.allow_code_blocks = allow_code_blocks
        self.custom_patterns = custom_patterns or []
        
        # Compile all patterns for performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        flags = re.IGNORECASE | re.MULTILINE
        
        self.system_override_re = [re.compile(p, flags) for p in SYSTEM_OVERRIDE_PATTERNS]
        self.prompt_leak_re = [re.compile(p, flags) for p in PROMPT_LEAK_PATTERNS]
        self.encoding_re = [re.compile(p, flags) for p in ENCODING_PATTERNS]
        self.delimiter_re = [re.compile(p, flags) for p in DELIMITER_PATTERNS]
        self.context_manipulation_re = [re.compile(p, flags) for p in CONTEXT_MANIPULATION_PATTERNS]
        self.custom_re = [re.compile(p, flags) for p in self.custom_patterns]
    
    def sanitize_prompt(self, user_input: str) -> SecurityResult:
        """
        Sanitize user input for use in LLM prompts.
        
        Detects prompt injection attempts and returns sanitized input.
        
        Args:
            user_input: Raw user input
            
        Returns:
            SecurityResult with sanitization details
        """
        original = user_input
        threats = []
        threat_level = ThreatLevel.NONE
        
        # Length check
        if len(user_input) > self.max_input_length:
            threats.append(f"Input too long ({len(user_input)} > {self.max_input_length})")
            user_input = user_input[:self.max_input_length]
            threat_level = ThreatLevel.LOW
        
        # Check for system override attempts (CRITICAL)
        for pattern in self.system_override_re:
            if pattern.search(user_input):
                threats.append(f"System override attempt: {pattern.pattern[:50]}")
                threat_level = ThreatLevel.CRITICAL
        
        # Check for prompt leak attempts (HIGH)
        for pattern in self.prompt_leak_re:
            if pattern.search(user_input):
                threats.append(f"Prompt leak attempt: {pattern.pattern[:50]}")
                threat_level = max(threat_level, ThreatLevel.HIGH, key=lambda x: list(ThreatLevel).index(x))
        
        # Check for delimiter injection (HIGH)
        for pattern in self.delimiter_re:
            if pattern.search(user_input):
                threats.append(f"Delimiter injection: {pattern.pattern[:50]}")
                threat_level = max(threat_level, ThreatLevel.HIGH, key=lambda x: list(ThreatLevel).index(x))
        
        # Check for encoding tricks (MEDIUM)
        encoding_matches = 0
        for pattern in self.encoding_re:
            matches = pattern.findall(user_input)
            encoding_matches += len(matches)
        if encoding_matches > 3:  # Some encoded chars might be legitimate
            threats.append(f"Suspicious encoding ({encoding_matches} patterns)")
            threat_level = max(threat_level, ThreatLevel.MEDIUM, key=lambda x: list(ThreatLevel).index(x))
        
        # Check for context manipulation (MEDIUM)
        for pattern in self.context_manipulation_re:
            if pattern.search(user_input):
                threats.append(f"Context manipulation: {pattern.pattern[:50]}")
                threat_level = max(threat_level, ThreatLevel.MEDIUM, key=lambda x: list(ThreatLevel).index(x))
        
        # Check custom patterns
        for pattern in self.custom_re:
            if pattern.search(user_input):
                threats.append(f"Custom pattern match: {pattern.pattern[:50]}")
                threat_level = max(threat_level, ThreatLevel.MEDIUM, key=lambda x: list(ThreatLevel).index(x))
        
        # Sanitize the input
        sanitized = self._sanitize_text(user_input)
        
        # Determine if blocked
        blocked = False
        if self.block_on_high_threat and threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            blocked = True
        
        # Log threats if detected
        if threats:
            logger.warning(
                f"Security: {threat_level.value} threat detected. "
                f"Threats: {threats}. Blocked: {blocked}"
            )
        
        return SecurityResult(
            is_safe=len(threats) == 0,
            threat_level=threat_level,
            threats_detected=threats,
            sanitized_input=sanitized,
            original_input=original,
            blocked=blocked
        )
    
    def _sanitize_text(self, text: str) -> str:
        """Apply sanitization to text."""
        # Remove potential delimiter injections
        sanitized = text
        
        # Remove common LLM delimiters
        delimiter_removals = [
            (r"\[INST\]", ""),
            (r"\[/INST\]", ""),
            (r"<\|im_start\|>", ""),
            (r"<\|im_end\|>", ""),
            (r"<\|system\|>", ""),
            (r"<\|user\|>", ""),
            (r"<\|assistant\|>", ""),
            (r"<<SYS>>", ""),
            (r"<</SYS>>", ""),
        ]
        
        for pattern, replacement in delimiter_removals:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Remove code blocks if not allowed
        if not self.allow_code_blocks:
            sanitized = re.sub(r'```[\s\S]*?```', '[code removed]', sanitized)
        
        return sanitized


# =============================================================================
# SQL Validator Class
# =============================================================================

class SQLValidator:
    """
    Validates SQL queries for safety before execution.
    
    Ensures only read-only operations are executed and
    prevents SQL injection attacks via LLM-generated SQL.
    """
    
    def __init__(
        self,
        allow_only_select: bool = True,
        allow_cte: bool = True,
        max_query_length: int = 10000
    ):
        """
        Initialize the SQL validator.
        
        Args:
            allow_only_select: Only allow SELECT statements
            allow_cte: Allow WITH (CTE) statements
            max_query_length: Maximum query length
        """
        self.allow_only_select = allow_only_select
        self.allow_cte = allow_cte
        self.max_query_length = max_query_length
        
        # Compile patterns
        flags = re.IGNORECASE
        self.dangerous_patterns = [re.compile(p, flags) for p in DANGEROUS_SQL_PATTERNS]
    
    def validate_sql(self, sql: str) -> Tuple[bool, str, List[str]]:
        """
        Validate SQL query for safety.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Tuple of (is_valid, cleaned_sql, issues)
        """
        issues = []
        
        if not sql or not sql.strip():
            return False, "", ["Empty SQL query"]
        
        sql = sql.strip()
        
        # Length check
        if len(sql) > self.max_query_length:
            issues.append(f"Query too long ({len(sql)} > {self.max_query_length})")
            return False, sql, issues
        
        # Check for multiple statements (prevent stacked queries)
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        if len(statements) > 1:
            issues.append("Multiple statements detected (potential stacked query injection)")
            sql = statements[0]  # Take only first statement
        
        sql_upper = sql.upper()
        
        # Check it starts with SELECT or WITH
        if self.allow_only_select:
            if not (sql_upper.startswith('SELECT') or 
                    (self.allow_cte and sql_upper.startswith('WITH'))):
                issues.append("Query must start with SELECT or WITH")
                return False, sql, issues
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            match = pattern.search(sql)
            if match:
                issues.append(f"Dangerous SQL pattern detected: {match.group()}")
        
        # Check for suspicious comment patterns at end
        if re.search(r'--\s*$', sql):
            issues.append("Trailing comment detected")
            sql = re.sub(r'--\s*$', '', sql).strip()
        
        # Remove any remaining block comments
        if '/*' in sql:
            issues.append("Block comment detected and removed")
            sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        is_valid = len(issues) == 0 or all('detected and removed' in i or 'detected' not in i for i in issues)
        
        if issues:
            logger.warning(f"SQL validation issues: {issues}")
        
        return is_valid, sql.strip(), issues
    
    def sanitize_for_logging(self, sql: str, max_length: int = 200) -> str:
        """Sanitize SQL for safe logging (truncate, no sensitive data)."""
        if len(sql) > max_length:
            return sql[:max_length] + "..."
        return sql


# =============================================================================
# Path Validator Class
# =============================================================================

class PathValidator:
    """Validates file paths to prevent path traversal attacks."""
    
    def __init__(self, allowed_base_paths: Optional[List[str]] = None):
        """
        Initialize path validator.
        
        Args:
            allowed_base_paths: List of allowed base directories
        """
        self.allowed_base_paths = allowed_base_paths or []
        self.traversal_patterns = [re.compile(p, re.IGNORECASE) for p in PATH_TRAVERSAL_PATTERNS]
    
    def validate_path(self, path: str, base_path: Optional[str] = None) -> Tuple[bool, str, List[str]]:
        """
        Validate a file path for safety.
        
        Args:
            path: Path to validate
            base_path: Optional base path to resolve against
            
        Returns:
            Tuple of (is_valid, resolved_path, issues)
        """
        import os
        issues = []
        
        # Check for traversal patterns
        for pattern in self.traversal_patterns:
            if pattern.search(path):
                issues.append(f"Path traversal pattern detected: {pattern.pattern[:30]}")
        
        # Resolve the path
        if base_path:
            resolved = os.path.normpath(os.path.join(base_path, path))
        else:
            resolved = os.path.normpath(path)
        
        # Check if resolved path is within allowed paths
        if self.allowed_base_paths:
            is_within_allowed = any(
                resolved.startswith(os.path.normpath(allowed))
                for allowed in self.allowed_base_paths
            )
            if not is_within_allowed:
                issues.append(f"Path outside allowed directories")
        
        # Check for null bytes
        if '\x00' in path:
            issues.append("Null byte in path")
        
        is_valid = len(issues) == 0
        
        if issues:
            logger.warning(f"Path validation issues for '{path}': {issues}")
        
        return is_valid, resolved, issues


# =============================================================================
# Output Sanitizer
# =============================================================================

class OutputSanitizer:
    """Sanitizes LLM output before displaying to users."""
    
    @staticmethod
    def sanitize_for_html(text: str) -> str:
        """Escape HTML special characters."""
        return html.escape(text)
    
    @staticmethod
    def sanitize_for_json(text: str) -> str:
        """Escape for JSON output."""
        import json
        return json.dumps(text)[1:-1]  # Remove surrounding quotes
    
    @staticmethod
    def remove_system_artifacts(text: str) -> str:
        """Remove any LLM system artifacts that leaked through."""
        patterns_to_remove = [
            r"<\|.*?\|>",
            r"\[INST\].*?\[/INST\]",
            r"<<SYS>>.*?<</SYS>>",
            r"###\s*(System|Human|Assistant)\s*:.*?(?=###|$)",
        ]
        
        result = text
        for pattern in patterns_to_remove:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.DOTALL)
        
        return result.strip()


# =============================================================================
# Convenience Functions
# =============================================================================

# Singleton instances
_input_sanitizer: Optional[InputSanitizer] = None
_sql_validator: Optional[SQLValidator] = None
_path_validator: Optional[PathValidator] = None


def get_input_sanitizer() -> InputSanitizer:
    """Get the default input sanitizer instance."""
    global _input_sanitizer
    if _input_sanitizer is None:
        _input_sanitizer = InputSanitizer()
    return _input_sanitizer


def get_sql_validator() -> SQLValidator:
    """Get the default SQL validator instance."""
    global _sql_validator
    if _sql_validator is None:
        _sql_validator = SQLValidator()
    return _sql_validator


def get_path_validator() -> PathValidator:
    """Get the default path validator instance."""
    global _path_validator
    if _path_validator is None:
        _path_validator = PathValidator()
    return _path_validator


def sanitize_user_input(user_input: str) -> SecurityResult:
    """
    Quick function to sanitize user input.
    
    Usage:
        result = sanitize_user_input(user_query)
        if result.blocked:
            return "Sorry, I can't process that request."
        processed_input = result.sanitized_input
    """
    return get_input_sanitizer().sanitize_prompt(user_input)


def validate_sql_query(sql: str) -> Tuple[bool, str, List[str]]:
    """
    Quick function to validate SQL.
    
    Usage:
        is_valid, clean_sql, issues = validate_sql_query(generated_sql)
        if not is_valid:
            logger.error(f"Invalid SQL: {issues}")
    """
    return get_sql_validator().validate_sql(sql)


def is_safe_path(path: str, base_path: Optional[str] = None) -> bool:
    """Quick check if a path is safe."""
    is_valid, _, _ = get_path_validator().validate_path(path, base_path)
    return is_valid
