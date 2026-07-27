"""
ArcV1 Terminal Tool

Provides safe shell command execution.
Commands are restricted by timeout and permissions.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from typing import Any

from tools.base import BaseTool, ToolCategory, ToolMetadata, ToolParameter, ToolResult


class TerminalTool(BaseTool):
    """
    Tool for executing shell commands.
    
    Supports command execution with timeout, working directory,
    and environment variable control.
    """
    
    def __init__(self, allowed_commands: list[str] | None = None) -> None:
        """
        Initialize the terminal tool.
        
        Args:
            allowed_commands: List of allowed command prefixes. If None, all allowed.
        """
        metadata = ToolMetadata(
            name="terminal",
            description="Execute shell commands with timeout and directory control",
            category=ToolCategory.TERMINAL,
            parameters=[
                ToolParameter(name="command", type_name="str",
                            description="Shell command to execute", required=True),
                ToolParameter(name="timeout", type_name="int",
                            description="Command timeout in seconds",
                            required=False, default=30),
                ToolParameter(name="working_directory", type_name="str",
                            description="Working directory",
                            required=False, default="."),
                ToolParameter(name="env", type_name="dict",
                            description="Additional environment variables",
                            required=False, default={}),
            ],
            return_type="TerminalOutput",
            permissions=["terminal:execute"],
            version="1.0.0",
            author="ArcV1"
        )
        super().__init__(metadata)
        self._allowed_commands = allowed_commands
    
    def _check_command_allowed(self, command: str) -> bool:
        """Check if command is in allowed list."""
        if self._allowed_commands is None:
            return True
        cmd = shlex.split(command)[0] if command else ""
        return any(cmd.startswith(allowed) for allowed in self._allowed_commands)
    
    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute a shell command.
        
        Args:
            command: Shell command string.
            timeout: Timeout in seconds.
            working_directory: Working directory.
            env: Additional environment variables.
            
        Returns:
            ToolResult with stdout, stderr, and return code.
        """
        start = time.time()
        
        try:
            command = kwargs.get("command", "")
            timeout = int(kwargs.get("timeout", 30))
            working_directory = str(kwargs.get("working_directory", "."))
            extra_env = kwargs.get("env", {})
            
            if not command:
                return ToolResult.fail("No command specified.")
            
            if not self._check_command_allowed(command):
                return ToolResult.fail(f"Command not allowed: {command}")
            
            # Prepare environment
            env = os.environ.copy()
            env.update(extra_env)
            
            # Execute
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_directory,
                env=env
            )
            
            duration = (time.time() - start) * 1000
            
            return ToolResult.ok(
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "command": command
                },
                execution_time_ms=duration,
                exit_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            duration = (time.time() - start) * 1000
            return ToolResult.fail(
                f"Command timed out after {timeout}s",
                execution_time_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ToolResult.fail(str(e), execution_time_ms=duration)