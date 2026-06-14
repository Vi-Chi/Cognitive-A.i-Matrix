"""Safe Shell Tool for Orbi Executor.

Salvaged from prior Omni-AI/Wibo system. Provides token and command blocking
for shell executions.
"""
from __future__ import annotations

import shlex
from dataclasses import dataclass

BLOCKED_TOKENS = ["|", ">", "<", ";", "&&", "||", "`", "$(", "\n", "\r"]
BLOCKED_COMMANDS = {"sudo", "rm", "mv", "dd", "mkfs", "reboot", "shutdown", "poweroff", "halt"}
DOCKER_MUTATIONS = {"run", "rm", "rmi", "stop", "start", "restart", "kill", "exec", "compose", "pull", "push", "build", "system", "volume", "network"}
APT_MUTATIONS = {"install", "remove", "purge", "upgrade", "dist-upgrade", "full-upgrade", "autoremove"}
SERVICE_MUTATIONS = {"restart", "start", "stop", "reload", "enable", "disable", "mask", "unmask"}
READONLY_ALLOWLIST = {
    "uname", "hostname", "date", "uptime", "df", "free", "vcgencmd", "systemctl", "ss", "docker", "curl", "ls", "find", "cat", "grep", "journalctl", "apt",
}

@dataclass
class SafetyResult:
    allowed: bool
    command: str
    reason: str

class SafeShellValidator:
    """Validates commands against a strict read-only allowlist and metacharacter blocks.
    
    Execution is handled separately by the Orbi executor.
    """
    def __init__(self, allow_docker_actions: bool = False, allow_apt_actions: bool = False):
        self.allow_docker_actions = allow_docker_actions
        self.allow_apt_actions = allow_apt_actions

    def validate(self, command: str) -> SafetyResult:
        stripped = command.strip()
        if not stripped:
            return SafetyResult(False, command, "empty command")
        
        for token in BLOCKED_TOKENS:
            if token in stripped:
                return SafetyResult(False, command, f"blocked shell token: {token}")
                
        try:
            parts = shlex.split(stripped)
        except ValueError as exc:
            return SafetyResult(False, command, f"parse error: {exc}")
            
        if not parts:
            return SafetyResult(False, command, "empty command")
            
        base = parts[0]
        if base in BLOCKED_COMMANDS:
            return SafetyResult(False, command, f"blocked command: {base}")
            
        if base not in READONLY_ALLOWLIST:
            return SafetyResult(False, command, f"not in read-only allowlist: {base}")
            
        if base in {"chmod", "chown"} and "-R" in parts:
            return SafetyResult(False, command, "recursive permission mutation blocked")
            
        if base == "apt" and len(parts) > 1 and parts[1] in APT_MUTATIONS and not self.allow_apt_actions:
            return SafetyResult(False, command, f"apt mutation blocked: {parts[1]}")
            
        if base == "systemctl" and len(parts) > 1 and parts[1] in SERVICE_MUTATIONS:
            return SafetyResult(False, command, f"service mutation blocked: {parts[1]}")
            
        if base == "docker" and len(parts) > 1 and parts[1] in DOCKER_MUTATIONS and not self.allow_docker_actions:
            return SafetyResult(False, command, f"docker mutation blocked: {parts[1]}")
            
        return SafetyResult(True, command, "allowed read-only command")
