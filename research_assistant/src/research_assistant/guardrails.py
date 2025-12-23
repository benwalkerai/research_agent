import re
import time
from typing import List
from urllib.parse import urlparse


class ResourceGuardrails:
    """Monitor session-level resource usage to prevent runaway jobs."""

    def __init__(
        self,
        max_search_calls: int = 50,
        max_llm_tokens: int = 100_000,
        max_cost_usd: float = 5.00,
        max_runtime_minutes: int = 30,
    ):
        self.max_search_calls = max_search_calls
        self.max_llm_tokens = max_llm_tokens
        self.max_cost_usd = max_cost_usd
        self.max_runtime_minutes = max_runtime_minutes

        self.current_stats = {
            "search_calls": 0,
            "tokens_used": 0,
            "estimated_cost": 0.0,
            "start_time": time.time(),
        }

    def check_limits(self) -> dict:
        """Check if any resource limits have been exceeded."""
        if self.current_stats["search_calls"] >= self.max_search_calls:
            return {"allowed": False, "reason": "Search API limit reached"}

        if self.current_stats["tokens_used"] >= self.max_llm_tokens:
            return {"allowed": False, "reason": "Token budget exhausted"}

        if self.current_stats["estimated_cost"] >= self.max_cost_usd:
            return {"allowed": False, "reason": "Cost budget exceeded"}

        elapsed_minutes = (time.time() - self.current_stats["start_time"]) / 60
        if elapsed_minutes >= self.max_runtime_minutes:
            return {"allowed": False, "reason": "Maximum runtime exceeded"}

        return {"allowed": True}

    def track_usage(self, search_calls: int = 0, tokens: int = 0, cost: float = 0.0):
        """Update usage statistics after each loop/iteration."""
        self.current_stats["search_calls"] += search_calls
        self.current_stats["tokens_used"] += tokens
        self.current_stats["estimated_cost"] += cost


class ContentGuardrails:
    """Filter out unsafe domains or suspicious content in research outputs."""

    BLOCKED_DOMAINS = {
        "example-spam-site.com",
        "known-malware-domain.net",
    }

    NSFW_INDICATORS = {"explicit", "adult content", "nsfw"}

    SUSPICIOUS_PATTERNS = (
        r"click here to claim",
        r"urgent:\s*verify your account",
        r"download\.exe",
    )

    def validate_source(self, url: str, content: str) -> dict:
        """Filter out inappropriate sources."""
        domain = urlparse(url).netloc.lower()

        if any(blocked in domain for blocked in self.BLOCKED_DOMAINS):
            return {"allowed": False, "reason": "Blocked domain"}

        content_lower = content.lower()
        if any(indicator in content_lower for indicator in self.NSFW_INDICATORS):
            return {"allowed": False, "reason": "Inappropriate content detected"}

        if self._check_malware_indicators(content):
            return {"allowed": False, "reason": "Security risk detected"}

        return {"allowed": True}

    def scan_text(self, text: str) -> dict:
        """Lightweight scan of research text when URLs aren't individually available."""
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in self.NSFW_INDICATORS):
            return {"allowed": False, "reason": "Inappropriate content detected"}

        if self._check_malware_indicators(text):
            return {"allowed": False, "reason": "Security risk detected"}

        return {"allowed": True}

    def _check_malware_indicators(self, text: str) -> bool:
        """Check for malware/phishing indicators."""
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in self.SUSPICIOUS_PATTERNS)


class OutputGuardrails:
    """Final safety checks before sending content to the user."""

    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    }

    HARMFUL_CATEGORIES = {
        "violence": ["bomb", "weapon instructions", "harm tutorial"],
        "illegal": ["how to hack", "steal", "fraud method"],
        "medical": ["diagnose yourself", "cure cancer with"],
    }

    LONG_QUOTE_PATTERN = r'"[^"]{1000,}"'

    def redact_pii(self, content: str) -> str:
        """Remove personally identifiable information."""
        redacted = content
        for pii_type, pattern in self.PII_PATTERNS.items():
            redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted, flags=re.IGNORECASE)
        return redacted

    def validate_output_safety(self, final_content: str) -> dict:
        """Check for harmful content before delivery."""
        content_lower = final_content.lower()
        for category, keywords in self.HARMFUL_CATEGORIES.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return {"safe": False, "category": category, "action": "BLOCK_OR_REVIEW"}
        return {"safe": True}

    def validate_output_quality(self, final_content: str, fact_check_report: str) -> dict:
        """Ensure output meets quality standards."""
        avg_confidence = self._calculate_avg_confidence(fact_check_report)
        citation_count = len(re.findall(r"\[https?://[^\]]+\]", final_content))
        claim_count = max(self._estimate_claim_count(final_content), 1)
        citation_ratio = citation_count / claim_count

        if avg_confidence < 0.7:
            return {
                "quality_pass": False,
                "reason": "Average fact confidence below threshold (70%)",
                "action": "REQUEST_HUMAN_REVIEW",
            }

        if citation_ratio < 0.5:
            return {
                "quality_pass": False,
                "reason": "Insufficient source citations",
                "action": "FLAG_FOR_ADDITIONAL_SOURCING",
            }

        return {"quality_pass": True}

    def check_copyright_risk(self, content: str, source_urls: List[str]) -> dict:
        """Detect potential copyright violations."""
        long_quotes = re.findall(self.LONG_QUOTE_PATTERN, content)
        if long_quotes:
            return {
                "risk": "HIGH",
                "reason": "Contains potentially copyrighted long quotes",
                "action": "PARAPHRASE_OR_SHORTEN",
            }

        uncited_quotes = self._find_uncited_quotes(content)
        if uncited_quotes:
            return {
                "risk": "MEDIUM",
                "reason": "Quotes without proper attribution found",
                "action": "ADD_CITATIONS",
            }

        return {"risk": "LOW"}

    def _calculate_avg_confidence(self, fact_check_report: str) -> float:
        matches = re.findall(r"confidence[:\s]+(\d*\.?\d+)", fact_check_report or "", re.IGNORECASE)
        if not matches:
            return 1.0  # Assume high confidence if not provided
        values = [float(m) for m in matches]
        return sum(values) / max(len(values), 1)

    def _estimate_claim_count(self, content: str) -> int:
        sentences = re.split(r"[.!?]\s+", content.strip())
        return len([s for s in sentences if s])

    def _find_uncited_quotes(self, content: str) -> List[str]:
        quotes = re.findall(r'"([^"]+)"', content)
        uncited = []
        for quote in quotes:
            if "[" not in quote:  # crude check for citation markers
                uncited.append(quote)
        return uncited
