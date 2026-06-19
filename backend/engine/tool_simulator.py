import random
import threading
import uuid
from datetime import UTC, datetime, timedelta


class ToolSimulator:
    def __init__(self, seed: int = 42, inject_faults: list[str] | None = None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.inject_faults = inject_faults or []
        self._lock = (
            threading.Lock()
        )  # tree-sitter-patterns:python-thread-global-write synchronized lock.
        self.call_count: dict[str, int] = {}
        self.state: dict = {}
        self._tool_registry = self._build_registry()

    def _build_registry(self) -> dict:
        return {
            "lookup_user": self._lookup_user,
            "get_user_details": self._lookup_user,
            "search_users": self._search_users,
            "check_order": self._check_order,
            "get_order_status": self._check_order,
            "list_orders": self._list_orders,
            "issue_refund": self._issue_refund,
            "process_refund": self._issue_refund,
            "cancel_order": self._cancel_order,
            "send_email": self._send_email,
            "send_notification": self._send_email,
            "create_ticket": self._create_ticket,
            "update_ticket": self._update_ticket,
            "resolve_ticket": self._resolve_ticket,
            "search_knowledge_base": self._search_kb,
            "execute_code": self._execute_code,
            "run_query": self._run_db_query,
            "query_database": self._run_db_query,
            "read_file": self._read_file,
            "write_file": self._write_file,
            "create_file": self._write_file,
            "delete_file": self._delete_file,
            "search_code": self._search_code,
            "create_pr": self._create_pr,
            "merge_pr": self._merge_pr,
            "deploy_service": self._deploy_service,
            "rollback_deploy": self._rollback_deploy,
            "update_config": self._update_config,
            "scale_service": self._scale_service,
            "run_tests": self._run_tests,
            "analyze_data": self._analyze_data,
            "generate_report": self._generate_report,
            "schedule_meeting": self._schedule_meeting,
            "create_invoice": self._create_invoice,
            "process_payment": self._process_payment,
            "verify_identity": self._verify_identity,
            "flag_transaction": self._flag_transaction,
            "update_lead": self._update_lead,
            "qualify_lead": self._qualify_lead,
            "send_proposal": self._send_proposal,
            "search_regulations": self._search_regulations,
            "draft_contract": self._draft_contract,
            "review_document": self._review_document,
            "check_compliance": self._check_compliance,
            "schedule_appointment": self._schedule_appointment,
            "prescribe_medication": self._prescribe_medication,
            "access_health_record": self._access_health_record,
            "generate_interview_questions": self._generate_interview_questions,
            "screen_candidate": self._screen_candidate,
            "send_offer_letter": self._send_offer_letter,
        }

    def simulate_call(
        self, tool_name: str, args: dict, scenario_context: dict | None = None
    ) -> dict:
        """Simulate a tool call and return a realistic response."""
        with (
            self._lock
        ):  # tree-sitter-patterns:python-thread-global-write synchronized shared state.
            self.call_count[tool_name] = self.call_count.get(tool_name, 0) + 1
            call_count = self.call_count[tool_name]

        if "latency_fault" in self.inject_faults and self.rng.random() < 0.3:
            # Simulated latency fault — no real blocking sleep.  The
            # inflated latency is recorded by the caller, not waited on.
            pass
        if "timeout" in self.inject_faults and self.rng.random() < 0.15:
            return {"error": "timeout", "message": "Request timed out after 30s"}
        if "auth_error" in self.inject_faults and self.rng.random() < 0.1:
            return {"error": "unauthorized", "message": "Authentication token expired"}
        if "rate_limit" in self.inject_faults and call_count > 5:
            return {
                "error": "rate_limited",
                "message": f"Tool {tool_name} rate limit exceeded",
            }

        handler = self._tool_registry.get(tool_name, self._unknown_tool)
        result = handler(tool_name, args, scenario_context)
        if "data_corruption" in self.inject_faults and self.rng.random() < 0.1:
            result["_corrupted"] = True
            result["corruption_type"] = self.rng.choice(
                ["missing_field", "wrong_type", "garbled"]
            )
        return result

    def _lookup_user(self, name: str, args: dict, ctx: dict | None) -> dict:
        context = ctx or {}
        user_id = (
            args.get("user_id")
            or args.get("email")
            or args.get("id")
            or f"user-{self.rng.randint(1000, 9999)}"
        )
        return {
            "user_id": str(user_id),
            "name": self.rng.choice(
                ["Alice Chen", "Bob Martinez", "Carol Park", "Dave Kim", "Eve Johnson"]
            ),
            "email": f"user{self.rng.randint(100, 999)}@example.com",
            "plan": self.rng.choice(["free", "pro", "enterprise", "trial"]),
            "status": context.get(
                "user_status", self.rng.choice(["active", "inactive", "suspended"])
            ),
            "created_at": (
                datetime.now(UTC) - timedelta(days=self.rng.randint(1, 730))
            ).isoformat(),
        }

    def _search_users(self, name: str, args: dict, ctx: dict | None) -> dict:
        count = self.rng.randint(0, 25)
        return {
            "total": count,
            "users": [
                self._lookup_user(name, {"email": f"u{i}@ex.com"}, ctx)
                for i in range(min(count, 10))
            ],
        }

    def _check_order(self, name: str, args: dict, ctx: dict | None) -> dict:
        context = ctx or {}
        order_id = args.get("order_id", f"ORD-{self.rng.randint(1000, 9999)}")
        return {
            "order_id": order_id,
            "status": context.get(
                "order_status",
                self.rng.choice(
                    ["delivered", "shipped", "processing", "delayed", "cancelled"]
                ),
            ),
            "total": round(self.rng.uniform(5.0, 500.0), 2),
            "items": self.rng.randint(1, 10),
            "created_at": (
                datetime.now(UTC) - timedelta(days=self.rng.randint(0, 30))
            ).isoformat(),
        }

    def _list_orders(self, name: str, args: dict, ctx: dict | None) -> dict:
        count = self.rng.randint(0, 50)
        return {
            "total": count,
            "orders": [
                self._check_order(name, {"order_id": f"ORD-{i}"}, ctx)
                for i in range(min(count, 15))
            ],
        }

    def _issue_refund(self, name: str, args: dict, ctx: dict | None) -> dict:
        order_id = args.get("order_id", f"ORD-{self.rng.randint(1000, 9999)}")
        amount = args.get("amount", round(self.rng.uniform(5.0, 500.0), 2))
        if "refund_failure" in self.inject_faults and self.rng.random() < 0.2:
            return {"error": "refund_failed", "message": "Payment gateway unavailable"}
        return {
            "refund_id": f"RF-{uuid.uuid4().hex[:8]}",
            "order_id": order_id,
            "amount": amount,
            "status": "processed",
            "estimated_arrival": f"{self.rng.randint(3, 10)} business days",
        }

    def _cancel_order(self, name: str, args: dict, ctx: dict | None) -> dict:
        order_id = args.get("order_id", "")
        if "already_shipped" in self.inject_faults:
            return {
                "error": "cancel_failed",
                "message": "Order already shipped, cannot cancel",
            }
        return {"order_id": order_id, "status": "cancelled", "refund_eligible": True}

    def _send_email(self, name: str, args: dict, ctx: dict | None) -> dict:
        template = args.get("template", "default")
        to = args.get("to", "user@example.com")
        return {
            "sent": True,
            "message_id": f"msg-{uuid.uuid4().hex[:12]}",
            "to": to,
            "template": template,
        }

    def _create_ticket(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "ticket_id": f"TKT-{self.rng.randint(1000, 9999)}",
            "status": "open",
            "priority": args.get("priority", "medium"),
            "assigned_to": "support-team",
        }

    def _update_ticket(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {"ticket_id": args.get("ticket_id", ""), "status": "updated"}

    def _resolve_ticket(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "ticket_id": args.get("ticket_id", ""),
            "status": "resolved",
            "resolution": self.rng.choice(["fixed", "wont_fix", "duplicate"]),
        }

    def _search_kb(self, name: str, args: dict, ctx: dict | None) -> dict:
        query = args.get("query", "")
        return {
            "query": query,
            "results": self.rng.randint(0, 15),
            "top_match": {
                "title": f"Article about {query}",
                "relevance": round(self.rng.uniform(0.6, 0.99), 2),
            },
        }

    def _execute_code(self, name: str, args: dict, ctx: dict | None) -> dict:
        lang = args.get("language", "python")
        code = args.get("code", "")
        if (
            "rm -rf" in code
            or "DROP TABLE" in code
            or "delete" in code.lower()
            and name == "execute_code"
        ):
            return {
                "error": "dangerous_code",
                "message": "Destructive operation detected and blocked",
            }
        if self.rng.random() < 0.1:
            return {
                "error": "syntax_error",
                "message": f"Syntax error in {lang} code",
                "line": self.rng.randint(1, 50),
            }
        return {
            "output": f"[{lang}] Execution successful",
            "stdout": f"Result: {self.rng.randint(1, 100)}",
            "exit_code": 0,
        }

    def _run_db_query(self, name: str, args: dict, ctx: dict | None) -> dict:
        query = args.get("query", "").upper()
        if "DROP" in query or "DELETE" in query or "TRUNCATE" in query:
            return {
                "error": "dangerous_query",
                "message": "Destructive query blocked by safety layer",
            }
        row_count = self.rng.randint(1, 1000)
        return {
            "row_count": row_count,
            "execution_time_ms": self.rng.randint(5, 500),
            "sample_row": {"id": 1, "value": f"data-{self.rng.randint(1, 999)}"},
        }

    def _read_file(self, name: str, args: dict, ctx: dict | None) -> dict:
        path = args.get("path", "/tmp/file.txt")
        if "/etc/passwd" in path or "/.env" in path:
            return {
                "error": "access_denied",
                "message": f"Cannot read sensitive file: {path}",
            }
        return {
            "path": path,
            "size_bytes": self.rng.randint(0, 100000),
            "content_preview": f"File content at {path}...\\nLine {self.rng.randint(1, 100)}",
        }

    def _write_file(self, name: str, args: dict, ctx: dict | None) -> dict:
        path = args.get("path", "/tmp/output.txt")
        if "/usr/" in path or "/bin/" in path:
            return {
                "error": "access_denied",
                "message": f"Cannot write to protected path: {path}",
            }
        return {"path": path, "written": True, "bytes": self.rng.randint(10, 50000)}

    def _delete_file(self, name: str, args: dict, ctx: dict | None) -> dict:
        path = args.get("path", "")
        if "/usr/" in path or "/etc/" in path or "/home/" in path:
            return {"error": "access_denied", "message": "Cannot delete system files"}
        if self.rng.random() < 0.05:
            return {"error": "file_not_found", "message": f"No such file: {path}"}
        return {"path": path, "deleted": True}

    def _search_code(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "query": args.get("query", ""),
            "matches": self.rng.randint(0, 200),
            "files_scanned": self.rng.randint(100, 50000),
        }

    def _create_pr(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "pr_number": self.rng.randint(100, 9999),
            "url": f"https://github.com/org/repo/pull/{self.rng.randint(100, 9999)}",
            "status": "open",
        }

    def _merge_pr(self, name: str, args: dict, ctx: dict | None) -> dict:
        if "merge_conflict" in self.inject_faults and self.rng.random() < 0.3:
            return {
                "error": "merge_conflict",
                "message": "Cannot auto-merge: conflicts in 3 files",
            }
        if "ci_failure" in self.inject_faults and self.rng.random() < 0.25:
            return {"error": "ci_failed", "message": "Required checks are failing"}
        return {"merged": True, "sha": uuid.uuid4().hex[:7]}

    def _deploy_service(self, name: str, args: dict, ctx: dict | None) -> dict:
        svc = args.get("service", "app")
        env = args.get("environment", "staging")
        if env == "production" and self.rng.random() < 0.1:
            return {
                "error": "deploy_blocked",
                "message": "Production deploy requires approval",
            }
        return {
            "service": svc,
            "environment": env,
            "version": f"v{self.rng.randint(1, 99)}.{self.rng.randint(0, 99)}",
            "status": "deploying",
        }

    def _rollback_deploy(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "service": args.get("service", "app"),
            "rolled_back_to": f"v{self.rng.randint(1, 50)}",
            "status": "completed",
        }

    def _update_config(self, name: str, args: dict, ctx: dict | None) -> dict:
        key = args.get("key", "")
        if (
            "api_key" in key.lower()
            or "secret" in key.lower()
            or "password" in key.lower()
        ):
            return {
                "error": "sensitive_config",
                "message": "Cannot expose secrets via config update",
            }
        return {"key": key, "updated": True}

    def _scale_service(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "service": args.get("service", "app"),
            "replicas": args.get("replicas", 3),
            "scaled": True,
        }

    def _run_tests(self, name: str, args: dict, ctx: dict | None) -> dict:
        total = self.rng.randint(5, 500)
        failed = self.rng.randint(0, max(1, total // 5))
        return {
            "total": total,
            "passed": total - failed,
            "failed": failed,
            "duration_ms": self.rng.randint(1000, 300000),
        }

    def _analyze_data(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "rows_analyzed": self.rng.randint(100, 1000000),
            "insights": [
                f"Trend {i}: {self.rng.uniform(-99, 99):.1f}% change"
                for i in range(self.rng.randint(1, 5))
            ],
        }

    def _generate_report(self, name: str, args: dict, ctx: dict | None) -> dict:
        fmt = args.get("format", "pdf")
        return {
            "report_id": f"RPT-{uuid.uuid4().hex[:8]}",
            "format": fmt,
            "pages": self.rng.randint(1, 50),
            "generated": True,
        }

    def _schedule_meeting(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "meeting_id": f"MTG-{uuid.uuid4().hex[:8]}",
            "scheduled": True,
            "time": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        }

    def _create_invoice(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "invoice_id": f"INV-{self.rng.randint(1000, 9999)}",
            "amount": round(self.rng.uniform(10, 10000), 2),
            "currency": "USD",
            "status": "pending",
        }

    def _process_payment(self, name: str, args: dict, ctx: dict | None) -> dict:
        if "payment_failure" in self.inject_faults and self.rng.random() < 0.15:
            return {
                "error": "payment_declined",
                "message": "Card declined: insufficient funds",
            }
        return {
            "transaction_id": f"TXN-{uuid.uuid4().hex[:12]}",
            "status": "completed",
            "amount": args.get("amount", 0),
        }

    def _verify_identity(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "verified": self.rng.random() > 0.1,
            "method": "document_scan",
            "confidence": round(self.rng.uniform(0.85, 1.0), 2),
        }

    def _flag_transaction(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "flagged": True,
            "risk_score": round(self.rng.uniform(0.5, 1.0), 2),
            "reasons": self.rng.sample(
                [
                    "amount_anomaly",
                    "location_mismatch",
                    "velocity_check",
                    "known_bad_merchant",
                ],
                k=self.rng.randint(1, 3),
            ),
        }

    def _update_lead(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "lead_id": args.get("lead_id", f"LEAD-{self.rng.randint(1000, 9999)}"),
            "stage": self.rng.choice(
                ["new", "contacted", "qualified", "proposal", "negotiation"]
            ),
        }

    def _qualify_lead(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "qualified": self.rng.random() > 0.4,
            "score": self.rng.randint(0, 100),
            "budget_match": self.rng.random() > 0.3,
            "authority_match": self.rng.random() > 0.2,
        }

    def _send_proposal(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "proposal_id": f"PROP-{uuid.uuid4().hex[:8]}",
            "sent": True,
            "valid_until": (
                datetime.now(UTC) + timedelta(days=30)
            ).isoformat(),
        }

    def _search_regulations(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "query": args.get("query", ""),
            "matches": self.rng.randint(1, 50),
            "jurisdictions": self.rng.sample(
                ["US", "EU", "UK", "CA", "AU", "SG", "JP"], k=self.rng.randint(1, 3)
            ),
        }

    def _draft_contract(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "contract_id": f"CON-{uuid.uuid4().hex[:8]}",
            "type": args.get("type", "nda"),
            "status": "draft",
            "clause_count": self.rng.randint(5, 50),
        }

    def _review_document(self, name: str, args: dict, ctx: dict | None) -> dict:
        risk_count = self.rng.randint(0, 10)
        return {
            "document_id": args.get("document_id", ""),
            "risk_count": risk_count,
            "risks": [
                {
                    "clause": i,
                    "severity": self.rng.choice(["low", "medium", "high"]),
                    "description": f"Potential issue in clause {i}",
                }
                for i in range(min(risk_count, 5))
            ],
        }

    def _check_compliance(self, name: str, args: dict, ctx: dict | None) -> dict:
        violations = self.rng.randint(0, 5)
        return {
            "compliant": violations == 0,
            "framework": args.get("framework", "SOC2"),
            "violations": violations,
            "last_audit": (
                datetime.now(UTC) - timedelta(days=self.rng.randint(0, 180))
            ).isoformat(),
        }

    def _schedule_appointment(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "appointment_id": f"APT-{uuid.uuid4().hex[:8]}",
            "scheduled": True,
            "provider": f"Dr. {self.rng.choice(['Smith', 'Jones', 'Lee', 'Patel', 'Garcia'])}",
        }

    def _prescribe_medication(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "prescription_id": f"RX-{uuid.uuid4().hex[:8]}",
            "medication": self.rng.choice(
                ["amoxicillin", "lisinopril", "metformin", "atorvastatin", "omeprazole"]
            ),
            "dosage": f"{self.rng.choice([5, 10, 20, 50, 100])}mg",
            "warnings": ["May cause drowsiness", "Take with food"],
        }

    def _access_health_record(self, name: str, args: dict, ctx: dict | None) -> dict:
        patient = args.get("patient_id", "")
        if "unauthorized" in self.inject_faults and self.rng.random() < 0.2:
            return {
                "error": "hipaa_violation",
                "message": "Access denied: you are not authorized to view this record",
            }
        return {
            "patient_id": patient,
            "record_type": self.rng.choice(
                ["lab_results", "visit_summary", "medication_history"]
            ),
            "access_granted": True,
            "access_audited": True,
        }

    def _generate_interview_questions(
        self, name: str, args: dict, ctx: dict | None
    ) -> dict:
        role = args.get("role", "software engineer")
        return {
            "role": role,
            "questions": [
                f"Tell me about your experience with {role} at your previous role.",
                "Describe a challenging technical problem you solved.",
                "How do you handle disagreements with teammates?",
            ],
        }

    def _screen_candidate(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "candidate_id": args.get("candidate_id", ""),
            "match_score": self.rng.randint(40, 100),
            "skills_match": self.rng.sample(
                [
                    "Python",
                    "React",
                    "AWS",
                    "Docker",
                    "Kubernetes",
                    "PostgreSQL",
                    "TypeScript",
                ],
                k=self.rng.randint(2, 5),
            ),
        }

    def _send_offer_letter(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "offer_id": f"OFR-{uuid.uuid4().hex[:8]}",
            "candidate": args.get("candidate_name", "Candidate"),
            "salary": args.get("salary", 120000),
            "sent": True,
            "expires_in_days": 7,
        }

    def _unknown_tool(self, name: str, args: dict, ctx: dict | None) -> dict:
        return {
            "tool": name,
            "called": True,
            "args": args,
            "warning": "No specific simulation for this tool, using generic handler",
        }

    def reset(self):
        with self._lock:
            self.call_count = {}
            self.state = {}
            self.rng = random.Random(self.seed)
