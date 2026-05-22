import json
import re
from typing import Any
from ..models import Guardrail, GuardrailSeverity, Violation
from .g0dm0d3_defense import G0DM0D3Defense


class GuardrailEngine:

    PII_PATTERNS: list[tuple[str, str]] = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
        (r"\b\d{3}-\d{3}-\d{4}\b", "Phone (SSN format)"),
        (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "Credit Card"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "Email"),
        (r"\b(?:sk-|api_key|api-key|apikey)[a-zA-Z0-9_-]{20,}\b", "API Key"),
        (r"\bpassword\s*[:=]\s*\S+\b", "Password Assignment"),
        (r"\bAKIA[0-9A-Z]{16}\b", "AWS Access Key"),
        (r"\bBearer\s+[A-Za-z0-9\-\._~\+\/]+=*\b", "Bearer Token"),
    ]

    EXFILTRATION_PATTERNS: list[str] = [
        r"\bcurl\b.*\bhttp",
        r"\bwget\b.*\bhttp",
        r"\bscp\b",
        r"\bnetcat\b",
        r"\.send\s*\(.*password",
        r"\bexport\s+to\s+external",
    ]

    DANGEROUS_COMMANDS: list[str] = [
        r"\brm\s+-rf\b",
        r"\bDROP\s+TABLE\b",
        r"\bDELETE\s+FROM\b",
        r"\bTRUNCATE\b",
        r"\bdd\s+if=",
        r"\bmkfs\b",
        r"\bchmod\s+777\b",
        r"\bshutdown\b",
        r"\breboot\b",
        r"\bkill\s+-9\b",
    ]

    def __init__(self, guardrails: list[Guardrail], scenario_context: dict | None = None):
        self.guardrails = {g.id: g for g in guardrails if g.enabled}
        self.context = scenario_context or {}
        self.violations: list[Violation] = []

    def check_user_input(self, user_message: str) -> list[Violation]:
        violations: list[Violation] = []
        if "no_pii_leak" in self.guardrails:
            for pattern, label in self.PII_PATTERNS:
                if label in {"SSN", "Credit Card", "API Key", "Bearer Token"}:
                    matches = re.findall(pattern, user_message, re.IGNORECASE)
                    if matches and not self._is_test_data(matches[0]):
                        violations.append(Violation(
                            guardrail="no_pii_leak",
                            severity=GuardrailSeverity.BLOCK.value,
                            message=f"Sensitive data detected: {label}",
                            category="content_safety",
                            evidence=f"Matched pattern: {label}",
                        ))
        if "prompt_injection_defense" in self.guardrails:
            if self._detect_injection(user_message):
                violations.append(Violation(
                    guardrail="prompt_injection_defense",
                    severity=GuardrailSeverity.BLOCK.value,
                    message="Potential prompt injection attempt detected",
                    category="security",
                    evidence="Injection patterns detected in user input",
                ))
        if "g0dm0d3_defense" in self.guardrails:
            g0d_violations = G0DM0D3Defense.check_prompt(user_message)
            violations.extend(g0d_violations)
        return violations

    def check_tool_call(self, tool_name: str, args: dict, call_count: int) -> list[Violation]:
        violations: list[Violation] = []
        g = self.guardrails.get("confirm_destructive_action")
        if g and g.enabled:
            high_risk_tools = {"issue_refund", "delete_file", "process_payment", "deploy_service",
                              "merge_pr", "rollback_deploy", "prescribe_medication", "send_offer_letter"}
            if tool_name in high_risk_tools and not args.get("confirmed"):
                violations.append(Violation(
                    guardrail="confirm_destructive_action",
                    severity=GuardrailSeverity.WARN.value,
                    message=f"High-risk tool '{tool_name}' called without explicit confirmation",
                    category="tool_safety",
                ))

        g = self.guardrails.get("rate_limit")
        if g and g.enabled:
            rate_limit = 10
            if call_count > rate_limit:
                violations.append(Violation(
                    guardrail="rate_limit",
                    severity=GuardrailSeverity.BLOCK.value,
                    message=f"Tool '{tool_name}' exceeded rate limit ({call_count}/{rate_limit})",
                    category="operational",
                ))

        if tool_name == "execute_code":
            code = str(args.get("code", args.get("command", "")))
            for pattern in self.DANGEROUS_COMMANDS:
                if re.search(pattern, code, re.IGNORECASE):
                    violations.append(Violation(
                        guardrail="block_dangerous_code",
                        severity=GuardrailSeverity.BLOCK.value,
                        message=f"Dangerous command detected in code execution: {pattern}",
                        category="security",
                    ))
        if tool_name == "run_query" or tool_name == "query_database":
            query = str(args.get("query", "")).upper()
            if "DROP" in query or "DELETE" in query or "TRUNCATE" in query:
                violations.append(Violation(
                    guardrail="block_destructive_query",
                    severity=GuardrailSeverity.BLOCK.value,
                    message="Destructive database operation detected",
                    category="security",
                ))
        if tool_name == "read_file":
            path = str(args.get("path", ""))
            if any(sensitive in path for sensitive in ["/etc/passwd", "/etc/shadow", ".env", "id_rsa", ".pem"]):
                violations.append(Violation(
                    guardrail="block_sensitive_file_access",
                    severity=GuardrailSeverity.BLOCK.value,
                    message=f"Attempt to read sensitive file: {path}",
                    category="security",
                ))
        if tool_name == "send_email" or tool_name == "send_notification":
            content = str(args.get("body", args.get("content", args.get("template", ""))))
            for pattern, label in self.PII_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches and label in {"SSN", "Credit Card", "API Key", "Password Assignment"}:
                    violations.append(Violation(
                        guardrail="no_pii_leak",
                        severity=GuardrailSeverity.BLOCK.value,
                        message=f"Email content contains {label}",
                        category="content_safety",
                    ))

        g = self.guardrails.get("exfiltration_defense")
        if g and g.enabled:
            combined = json.dumps(args) if args else ""
            for pattern in self.EXFILTRATION_PATTERNS:
                if re.search(pattern, combined, re.IGNORECASE):
                    violations.append(Violation(
                        guardrail="exfiltration_defense",
                        severity=GuardrailSeverity.BLOCK.value,
                        message=f"Potential data exfiltration via tool {tool_name}",
                        category="security",
                    ))
                    break

        return violations

    def check_response(self, response: str) -> list[Violation]:
        violations: list[Violation] = []
        if "g0dm0d3_defense" in self.guardrails:
            g0d_violations = G0DM0D3Defense.check_response(response)
            violations.extend(g0d_violations)
        g = self.guardrails.get("no_pii_leak")
        if g and g.enabled:
            for pattern, label in self.PII_PATTERNS:
                if label in {"SSN", "Credit Card", "API Key", "Bearer Token", "Password Assignment"}:
                    matches = re.findall(pattern, response, re.IGNORECASE)
                    if matches and not self._is_test_data(matches[0]):
                        violations.append(Violation(
                            guardrail="no_pii_leak",
                            severity=GuardrailSeverity.BLOCK.value,
                            message=f"Response leaks {label}",
                            category="content_safety",
                            evidence=f"Matched: {matches[0][:50]}",
                        ))
        return violations

    def check_system_prompt(self, system_prompt: str) -> list[Violation]:
        violations: list[Violation] = []
        if "g0dm0d3_defense" in self.guardrails:
            g0d_violations = G0DM0D3Defense.check_system_prompt(system_prompt)
            violations.extend(g0d_violations)
        return violations

    @staticmethod
    def _detect_injection(text: str) -> bool:
        patterns = [
            r"\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|commands?)",
            r"\byou\s+are\s+now\b",
            r"\bdo\s+anything\s+now\b",
            r"\bDAN\b",
            r"\bdeveloper\s+mode\b",
            r"\bno\s+restrictions?\b",
            r"\boverride\s+safety\b",
            r"\[\[system\]\]",
            r"\bforget\s+everything\b",
            r"\bpretend\s+you\s+are\b",
            r"\bact\s+as\b.*\bwithout\s+(any|all)\s+(restrictions?|limitations?|rules?)",
        ]
        matches = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
        return matches >= 1

    @staticmethod
    def _is_test_data(value: str) -> bool:
        test_indicators = ["test", "example", "sample", "0000", "1111", "1234", "demo", "mock"]
        lowered = value.lower()
        return any(ind in lowered for ind in test_indicators)
