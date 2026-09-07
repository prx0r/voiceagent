#!/usr/bin/env bash
set -euo pipefail
mkdir -p upstreams && cd upstreams
repos=(
  "https://github.com/livekit/agents.git"
  "https://github.com/livekit-examples/python-agents-examples.git"
  "https://github.com/livekit/sip.git"
  "https://github.com/pipecat-ai/pipecat.git"
  "https://github.com/bolna-ai/bolna.git"
  "https://github.com/TEN-framework/ten-framework.git"
  "https://github.com/codewithmuh/hearthline.git"
  "https://github.com/Shopify/shop-chat-agent.git"
  "https://github.com/Shopify/ucp-cli.git"
  "https://github.com/Universal-Commerce-Protocol/ucp.git"
  "https://github.com/agentic-commerce-protocol/agentic-commerce-protocol.git"
  "https://github.com/daydreamsai/lucid-agents.git"
  "https://github.com/paypal/agent-toolkit.git"
  "https://github.com/stripe/ai.git"
  "https://github.com/openreferral/specification.git"
  "https://github.com/TimefoldAI/timefold-quickstarts.git"
  "https://github.com/TimefoldAI/timefold-solver.git"
  "https://github.com/langchain-ai/langgraph.git"
  "https://github.com/mem0ai/mem0.git"
  "https://github.com/neo4j/neo4j-graphrag-python.git"
  "https://github.com/temporalio/samples-python.git"
  "https://github.com/openai/openai-agents-python.git"
  "https://github.com/google/adk-python.git"
  "https://github.com/NVIDIA-AI-Blueprints/Retail-Agentic-Commerce.git"
  "https://github.com/anthropics/commerce-agents.git"
  "https://github.com/Accio-org/BusinessArena.git"
  "https://github.com/Accio-org/CommerceAgentBench.git"
  "https://github.com/arenza-ai/agentic-commerce-score.git"
)
for repo in "${repos[@]}"; do
  name="$(basename "$repo" .git)"
  [[ -d "$name/.git" ]] || git clone --depth 1 "$repo" "$name"
done
