# Healthcare Agents on AgentCore - Documentation

Production-ready healthcare AI agents solution using AWS Bedrock AgentCore.

## Quick Links

- **🚀 Getting Started:** [DEPLOYMENT.md](DEPLOYMENT.md) - Deploy your first agent
- **⚙️ Configuration:** [AGENT_CONFIGURATION.md](AGENT_CONFIGURATION.md) - Configure agents
- **🏗️ Architecture:** [architecture/GATEWAY.md](architecture/GATEWAY.md) - System architecture

## Documentation Structure

### 📋 Core Guides

**Getting Started:**
- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide (CDK, frontend, backend)
- [AGENT_CONFIGURATION.md](AGENT_CONFIGURATION.md) - Agent configuration and patterns

**Healthcare Patterns:**
- [CLAIMS_AGENTS_SUMMARY.md](CLAIMS_AGENTS_SUMMARY.md) - Claims assembly & submission agents
- [CLAIMS_AGENTS_DEPLOYMENT.md](CLAIMS_AGENTS_DEPLOYMENT.md) - Claims agents deployment

### 🏗️ Architecture

**Core Components:**
- [GATEWAY.md](architecture/GATEWAY.md) - AgentCore Gateway, Lambda targets, MCP protocol
- [MEMORY_INTEGRATION.md](architecture/MEMORY_INTEGRATION.md) - AgentCore Memory integration
- [STREAMING.md](architecture/STREAMING.md) - Streaming responses and real-time updates

### 🔧 Tools

**Available Tools:**
- [overview.md](tools/overview.md) - All available gateway tools
- [healthlake-tools.md](tools/healthlake-tools.md) - AWS HealthLake FHIR tools (7 tools)
- [sample-tool.md](tools/sample-tool.md) - Example tool implementation

### ⚙️ Operations

**Development:**
- [TOOL_AC_CODE_INTERPRETER.md](operations/TOOL_AC_CODE_INTERPRETER.md) - Code interpreter tool usage

## What's Deployed

### Gateway Targets (3)

1. **sample-tool-target** - Text analysis example
2. **payor-policy-tools** - Prior authorization requirement rules
3. **healthlake-tools** - 7 FHIR EHR tools (conditions, medications, observations, allergies, appointments, search, everything)

### Runtime

- **healthcare_agents_stack_StrandsAgent** - Strands-based agent runtime with memory integration

## Stack Configuration

Current setup (`infra-cdk/config.yaml`):

```yaml
stack_name_base: healthcare-agents-stack

backend:
  pattern: medical-coding-agent
  deployment_type: docker

  healthlake:
    read_only_mode: true
    region: us-east-1
    datastore_id: '3aec3833b094687baabc7def9b85976b'
```

## Key Features

- ✅ Lambda-based Gateway targets with independent scaling
- ✅ OAuth2 authentication via Cognito
- ✅ External MCP client support (Claude Desktop, Cursor)
- ✅ AgentCore Memory integration
- ✅ Streaming support
- ✅ Read-only HealthLake mode for production safety
- ✅ Multi-agent orchestration (Strands)

## Getting Help

- Check specific documentation sections above
- Review [GATEWAY.md](architecture/GATEWAY.md) troubleshooting section
- Check CloudWatch logs for Lambda and Gateway operations
