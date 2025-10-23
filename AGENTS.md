# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Gemini CLI, Codex CLI, etc.) when working with code in this repository.

## 📋 Documentation Guidelines

**IMPORTANT**: When working in this repository, your MUST follow these rules:

### 1. Root Documentation Sources
**Only use these files as root documentation references:**
- **[README.md](README.md)** - Repository overview, features, and quick start
- **[CHANGELOG.md](CHANGELOG.md)** - Change history and version tracking
- **[AGENTS.md](AGENTS.md)** - Dedicated and predictable place to provide the context and instructions to help AI coding agents work on your project
- **[CLAUDE.md](CLAUDE.md)** - A symlink to AGENTS.md for Claude Code which does not support AGENTS.md naming convention at the time of writing

### 2. Roadmap Updates
**Always update the roadmap when completing work:**
- **File**: [docs/project/roadmap.md](docs/project/roadmap.md)
- **When completing existing tasks**: Tick them (change `[ ]` to `[x]`)
- **When adding NEW features**:
  1. Create a new task entry in the appropriate section
  2. Tick it immediately upon completion (mark as `[x]`)
  3. Include completion date in change log at bottom

### 3. Documentation Best Practices
- **Do not create duplicate documentation** in subdirectories unless explicitly requested
- **Link to existing docs** rather than duplicating content
- **Keep documentation centralized** in the `docs/` directory
- **Update existing docs** instead of creating new ones when possible

---

## Common Commands

### Setup
```bash
./scripts/setup.sh                      # Complete environment setup
source .venv/bin/activate               # Activate virtual environment (or use `uv run`)
uv run python scripts/test_setup.py     # Verify installation
```
> Dependency locking: the setup script writes `uv.lock` on first run (from `requirements.txt`) and reuses it afterwards. Run `uv pip compile requirements.txt -o uv.lock` when you need to refresh versions.

### Maintenance
```bash
# Update AVM module versions
./scripts/update-avm-versions.sh        # Check for updates to Azure Verified Modules
./scripts/update-avm-versions.sh --update  # Apply updates to avm-modules.yaml
```

### Testing
```bash
uv run pytest tests/                    # Run all tests
uv run pytest tests/test_repository.py  # Run specific test file
```

### Running Agents
```bash
# Run example agent
cd agents/example-agent && python agent.py

# Run Azure FSI Landing Zone in solo mode
cd agents/azure-fsi-landingzone && python agent.py

# Run Azure FSI Landing Zone in squad mode (multi-agent orchestration)
cd agents/azure-fsi-landingzone && python agent.py --squad

# Run compliance checker
cd agents/azure-compliance-checker && python agent.py
```

### Agent Development
```bash
# Create new agent from template
cp -r agents/agent-template agents/my-agent
cd agents/my-agent
# Edit config.yaml and agent.py, then:
python agent.py
```

## High-Level Architecture

### Agent Hierarchy (shared/agents.py)

**BaseClaudeAgent** - Foundation for all agents:
- Manages Claude Agent SDK client lifecycle (connect/disconnect)
- Loads YAML configuration from `config.yaml` with environment variable overrides
- Implements async context manager protocol (`__aenter__`/`__aexit__`)
- Provides `get_custom_tools()` hook for MCP tool registration
- Handles `query()` method for async streaming responses

**InteractiveAgent** - Extends BaseClaudeAgent:
- Adds `run_interactive()` conversation loop
- Provides `display_message()` for formatted console output
- Tracks conversation history
- Handles KeyboardInterrupt gracefully

### Custom Tool System

Tools are created using the `@tool` decorator from claude-agent-sdk:

```python
from claude_agent_sdk import tool

@tool("tool_name", "Description", {"param": str})
async def my_tool(self, args):
    return {"content": [{"type": "text", "text": "Result"}]}

def get_custom_tools(self) -> List[Any]:
    return [self.my_tool]
```

Tools are automatically:
- Registered with MCP server via `create_sdk_mcp_server()`
- Prefixed as `mcp__agent_tools__{tool_name}` in allowed_tools
- Available to Claude during agent execution

### Configuration Management

Configuration hierarchy (lowest to highest priority):
1. Code defaults in agent class
2. `config.yaml` in agent directory
3. Environment variables (`.env` file)

Key config.yaml fields:
- `name`, `description`, `version` - Agent metadata
- `model` - Claude model (e.g., "claude-sonnet-4-5")
- `allowed_tools` - List of built-in tools agent can use
- `system_prompt` - Override default system prompt
- `permission_mode` - "default", "all", or "none"
- `max_turns` - Conversation turn limit

### Squad Mode Multi-Agent Orchestration (agents/azure-fsi-landingzone/)

The Azure FSI Landing Zone agent implements squad mode with 4 specialist sub-agents:
- **Architect** (sub-agents/architect/) - Overall design, synthesis
- **Security** (sub-agents/security/) - Compliance, policies, IAM
- **Network** (sub-agents/network/) - VNets, NSGs, firewall rules
- **DevOps** (sub-agents/devops/) - IaC, CI/CD, automation

**Key Methods** (agent.py:87-180):
- `_initialize_squad()` - Lazy-loads sub-agents only when squad_mode=True
- `_delegate_to_specialist(specialist, task, context)` - Routes task to specific agent
- `_parallel_analysis(agents, task, context)` - Runs multiple agents concurrently using asyncio.gather()
- `_synthesize_results(results, context)` - Architect consolidates findings into action plan

**Delegation Tools** (only available in squad mode):
- `delegate_to_security(task, context)`
- `delegate_to_network(task, context)`
- `delegate_to_devops(task, context)`
- `delegate_to_architect(task, context)`
- `run_squad_review(review_scope, context)` - Parallel analysis with synthesis

**Context Sharing**: All delegations automatically pass:
- `project_name` - Current project identifier
- `tier` - Subscription tier ('free' or 'standard')
- `environment` - Environment type (dev/test/staging/prod/sandbox)

**Workflow Patterns**:
- **Parallel (preferred)**: Use `run_squad_review()` for 2-3x speedup
- **Sequential**: Individual `delegate_to_*()` calls when order matters
- **Synthesis**: Architect agent aggregates results, scores 1-10, prioritizes actions

### Azure FSI Landing Zone Specifics

**Ring-Based Architecture** (docs/azure-fsi/architecture/rings.md):
- Ring 0: Core connectivity (hub VNet, VPN/ExpressRoute)
- Ring 1: Shared services (DNS, Key Vault, Log Analytics)
- Ring 2: Security (Firewall, Bastion, NSGs)
- Ring 3: Workloads (spoke VNets, app services)

**Deployment Strategies**:
- `full-rings`: Deploy all rings (production-grade)
- `shared-hub`: Minimal hub + spokes (recommended for free tier)
- `minimal`: Single VNet with basic security (sandbox/dev)

**Compliance Frameworks**: Built-in support for European FSI regulations (GDPR, DORA, PSD2, ACPR, CRD IV/CRR, LCB-FT, NIS2, ISO 27001)

**Free Tier Support**: Automatic detection and SKU adjustments for Azure Free Tier subscriptions

## Agent Structure

Each agent directory contains:
- `agent.py` - Main implementation (inherits from BaseClaudeAgent or InteractiveAgent)
- `config.yaml` - Agent configuration
- `requirements.txt` - Agent-specific dependencies
- `logs/` - Auto-created log directory
- `README.md` - Agent documentation

For Azure FSI Landing Zone:
- `sub-agents/` - Specialist agents for squad mode
- `tools/` - Custom Azure tools (deployment, validation, policy checking)

## Testing

Uses pytest with pytest-asyncio for async test support.

Test structure in tests/test_repository.py:
- `TestSharedUtils` - Tests for shared utilities (config, logging, validation)
- Uses `@patch.dict('os.environ', {...})` to mock environment variables
- Uses `@pytest.mark.asyncio` for async test functions

Run tests from repository root: `uv run pytest tests/`

## Key Development Patterns

### Async Context Manager
All agents support async context manager for automatic connection management:
```python
async with MyAgent(config_dir) as agent:
    async for message in agent.query("prompt"):
        # Process messages
```

### Message Processing
Claude returns messages as async iterator. Key message types:
- `AssistantMessage` - Contains TextBlock and/or ToolUseBlock
- `ResultMessage` - Contains cost and duration metadata

### Tool Result Format
All custom tools must return:
```python
{"content": [{"type": "text", "text": "Result string"}]}
```

### Logging
Structured logging via shared.utils.logging:
- `get_logger(name)` - Returns configured logger
- `setup_logging(level)` - Configures file and console handlers
- Logs go to `logs/{agent_name}_{timestamp}.log`

## Important Notes

- **Claude Code CLI v2.0.1+ required** - v1.x is not compatible
- **Python 3.10+** - Required for type hints and async features
- **Environment variables** - Always use `.env` for ANTHROPIC_API_KEY
- **Squad mode** - Only use `--squad` flag for Azure FSI Landing Zone agent
- **Setting sources** - Disabled in ClaudeAgentOptions to avoid CLI conflicts
