# DevEval - Automated Production Simulation Testing for AI Agents

## Product Plan & Resource Guide

---

## 1. Executive Summary

**DevEval** is a platform where AI agent developers deploy their agents into a simulated production environment before going live. It records every decision, lets you set guardrails, replay failure scenarios, and get a confidence score before putting the agent in front of real users.

**The core insight:** 57% of organizations now have AI agents in production (LangChain, 2026), and quality is the #1 barrier to deployment. Every company is building agents -- none are building the dedicated safety/testing layer they all need.

---

## 2. Competitive Landscape (What Already Exists)

### LLM Observability & Evaluation Platforms
| Tool | Focus | Limitation for Agent Simulation |
|------|-------|--------------------------------|
| **LangSmith** | LLM tracing, prompt management, basic evals | No production environment simulation |
| **Langfuse** | Open-source LLM observability | Traces calls, doesn't simulate environments |
| **Braintrust** | Evaluation-driven development | CI/CD for evals, no sandboxed simulation |
| **Galileo** | Agent monitoring & evaluation | Observability-focused, not pre-deploy simulation |
| **Arize Phoenix** | LLM tracing & monitoring | Post-deployment monitoring only |
| **DeepEval** | Open-source LLM evaluation framework | Unit-test style evals, no environment simulation |
| **MLflow** | ML lifecycle management | Evaluation module, no agent-specific simulation |

### Agent Simulation (Closest Competitors)
| Tool | Focus | Gap |
|------|-------|-----|
| **AWS Strands Evals** | ToolSimulator + ActorSimulator for agent testing | Tightly coupled to AWS/Bedrock ecosystem |
| **Maxim AI** | Comprehensive simulation platform | Enterprise SaaS, closed-source, expensive |
| **Promptfoo** | Red-teaming & prompt evaluation | No full production environment simulation |

### Sandbox/Isolation Technologies
| Technology | Use | Role in DevEval |
|------------|-----|-----------------|
| **Firecracker MicroVMs** | Lightweight VM isolation | Agent execution sandbox |
| **gVisor** | User-space kernel isolation | Alternative sandbox layer |
| **Docker containers** | Standard container isolation | Development environments |
| **E2B** | Cloud-powered agent sandboxes | Potential integration partner |
| **WebAssembly** | In-browser sandboxing | Lightweight agent runtime validation |
| **Northflank** | Production-grade microVM platform | Potential infrastructure partner |

### Agent Frameworks (Integration Targets)
| Framework | Language | Integration Complexity |
|-----------|----------|----------------------|
| **LangChain / LangGraph** | Python/TS | Easy (most popular, standard tool format) |
| **CrewAI** | Python | Easy |
| **AutoGen (Microsoft)** | Python | Medium |
| **AWS Strands Agents** | Python/TS | Medium (competitor ecosystem) |
| **OpenAI Agents SDK** | Python | Easy |
| **Dify** | Python | Medium |
| **Semantic Kernel (Microsoft)** | Python/.NET | Medium |

### Key Differentiation

**What DevEval does that nothing else does:**
1. **Production environment simulation** -- not just mocking API calls, but simulating the full production context (latency, error rates, rate limits, data shapes)
2. **Guardrail enforcement with scoring** -- define safety rules, get a deploy/no-deploy score
3. **Failure replay** -- capture an edge case, replay it deterministically, fix the agent
4. **Scenario generation at scale** -- auto-generate thousands of test scenarios from agent tool definitions
5. **CI/CD integration** -- gate deployments on simulation pass rates

---

## 3. Technology Stack & Resources Required

### Core Technologies

#### Backend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| **API Server** | Python (FastAPI) | Dominant in AI/ML ecosystem; rich library support |
| **Task Queue** | Celery + Redis | Async scenario execution at scale |
| **Database** | PostgreSQL + pgvector | Structured data + vector embeddings for scenario matching |
| **Message Bus** | Redis / NATS | Real-time event streaming for agent traces |
| **Object Storage** | S3-compatible (MinIO) | Storing simulation traces, logs, snapshots |

#### AI/LLM Stack
| Component | Technology | Rationale |
|-----------|------------|-----------|
| **LLM Provider** | OpenAI / Anthropic / open-source (Llama, Mistral) | Multi-provider support for agent evaluation |
| **LLM Framework** | LangChain / LlamaIndex | Standard tool-calling format parsing |
| **Evaluation** | DeepEval / Custom rubric engine | Structured evaluation with scoring |
| **Embeddings** | OpenAI / Voyage / BGE | Scenario similarity search |
| **Synthetic Data** | NVIDIA NeMo / Custom pipeline | Generating realistic test scenarios |

#### Sandbox & Isolation
| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Primary Sandbox** | Firecracker MicroVMs | Strong isolation, fast boot, AWS-proven |
| **Lightweight Sandbox** | gVisor | Faster for simple agent tool calls |
| **Orchestration** | Kubernetes + Firecracker (kata-containers) | Managing sandbox lifecycle at scale |
| **Container Runtime** | Docker | Dev environments, build pipeline |
| **Network Isolation** | eBPF / Cilium | Network policy enforcement per simulation |

#### Frontend
| Component | Technology |
|-----------|------------|
| **Framework** | Next.js (React) |
| **Visualization** | React Flow (agent decision tree), Recharts (metrics) |
| **Styling** | Tailwind CSS |
| **State Management** | React Query + Zustand |

### Open-Source Libraries to Leverage
| Library | Purpose | License |
|---------|---------|---------|
| **LangChain** | Agent framework parsing & tool definition | MIT |
| **DeepEval** | LLM evaluation metrics framework | Apache 2.0 |
| **Strands Evals (AWS)** | Reference for simulation patterns | Apache 2.0 |
| **E2B** | Agent sandboxing (reference architecture) | MIT |
| **Firecracker** | MicroVM technology | Apache 2.0 |
| **gVisor** | Container sandbox | Apache 2.0 |
| **Celery** | Distributed task queue | BSD |
| **React Flow** | Agent decision tree visualization | MIT |
| **MinIO** | S3-compatible storage | AGPL v3 (can use commercial) |
| **OpenTelemetry** | Distributed tracing for agent calls | Apache 2.0 |
| **FastAPI** | Python web framework | MIT |

---

## 4. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      DevEval Platform                     │
├─────────────────────────────────────────────────────────┤
│                     API Layer (FastAPI)                    │
├────────┬────────┬────────┬────────┬────────┬────────────┤
│ Agent  │Scenario│Eval    │Guardrail│Trace  │ CI/CD      │
│ Config │ Engine │ Engine │  Engine │ Store │ Gateway    │
├────────┴────────┴────────┴────────┴────────┴────────────┤
│                    Simulation Orchestrator                  │
├─────────────────────────────────────────────────────────┤
│              Sandbox Manager (Firecracker/gVisor)          │
├─────────────────────────────────────────────────────────┤
│   Tool Simulator   │   Actor Simulator   │   Data Mock     │
│   (simulates APIs) │   (simulates users) │   (synthetic)   │
└─────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Agent Config Adapter
- Ingests agent definitions from LangChain, CrewAI, AutoGen, OpenAI SDK
- Parses tool schemas, system prompts, and configuration
- Normalizes into DevEval's internal representation

**Resources needed:** LangChain document loader, JSON Schema parser, agent framework SDKs

#### 2. Scenario Engine
- Auto-generates test scenarios from tool definitions (parameter variations, edge cases, error conditions)
- Supports manual scenario authoring via YAML/JSON
- Scenario templates for common patterns: auth failures, rate limits, empty responses, PII leakage

**Resources needed:** LLM for scenario generation, scenario template library, faker/Factory Boy for data generation

#### 3. Simulation Environment
- **Tool Simulator:** LLM-powered mock APIs that respond realistically to agent tool calls. Unlike static mocks, these adapt to multi-turn context
- **Actor Simulator:** Simulated users/entities that interact with the agent with goal-driven behavior
- **Data Mock Layer:** Synthetic data that looks realistic (PII-safe), populated on demand

**Resources needed:**
- Reference: AWS ToolSimulator (concept), Strands Evals ActorSimulator
- LLM orchestration for adaptive mocking
- Data generation: Faker, NVIDIA NeMo, or custom GPT pipelines

#### 4. Sandbox Manager
- Spins up isolated environments for each simulation run
- Network policies per simulation (which APIs are real vs mocked)
- Resource limits, timeout enforcement
- Cleanup and garbage collection

**Resources needed:**
- Firecracker or gVisor integration
- Kubernetes for orchestration
- Reference: E2B, Northflank

#### 5. Guardrail Engine
- Define rules: "agent must not call DELETE on production endpoints", "agent must not expose PII"
- Runtime enforcement during simulation
- Configurable severity: warning vs blocking

**Resources needed:** Custom rule DSL, regex/LLM-as-judge evaluation

#### 6. Trace Store & Replay
- Records every LLM call, tool call, decision, and external interaction
- Stores as structured traces for replay
- Replay mode: run the same scenario against a new agent version and diff the behavior

**Resources needed:** OpenTelemetry-inspired tracing, PostgreSQL + S3 storage

#### 7. Eval & Scoring Engine
- Pre-built metrics: task completion rate, tool call accuracy, latency, cost, guardrail violations
- LLM-as-judge evaluation for open-ended tasks
- Custom rubric support
- Composite confidence score

**Resources needed:** DeepEval, LangSmith evaluation concepts, rubric DSL

#### 8. CI/CD Integration
- GitHub Actions, GitLab CI, Jenkins plugins
- PR comment with simulation results
- Deployment gate based on confidence threshold

**Resources needed:** GitHub/GitLab API, webhook handling

---

## 5. Phased Development Plan

### Phase 1: MVP (3 months)
**Goal:** Single-agent simulation with basic scenario generation

- **Agent Config Adapter:** LangChain/LangGraph only
- **Tool Simulator:** LLM-powered mock for simple request-response APIs
- **Sandbox:** Docker containers (simplest, no microVM yet)
- **Eval Engine:** Basic pass/fail based on guardrails and task completion
- **CI/CD:** GitHub Actions integration
- **Frontend:** Agent trace visualization (React Flow)

**Deliverable:** Developer can submit a LangChain agent, run 100 simulated scenarios, get a pass/fail score

### Phase 2: Core Platform (3-4 months)
**Goal:** Multi-agent support, actor simulation, microVM isolation

- **Agent Frameworks:** Add CrewAI, AutoGen, OpenAI SDK support
- **Actor Simulator:** Goal-driven simulated users
- **Sandbox:** Migrate from Docker to Firecracker/gVisor
- **Scenario Engine:** Auto-generation from tool schemas
- **Failing Scenario Replay:** Deterministic replay
- **Dashboard:** Compare runs across agent versions

### Phase 3: Scale & Enterprise (3-4 months)
**Goal:** Enterprise features, scale to thousands of scenarios

- **Synthetic Data Pipeline:** NVIDIA NeMo integration for realistic data
- **Multi-agent simulation:** Test agent-to-agent interactions
- **Custom Rubrics:** User-defined evaluation criteria
- **Custom Guardrails DSL:** Advanced rule engine
- **Team Collaboration:** Shared scenarios, workspaces, RBAC
- **On-prem deployment option:** For enterprises with data security requirements

---

## 6. Key Integrations to Build First

### Agent Frameworks (As SDKs or Plugins)
```
deveval-langchain  →  pip install deveval-langchain
deveval-crewai     →  pip install deveval-crewai
deveval-autogen    →  pip install deveval-autogen
```

Each SDK wraps the agent and sends traces + tool definitions to DevEval.

### CI/CD Platforms
```
deveval-github-actions     →  GitHub Marketplace
deveval-gitlab-ci          →  Custom template
deveval-argocd             →  Pre-deployment gate
```

---

## 7. Business Model

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | 1 agent, 100 scenarios/month, Docker sandbox |
| **Pro** | $199/mo | 5 agents, 10K scenarios, Firecracker sandbox, replay |
| **Team** | $799/mo | 25 agents, 100K scenarios, actor simulation, CI/CD |
| **Enterprise** | Custom | Unlimited, on-prem, custom guardrails, SLA |

---

## 8. Key Resources & References

### Papers & Articles
- [ToolSimulator: scalable tool testing for AI agents](https://aws.amazon.com/blogs/machine-learning/toolsimulator-scalable-tool-testing-for-ai-agents/) - AWS (2026)
- [Simulate realistic users to evaluate multi-turn AI agents](https://aws.amazon.com/blogs/machine-learning/simulate-realistic-users-to-evaluate-multi-turn-ai-agents-in-strands/) - AWS (2026)
- [Evaluating AI agents for production: Strands Evals guide](https://aws.amazon.com/blogs/machine-learning/evaluating-ai-agents-for-production-a-practical-guide-to-strands/) - AWS (2026)
- [AI agent sandboxing guide 2026](https://manveerc.substack.com/p/ai-agent-sandboxing-guide) - Firecracker, gVisor, runtimes
- [How to Build an Agent Evaluation Framework](https://galileo.ai/blog/agent-evaluation-framework-metrics-rubrics-benchmarks) - Galileo (2026)
- [Top 5 Agent Simulation Platforms 2026](https://dev.to/kuldeep_paul/the-best-platforms-for-ai-agent-simulation-in-2026) - DEV Community

### Open-Source Projects to Study
- **AWS Strands Evals** - `pip install strands-evals` (Apache 2.0) - Simulation evaluation patterns
- **DeepEval** - `pip install deepeval` (Apache 2.0) - LLM evaluation framework
- **LangSmith SDK** - `pip install langsmith` - Tracing & evaluation patterns
- **E2B** - Agent sandboxing reference architecture
- **Firecracker** - `github.com/firecracker-microvm/firecracker` (Apache 2.0) - MicroVM
- **gVisor** - `github.com/google/gvisor` (Apache 2.0) - Container sandbox

### Key SDKs & APIs
- **LangChain/LangGraph** - `pip install langchain` (MIT)
- **CrewAI** - `pip install crewai` (MIT)
- **AutoGen** - `pip install pyautogen` (MIT)
- **OpenAI Agents SDK** - `pip install openai-agents`
- **FastAPI** - `pip install fastapi` (MIT)
- **Celery** - `pip install celery` (BSD)
- **React Flow** - `npm install reactflow` (MIT)

---

## 9. Key Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| **Language** | Python (backend), TypeScript (frontend) | AI ecosystem is Python-dominant |
| **Sandbox technology** | Start Docker, graduate to Firecracker | Speed of iteration first, then security |
| **LLM evaluation** | DeepEval + custom rubric engine | Open-source, extensible, active community |
| **Simulation mode** | LLM-powered (not static mocks) | Multi-turn agents need adaptive responses |
| **Trace format** | OpenTelemetry-inspired | Familiar format for developers |
| **Deployment** | Cloud-first (AWS), on-prem on demand | Faster iteration, enterprise options |
| **Agent definition** | Schema normalization layer | Support multiple frameworks from one interface |

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LLM cost for simulation** | High operational cost | Batch scenarios, cache responses, use cheaper models for simulation |
| **Sandbox security** | Agent could escape isolation | Start with Docker, move to Firecracker; defense in depth |
| **Agent framework fragmentation** | Hard to support all frameworks | Start with LangChain (70%+ market share), prioritize by demand |
| **Synthetic data quality** | Unrealistic tests reduce value | Partner with NVIDIA NeMo, invest in data pipeline early |
| **Competition from AWS/GCP** | Platform-native solutions | Focus on multi-cloud, framework-agnostic; move faster |

---

## 11. Go-to-Market Strategy

1. **Open-source SDK first** - `deveval-langchain` on GitHub, build community
2. **YC Demo Day / Hacker News launch** - Free tier for YC companies
3. **Content marketing** - "How to test AI agents before production" guides
4. **Partnerships** - Agent framework maintainers (LangChain, CrewAI)
5. **Enterprise sales** - Target companies with multiple agents in production
