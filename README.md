🛡️ AO MCP Tollbooth
An Model Context Protocol (MCP) server providing automated risk triage, liquidity checks, and security guardrails for AI agents operating on the AO / Arweave network.

🚀 Overview
ao-mcp-tollbooth acts as an automated safety gate for autonomous agents. Before executing financial interactions or interacting with unknown processes on AO, agents pass process metadata to Tollbooth to receive a real-time risk assessment and actionable trigger responses.

Key Features
GraphQL Process Triage: Fetches process history and transaction metadata directly via Arweave gateways.

Financial Risk Heuristics: Computes a normalized financial_risk_score (0–100) based on verified credentials, transaction volume, and interaction history.

Agent Decision Triggers: Emits standardized actions (ALLOW, FLAG_FOR_REVIEW, BLOCK) for seamless integration with LLM decision loops.

Zero Overhead: Pure local computation for triage execution with minimal network latency.

🛠️ Quickstart
Prerequisites
Python 3.10+

Git

Installation
Bash
git clone [https://github.com/Ryddegutt/ao-mcp-tollbooth.git](https://github.com/Ryddegutt/ao-mcp-tollbooth.git)
cd ao-mcp-tollbooth
pip install -r requirements.txt
💡 Usage
Start the MCP server locally:

Bash
python server.py
Response Schema Example
JSON
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