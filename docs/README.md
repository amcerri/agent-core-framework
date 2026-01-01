# Agent Core Framework Documentation

Welcome to the Agent Core Framework documentation. This directory contains public-facing documentation for users of the framework.

## Overview

The Agent Core Framework is a foundational, vendor-agnostic framework for building multi-agent systems. It provides a stable, extensible core with explicit orchestration, governance, and observability capabilities.

### Key Features

- **Core Runtime**: Execution control plane with lifecycle management and routing
- **Agent/Tool/Service Abstractions**: Base classes and contracts for implementing capabilities
- **Orchestration**: Declarative flow engine with YAML support and optional LangGraph integration
- **Governance**: Permissions, policies, budgets, and audit enforcement
- **Observability**: Structured logging, tracing, metrics, and audit events
- **Error Handling**: Structured error classification and retry policies respecting idempotency and budgets
- **Configuration**: YAML-based configuration with validation and environment overrides

## Documentation Index

### Getting Started

- [Overview](./overview.md) - Framework introduction and key concepts
- [Installation](./installation.md) - How to install and set up the framework

### Core Concepts

- [Architecture Overview](./architecture.md) - High-level system architecture and design principles
- [Configuration](./configuration.md) - Configuration system and schema reference

### Guides

- [Creating Agents](./creating-agents.md) - Guide to implementing custom agents
- [Creating Tools](./creating-tools.md) - Guide to implementing custom tools
- [Creating Services](./creating-services.md) - Guide to implementing custom services
- [Orchestration and Flows](./flows.md) - Guide to defining and executing flows

### Reference

- [Runtime API](./runtime-api.md) - Runtime class and execution methods
- [Contracts](./contracts.md) - Core contracts and interfaces

## How to Read This Documentation

### For New Users

1. Start with [Overview](./overview.md) for framework introduction
2. Read [Installation](./installation.md) to get started
3. Review [Architecture](./architecture.md) for system design
4. Explore specific guides as needed

### For Developers

1. [Overview](./overview.md) - Framework introduction
2. [Architecture](./architecture.md) - System design and patterns
3. [Configuration](./configuration.md) - Settings and environment setup
4. [Creating Agents](./creating-agents.md), [Creating Tools](./creating-tools.md), [Creating Services](./creating-services.md) - Implementation guides
5. [Runtime API](./runtime-api.md) - API reference

### For System Architects

1. [Architecture](./architecture.md) - System design patterns
2. [Contracts](./contracts.md) - Interface definitions
3. [Configuration](./configuration.md) - Extensibility and customization
4. [Orchestration and Flows](./flows.md) - Orchestration patterns

## Conventions

- **Code references**: Use repository-relative paths (e.g., `agent_core/runtime/runtime.py`)
- **Configuration**: References to configuration files and schemas
- **Links**: All internal links use relative paths
- **Navigation**: Each page includes back links to docs index and repository root

---

Back to [repository root](../README.md)

