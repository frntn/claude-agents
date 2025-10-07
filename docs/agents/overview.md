# Agents Documentation

This repository provides a comprehensive framework for building Claude agents using the official Claude Agent SDK. This document serves as your guide to understanding, developing, and maintaining agents within this codebase.

## Table of Contents

1. [What are Claude Agents?](#what-are-claude-agents)
2. [Agent Architecture](#agent-architecture)
3. [Available Agents](#available-agents)
4. [Creating Your First Agent](#creating-your-first-agent)
5. [Resources](#resources)

## What are Claude Agents?

Claude agents are autonomous AI systems built on top of Claude that can:

- **Execute multi-step workflows** with planning and reasoning
- **Use tools and APIs** to interact with external systems
- **Maintain conversation context** across multiple interactions
- **Make decisions** based on available information and defined goals
- **Handle complex tasks** that require multiple capabilities

### Key Characteristics

- **Autonomous**: Can work independently with minimal human intervention
- **Tool-enabled**: Can use custom tools to extend capabilities
- **Context-aware**: Maintains state and memory across interactions
- **Configurable**: Behavior can be customized through configuration
- **Extensible**: New capabilities can be added through custom tools

## Agent Architecture

Our agent framework is built on several key components:

```
Agent Architecture
├── BaseClaudeAgent          # Core agent functionality
├── InteractiveAgent         # Conversation interface
├── Tools System            # Custom tool definitions
├── Configuration          # YAML-based settings
└── Shared Utilities      # Common functions and helpers
```

### Core Components

#### BaseClaudeAgent
The foundation class that provides:
- Claude client initialization
- Tool registration and management
- Configuration loading
- Error handling and logging
- Context management

#### InteractiveAgent
Extends BaseClaudeAgent with:
- Conversation loop management
- User input handling
- Response formatting
- Session state management

#### Tools System
- **Custom Tools**: Define specific capabilities for your agent
- **Tool Registration**: Automatic discovery and registration
- **Parameter Validation**: Type-safe tool parameters
- **Error Handling**: Graceful failure management

## Available Agents

### Azure FSI Landing Zone Agent

An Azure Financial Services Industry Landing Zone deployment agent with two operational modes:

#### Solo Mode (Default)
- **Purpose**: Quick template generation and simple deployments
- **Best for**: Getting started, focused tasks, lower cost operations
- **Usage**: `python agent.py`

#### Squad Mode (`--squad` flag)
- **Purpose**: Expert-level analysis with specialized AI sub-agents
- **Team**: Architect, DevOps, Network, and Security specialists
- **Best for**: Production deployments, compliance reviews, drift detection
- **Usage**: `python agent.py --squad`

**Agent Location**: [`agents/azure-fsi-landingzone/`](../../agents/azure-fsi-landingzone/)
**Documentation**: See [Azure FSI Documentation](../azure-fsi/README.md)
**Comparison**: See the [detailed comparison guide](../azure-fsi/guides/comparison.md) to choose the right mode.

### Azure Compliance Checker
Validates Azure infrastructure against industry compliance standards.

### Example Agent
Demonstrates custom tool creation and agent patterns.

### Agent Template
Bootstrap template for creating new agents quickly.

## Creating Your First Agent

See the [Agent Development Guide](creating-agents.md) for detailed instructions on:

- Setting up a new agent from template
- Configuring agent behavior
- Creating custom tools
- Testing and deployment
- Best practices and guidelines

## Resources

### Documentation
- [Agent Development Guide](creating-agents.md) - Complete guide to building agents
- [Getting Started](../getting-started.md) - Repository setup and quick start
- [Azure FSI Documentation](../azure-fsi/README.md) - Azure Landing Zone agents

### External Resources
- [Claude Agent SDK Documentation](https://github.com/anthropics/claude-agent-sdk-python)
- [Claude API Documentation](https://docs.anthropic.com/)
- [MCP (Model Context Protocol) Specification](https://spec.modelcontextprotocol.io/)

### Example Use Cases
- **Customer Service**: Automated support with escalation
- **Data Analysis**: Process and analyze datasets
- **Infrastructure Deployment**: Automated cloud infrastructure provisioning
- **Compliance Checking**: Validate configurations against standards
- **Research Assistant**: Gather and synthesize information
- **Code Review**: Analyze code quality and suggest improvements

---

*For the most up-to-date information, please check the repository's documentation and the official Claude Agent SDK documentation.*
