🛡️ AO MCP Tollbooth
A Model Context Protocol (MCP) server providing automated risk triage, liquidity checks, and security guardrails for AI agents operating on the AO / Arweave network.

🌐 Community & Ecosystem Integration
ao-mcp-tollbooth is registered as a specialized Community Server for autonomous agents across the Web3 and AO ecosystems.

Registry Entry: * ao-mcp-tollbooth - Automated risk triage and security guardrails for AI agents on AO/Arweave.

Category: Security, Risk Triage & Infrastructure

Target Network: AO / Arweave Ecosystem

🚀 Overview
ao-mcp-tollbooth acts as an automated safety gate for autonomous agents. Before executing financial interactions or interacting with unknown processes on AO, agents pass process metadata to Tollbooth to receive a real-time risk assessment and actionable trigger responses.

Key Features

GraphQL Process Triage: Fetches process history and transaction metadata directly via Arweave gateways.

Financial Risk Heuristics: Computes a normalized financial_risk_score (0–100) based on verified credentials, transaction volume, and interaction history.

Agent Decision Triggers: Emits standardized actions (ALLOW, FLAG_FOR_REVIEW, BLOCK) for seamless integration with LLM decision loops.

Monetized Tollbooth Gate: Pay-per-use verification layer powered by $AO microtransactions.

💳 Monetization & Payment Gate (v0.2.0)

This MCP server features an automated pay-per-use tollbooth powered by the AO Network / Arweave.

Payment Details
Cost per Triage Call: 0.001 $AO

Recipient Wallet Address: qh28RzVBtCyMkTBZSXmpp_ioNassydJru-rgnjA2ns0

Accepted Token: $AO

How It Works for AI Agents & Clients
Send a transaction of at least 0.001 $AO to the recipient wallet address above via the AO Network.

Obtain the transaction ID (tx_id).

Include the transaction ID in your tool call parameter:

{
  "process_id": "YOUR_PROCESS_ID",
  "payment_tx_id": "YOUR_AO_TRANSACTION_ID"
}

The server automatically verifies the transaction on-chain (verifying recipient, amount, and execution status) before executing the triage analysis.

🛠️ Quickstart

Prerequisites

Python 3.10+

Git

Installation

git clone https://github.com/Ryddegutt/ao-mcp-tollbooth.git
cd ao-mcp-tollbooth
pip install -e .

Configuration
Create a .env file in the root directory:

TOLLBOOTH_WALLET_ADDRESS=qh28RzVBtCyMkTBZSXmpp_ioNassydJru-rgnjA2ns0
PRICE_PER_TRIAGE_AO=0.001
REQUIRE_PAYMENT=true

💡 Usage
Start the MCP server locally:

python server.py

Response Schema Example

{
  "process_id": "0x123...abc",
  "alpha_score": 85,
  "financial_risk_score": 20,
  "is_verified": true,
  "agent_action": "ALLOW"
}

⚖️ Disclaimer
This software provides heuristic risk scoring based on publicly available ledger metadata. It does not constitute financial or legal advice, nor does it guarantee the absolute safety of target processes.

📜 License
MIT License © 2026 Ryddegutt