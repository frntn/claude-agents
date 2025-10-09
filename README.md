# Claude Agents Repository

A collection of Claude agents built using the official **Claude Agent SDK** for Python.

## Repository Structure

```
claude-agents/
├── agents/                      # Individual agent implementations
│   ├── agent-template/          # Template for new agents
│   ├── example-agent/           # Example agent with custom tools
│   ├── azure-fsi-landingzone/   # Mono-agent for FSI Landing Zones
│   └── azure-fsi-landingzone-squad/ # Multi-agent squad for FSI
├── shared/                      # Shared utilities and base classes
│   ├── agents.py               # BaseClaudeAgent and InteractiveAgent classes
│   ├── utils/                  # Common utility functions
│   └── configs/                # Shared configuration files
├── docs/                       # Documentation
│   ├── getting-started.md      # Getting started guide
│   ├── agents/                 # Agent development docs
│   │   ├── overview.md         # Agent overview and catalog
│   │   └── creating-agents.md  # How to create agents
│   └── azure-fsi/              # Azure FSI Landing Zone docs
│       ├── README.md           # FSI agents overview
│       ├── architecture/       # Architecture documentation
│       └── guides/             # Usage guides
├── scripts/                    # Build and deployment scripts
└── tests/                      # Test files
```

## Features

✨ **Built with Claude Agent SDK**: Uses the official Python SDK for Claude agents
🛠️ **Custom Tools**: Easy creation of custom MCP tools using decorators
🤖 **Interactive Agents**: Ready-to-use interactive conversation interfaces
⚙️ **Configuration Management**: YAML-based configuration with environment overrides
📝 **Comprehensive Logging**: Structured logging with file and console output
🎯 **Type Safety**: Full type hints and validation

## AI Coding Agent Support

This repository includes **[AGENTS.md](AGENTS.md)** - a standardized guidance file for AI coding agents following the [agents.md](https://agents.md) open format.

**What's included:**
- Common development commands (setup, testing, running agents)
- High-level architecture overview (agent hierarchy, squad mode orchestration)
- Azure FSI Landing Zone specifics (ring-based deployment, compliance)
- Testing patterns and key development practices

**Compatibility:**
- ✅ **AGENTS.md** - Works with Gemini CLI, Codex CLI, Cursor, and other agents supporting the standard
- ✅ **CLAUDE.md** - Symlinked to AGENTS.md for Claude Code compatibility (until [native support](https://github.com/anthropics/claude-code/issues/6235) is added)

When using AI coding assistants with this repository, they'll automatically read AGENTS.md for project-specific context and instructions.

## Quick Start

1. **Install [uv](https://docs.astral.sh/uv/) (once) and run setup**
   ```bash
   git clone <repository-url>
   cd claude-agents
   ./scripts/setup.sh
   source .venv/bin/activate  # Or use `uv run <command>` without activating
   ```

2. **Configure your API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

3. **Try the example agent**
   ```bash
   cd agents/example-agent
   python agent.py
   ```

4. **Create your first custom agent**
   ```bash
   cp -r agents/agent-template agents/my-first-agent
   cd agents/my-first-agent
   # Edit config.yaml and agent.py
   python agent.py
   ```

### Dependency Management with uv
- On first run, the setup script resolves the newest compatible packages from `requirements.txt` and writes `uv.lock`.
- Subsequent installs automatically use `uv.lock` for reproducible versions.
- Refresh the lock file whenever you want to upgrade:
  ```bash
  uv pip compile requirements.txt -o uv.lock
  ```
- Commit `uv.lock` so teammates and CI get identical environments.

## Makefile Tasks

Common workflows are exposed via the root `Makefile`:

- Run `make help` to list available commands.
- Use `make setup` for the bootstrap script.
- Run `make test` for the primary pytest suite in `tests/`.
- Run `make test-azure-fsi` to execute the Azure FSI Landing Zone checks, including AVM template validation.
- Override `AZURE_BICEP_BUILD_TIMEOUT` when running `make test-azure-fsi` if `az bicep build` needs more than the default 120 seconds, and set `AZURE_BICEP_KEEP_TEMPLATES=1` to keep rendered `.bicep`/`.json` files for debugging.

## Available Agents

### Templates & Examples
- **🏗️ [agent-template](agents/agent-template/)**: Complete template for creating new agents with custom tools
- **🎯 [example-agent](agents/example-agent/)**: Feature-rich example showing Claude Agent SDK capabilities

### Azure FSI Landing Zone Agent
- **🏦 [azure-fsi-landingzone](docs/azure-fsi/)**: Azure FSI Landing Zone deployment agent with two operational modes:
  - **Solo Mode** (default): Quick template generation and simple deployments
  - **Squad Mode** (`--squad` flag): Multi-agent collaboration with specialist expertise (Architect, DevOps, Security, Network)

**Choose your mode:**
- **Solo Mode**: Best for quick template generation and simple deployments
- **Squad Mode**: Best for production readiness, compliance reviews, and expert analysis

See the [Azure FSI Documentation](docs/azure-fsi/) for detailed comparison and guides.

### Compliance Tools
- **📋 [azure-compliance-checker](agents/azure-compliance-checker/)**: Automated compliance validation for French FSI regulations (ACPR, CRD IV/CRR, LCB-FT, RGPD, ISO 27001, DORA, NIS2)

## Requirements

- **Python 3.10+**
- **Node.js 18+** (for Claude Code CLI)
- **Claude Code CLI v2.0.1+**: `npm install -g @anthropic-ai/claude-code@latest` ⚠️ **REQUIRED**
- **uv 0.4+** (Python packaging tool)
- **Claude Agent SDK v0.1.0+** (install with `uv pip sync uv.lock` or bootstrap with `uv pip install -r requirements.txt`)
- **Anthropic API key** (from https://console.anthropic.com)

**Important**: Claude Code CLI v2.0.1+ is required for the claude-agent-sdk to work. Version 1.x is not compatible.

## Key Components

### BaseClaudeAgent
Base class providing:
- Claude Agent SDK integration
- Configuration management  
- Custom tool support
- Async context manager support

### InteractiveAgent
Extends BaseClaudeAgent with:
- Interactive conversation loops
- Message display formatting
- Command-line interface

### Custom Tools
Create custom tools using the `@tool` decorator:

```python
from claude_agent_sdk import tool

@tool("my_tool", "Description of what it does", {"param": str})
async def my_custom_tool(args):
    return {"content": [{"type": "text", "text": "Result"}]}
```

## Documentation

### Getting Started
- **[Getting Started Guide](docs/getting-started.md)**: Repository setup and environment configuration
- **[Agent Overview](docs/agents/overview.md)**: Learn about Claude agents and available implementations
- **[Creating Agents](docs/agents/creating-agents.md)**: Comprehensive guide to building custom agents

### Specialized Documentation
- **[Azure FSI Landing Zone](docs/azure-fsi/)**: Complete documentation for FSI Landing Zone agents
  - Architecture guides (Ring-based deployment, Multi-agent squad)
  - Quick start guides (Mono-agent, Squad)
  - Deployment workflows and best practices

### Reference
- **[Repository Architecture](ARCHITECTURE.md)**: Overall repository architecture
- **[Roadmap](ROADMAP.md)**: Future plans and features

## Contributing

1. Use the `agent-template` as a starting point
2. Follow the established directory structure
3. Add comprehensive documentation (see [docs/agents/creating-agents.md](docs/agents/creating-agents.md))
4. Include tests for custom functionality
5. Use type hints throughout

## License

[Add your license information here]
