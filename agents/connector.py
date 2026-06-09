"""
Cognitive Matrix - Multi-Agent Connector Layer
Every external LLM is a SOURCE, not an authority.
Every response is audited before entering confirmed context.
No LLM bypasses the 369 axis.

Supported connectors:
  - Ollama (local models — qwen, gemma, tinyllama, phi)
  - Gordon (Docker AI via CLI)
  - Claude API (Anthropic)
  - OpenAI API (GPT)
  - Groq API (fast inference)
  - Any OpenAI-compatible endpoint
"""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 ViChi - https://github.com/ViChi

import json
import time
import subprocess
import urllib.request
import urllib.error
import os
from pathlib import Path

# ─── Base Agent ───────────────────────────────────────────────────────────────

class BaseAgent:
    """
    Every LLM connector inherits from this.
    Enforces: name, query(), health_check()
    Trust starts at = — must be earned through audit results.
    """
    name: str = "base"
    trust_score: float = 0.5  # starts neutral — earned over time
    query_count: int = 0
    confirmed_count: int = 0
    rejected_count: int = 0

    def query(self, prompt: str) -> dict:
        raise NotImplementedError

    def health_check(self) -> bool:
        raise NotImplementedError

    def record_audit_result(self, state: str):
        """Called after the matrix audits this agent's response."""
        self.query_count += 1
        if state == "+":
            self.confirmed_count += 1
        elif state == "-":
            self.rejected_count += 1
        # Trust score = ratio of confirmed to total
        # Weighted — recent behavior matters more
        if self.query_count > 0:
            self.trust_score = round(
                self.confirmed_count / self.query_count, 3
            )

    def status(self) -> dict:
        return {
            "name": self.name,
            "trust_score": self.trust_score,
            "queries": self.query_count,
            "confirmed": self.confirmed_count,
            "rejected": self.rejected_count,
            "healthy": self.health_check()
        }


# ─── Ollama Connector ─────────────────────────────────────────────────────────

class OllamaAgent(BaseAgent):
    """
    Local Ollama model connector.
    Zero cost, zero latency, offline capable.
    Default brain for fast tasks.
    """
    def __init__(self, model: str = "qwen2.5:1.5b",
                 base_url: str = "http://localhost:11434"):
        self.name = f"ollama:{model}"
        self.model = model
        self.base_url = base_url
        self.trust_score = 0.5
        self.query_count = 0
        self.confirmed_count = 0
        self.rejected_count = 0

    def query(self, prompt: str,
              system: str = None,
              temperature: float = 0.3,
              max_tokens: int = 512) -> dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if system:
            payload["system"] = system

        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            start = time.time()
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                elapsed = round(time.time() - start, 2)
                return {
                    "source": self.name,
                    "response": result.get("response", "").strip(),
                    "latency_s": elapsed,
                    "error": None
                }
        except Exception as e:
            return {
                "source": self.name,
                "response": "",
                "latency_s": None,
                "error": str(e)
            }

    def health_check(self) -> bool:
        try:
            urllib.request.urlopen(
                f"{self.base_url}/api/tags", timeout=3
            )
            return True
        except Exception:
            return False

    def list_models(self) -> list:
        try:
            with urllib.request.urlopen(
                f"{self.base_url}/api/tags", timeout=5
            ) as resp:
                data = json.loads(resp.read())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []


# ─── Gordon Connector ─────────────────────────────────────────────────────────

class GordonAgent(BaseAgent):
    """
    Docker Gordon connector via CLI.
    Uses: docker ai "your query"
    Context-aware of local Docker environment.
    Useful for: container debugging, Dockerfile generation,
                infrastructure questions.
    """
    name = "gordon:docker"

    def __init__(self):
        self.trust_score = 0.5
        self.query_count = 0
        self.confirmed_count = 0
        self.rejected_count = 0

    def query(self, prompt: str, **kwargs) -> dict:
        try:
            start = time.time()
            result = subprocess.run(
                ["docker", "ai", prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            elapsed = round(time.time() - start, 2)
            response = result.stdout.strip()
            error = result.stderr.strip() if result.returncode != 0 else None
            return {
                "source": self.name,
                "response": response,
                "latency_s": elapsed,
                "error": error
            }
        except FileNotFoundError:
            return {
                "source": self.name,
                "response": "",
                "latency_s": None,
                "error": "docker CLI not found"
            }
        except subprocess.TimeoutExpired:
            return {
                "source": self.name,
                "response": "",
                "latency_s": None,
                "error": "Gordon timed out"
            }
        except Exception as e:
            return {
                "source": self.name,
                "response": "",
                "latency_s": None,
                "error": str(e)
            }

    def health_check(self) -> bool:
        """
        Docker CLI exists but docker ai is unavailable on this Pi.
        Docker Model Runner exists but has no models loaded.
        Report accurately — trust requires honesty.
        """
        try:
            result = subprocess.run(
                ["docker", "ai", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = (result.stdout + result.stderr).lower()
            if "unknown command" in output:
                return False
            # Docker returns generic help with exit 0 for unknown subcommands on
            # this Pi, so require command-specific help text before reporting OK.
            return result.returncode == 0 and "docker ai" in output
        except Exception:
            return False

    def model_runner_status(self) -> dict:
        """
        Check Docker Model Runner separately.
        Available at 127.0.0.1:12434 but currently has no models.
        """
        try:
            import urllib.request
            with urllib.request.urlopen(
                "http://127.0.0.1:12434/engines/llama.cpp/v1/models",
                timeout=3
            ) as resp:
                data = json.loads(resp.read())
                models = data.get("data", [])
                return {
                    "runner_available": True,
                    "models_loaded": len(models),
                    "models": [m.get("id") for m in models]
                }
        except Exception as e:
            return {
                "runner_available": False,
                "models_loaded": 0,
                "error": str(e)
            }


# ─── Generic OpenAI-Compatible Connector ──────────────────────────────────────

class OpenAICompatibleAgent(BaseAgent):
    """
    Works with any OpenAI-compatible API:
    - OpenAI (GPT-4o, GPT-4o-mini)
    - Groq (llama, mixtral — very fast)
    - Together AI
    - Any local OpenAI-compatible server
    """
    def __init__(self, name: str, model: str,
                 api_key: str, base_url: str,
                 max_tokens: int = 512):
        self.name = name
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.trust_score = 0.5
        self.query_count = 0
        self.confirmed_count = 0
        self.rejected_count = 0

    def query(self, prompt: str,
              system: str = "You are a helpful assistant.",
              temperature: float = 0.3, **kwargs) -> dict:
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": self.max_tokens
        }).encode()

        try:
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
            )
            start = time.time()
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                elapsed = round(time.time() - start, 2)
                response = (
                    data["choices"][0]["message"]["content"].strip()
                )
                return {
                    "source": self.name,
                    "response": response,
                    "latency_s": elapsed,
                    "error": None
                }
        except Exception as e:
            return {
                "source": self.name,
                "response": "",
                "latency_s": None,
                "error": str(e)
            }

    def health_check(self) -> bool:
        return bool(self.api_key)


# ─── Anthropic Claude Connector ───────────────────────────────────────────────

class ClaudeAgent(BaseAgent):
    """
    Anthropic Claude connector.
    Best for: deep reasoning, complex analysis,
              philosophical pressure-testing.
    Requires: ANTHROPIC_API_KEY environment variable
    """
    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        self.name = f"claude:{model}"
        self.model = model
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.trust_score = 0.5
        self.query_count = 0
        self.confirmed_count = 0
        self.rejected_count = 0

    def query(self, prompt: str,
              system: str = "You are a precise reasoning assistant.",
              temperature: float = 0.3,
              max_tokens: int = 512, **kwargs) -> dict:
        if not self.api_key:
            return {
                "source": self.name,
                "response": "",
                "latency_s": None,
                "error": "ANTHROPIC_API_KEY not set"
            }

        payload = json.dumps({
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }).encode()

        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            start = time.time()
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                elapsed = round(time.time() - start, 2)
                response = data["content"][0]["text"].strip()
                return {
                    "source": self.name,
                    "response": response,
                    "latency_s": elapsed,
                    "error": None
                }
        except Exception as e:
            return {
                "source": self.name,
                "response": "",
                "latency_s": None,
                "error": str(e)
            }

    def health_check(self) -> bool:
        return bool(self.api_key)


# ─── Agent Registry ───────────────────────────────────────────────────────────

class AgentRegistry:
    """
    Central registry of all available agents.
    The matrix queries this to find the right tool.
    Trust scores accumulate here over time.
    """
    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        self.agents[agent.name] = agent
        return self

    def get(self, name: str) -> BaseAgent | None:
        return self.agents.get(name)

    def healthy(self) -> list[BaseAgent]:
        return [a for a in self.agents.values() if a.health_check()]

    def by_trust(self) -> list[BaseAgent]:
        """Return agents sorted by trust score, highest first."""
        return sorted(
            self.agents.values(),
            key=lambda a: a.trust_score,
            reverse=True
        )

    def status_all(self) -> list[dict]:
        return [a.status() for a in self.agents.values()]

    def best_available(self) -> BaseAgent | None:
        """
        Return the highest-trust healthy agent.
        Fallback chain: trust score → health → first available
        """
        healthy = self.healthy()
        if not healthy:
            return None
        return max(healthy, key=lambda a: a.trust_score)


# ─── Default Registry Factory ─────────────────────────────────────────────────

def build_default_registry() -> AgentRegistry:
    """
    Build the default agent registry from environment.
    Add agents here as you get API keys.
    Local agents always registered — they cost nothing.
    """
    registry = AgentRegistry()

    # Local Ollama agents — always available if Ollama is running
    registry.register(OllamaAgent("qwen2.5:1.5b"))
    registry.register(OllamaAgent("gemma3:1b"))
    registry.register(OllamaAgent("tinyllama:latest"))

    # Gordon — available if Docker Desktop is running
    registry.register(GordonAgent())

    # Claude — available if API key is set
    if os.environ.get("ANTHROPIC_API_KEY"):
        registry.register(ClaudeAgent("claude-haiku-4-5-20251001"))

    # OpenAI — available if API key is set
    if os.environ.get("OPENAI_API_KEY"):
        registry.register(OpenAICompatibleAgent(
            name="openai:gpt-4o-mini",
            model="gpt-4o-mini",
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            base_url="https://api.openai.com/v1"
        ))

    # Groq — fast inference, available if API key is set
    if os.environ.get("GROQ_API_KEY"):
        registry.register(OpenAICompatibleAgent(
            name="groq:llama3",
            model="llama3-8b-8192",
            api_key=os.environ.get("GROQ_API_KEY", ""),
            base_url="https://api.groq.com/openai/v1"
        ))

    return registry


# ─── Quick test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Agent Registry Test ===\n")
    registry = build_default_registry()

    print("Registered agents:")
    for status in registry.status_all():
        health = "✓" if status["healthy"] else "✗"
        print(f"  [{health}] {status['name']} "
              f"| trust: {status['trust_score']}")

    print("\nQuerying best available local agent...")
    agent = registry.get("ollama:qwen2.5:1.5b")
    if agent and agent.health_check():
        result = agent.query(
            "In one sentence: what is the sky?"
        )
        print(f"\n  Source:  {result['source']}")
        print(f"  Latency: {result['latency_s']}s")
        print(f"  Response: {result['response']}")
    else:
        print("  Ollama not available")
