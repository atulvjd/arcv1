"""
ArcV1 Filesystem Tool

Provides safe file and directory operations.
All operations are validated for security.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Any

from tools.base import BaseTool, ToolCategory, ToolMetadata, ToolParameter, ToolResult


class FilesystemTool(BaseTool):
    """
    Tool for file system operations.
    
    Supports read, write, list, copy, move, delete and info operations.
    All operations are restricted to allowed paths.
    """
    
    def __init__(self, allowed_paths: list[str] | None = None) -> None:
        """
        Initialize the filesystem tool.
        
        Args:
            allowed_paths: List of allowed base paths. If None, all paths allowed.
        """
        metadata = ToolMetadata(
            name="filesystem",
            description="File system operations: read, write, list, copy, move, delete, info",
            category=ToolCategory.FILESYSTEM,
            parameters=[
                ToolParameter(name="operation", type_name="str",
                            description="Operation: read/write/list/copy/move/delete/info",
                            required=True),
                ToolParameter(name="path", type_name="str",
                            description="Target file or directory path", required=True),
                ToolParameter(name="content", type_name="str",
                            description="Content to write (write operation only)",
                            required=False, default=""),
                ToolParameter(name="destination", type_name="str",
                            description="Destination path (copy/move operations only)",
                            required=False, default=""),
                ToolParameter(name="recursive", type_name="bool",
                            description="List directories recursively",
                            required=False, default=False),
            ],
            return_type="dict or str",
            permissions=["filesystem:read", "filesystem:write", "filesystem:delete"],
            version="1.0.0",
            author="ArcV1"
        )
        super().__init__(metadata)
        self._allowed_paths = [Path(p).resolve() for p in (allowed_paths or [])]
    
    def _validate_path(self, path: str) -> Path:
        """
        Validate and resolve a path.
        
        Args:
            path: Input path string.
            
        Returns:
            Resolved Path object.
            
        Raises:
            ValueError: If path is outside allowed directories.
        """
        resolved = Path(path).resolve()
        
        if self._allowed_paths:
            allowed = False
            for allowed in self._allowed_paths:
                try:
                    resolved.relative_to(allowed)
                    allowed = True
                    break
                except ValueError:
                    continue
            if not allowed:
                raise ValueError(f"Path {path} is not in allowed directories.")
        
        return resolved
    
    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute a filesystem operation.
        
        Args:
            operation: Type of operation (read/write/list/copy/move/delete/info).
            path: Target path.
            content: Content for write operations.
            destination: Destination for copy/move.
            recursive: Whether to list recursively.
            
        Returns:
            ToolResult with operation result.
        """
        start = time.time()
        
        try:
            operation = kwargs.get("operation", "")
            path = str(kwargs.get("path", ""))
            
            operations = {
                "read": self._read,
                "write": self._write,
                "list": self._list,
                "copy": self._copy,
                "move": self._move,
                "delete": self._delete,
                "info": self._info,
            }
            
            handler = operations.get(operation)
            if handler is None:
                return ToolResult.fail(f"Unknown operation: {operation}",
                                     operation=operation)
            
            result = handler(**kwargs)
            duration = (time.time() - start) * 1000
            result.execution_time_ms = duration
            return result
            
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ToolResult.fail(str(e), execution_time_ms=duration)
    
    def _read(self, **kwargs: Any) -> ToolResult:
        path = self._validate_path(kwargs["path"])
        if not path.exists():
            return ToolResult.fail(f"Path not found: {path}")
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            return ToolResult.ok({"path": str(path), "content": content,
                                "size": len(content), "type": "file"})
        return ToolResult.ok({"path": str(path), "type": "directory"})
    
    def _write(self, **kwargs: Any) -> ToolResult:
        path = self._validate_path(kwargs["path"])
        content = kwargs.get("content", "")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult.ok({"path": str(path), "bytes_written": len(content)})
    
    def _list(self, **kwargs: Any) -> ToolResult:
        path = self._validate_path(kwargs["path"])
        if not path.exists():
            return ToolResult.fail(f"Path not found: {path}")
        if not path.is_dir():
            return ToolResult.fail(f"Path is not a directory: {path}")
        
        recursive = kwargs.get("recursive", False)
        pattern = "**/*" if recursive else "*"
        
        items = []
        for item in sorted(path.glob(pattern)):
            items.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0
            })
        return ToolResult.ok({"path": str(path), "items": items,
                            "count": len(items)})
    
    def _copy(self, **kwargs: Any) -> ToolResult:
        src = self._validate_path(kwargs["path"])
        dst = self._validate_path(kwargs["destination"])
        if not src.exists():
            return ToolResult.fail(f"Source not found: {src}")
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        else:
            shutil.copytree(src, dst)
        return ToolResult.ok({"source": str(src), "destination": str(dst)})
    
    def _move(self, **kwargs: Any) -> ToolResult:
        src = self._validate_path(kwargs["path"])
        dst = self._validate_path(kwargs["destination"])
        if not src.exists():
            return ToolResult.fail(f"Source not found: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return ToolResult.ok({"source": str(src), "destination": str(dst)})
    
    def _delete(self, **kwargs: Any) -> ToolResult:
        path = self._validate_path(kwargs["path"])
        if not path.exists():
            return ToolResult.fail(f"Path not found: {path}")
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        return ToolResult.ok({"path": str(path), "deleted": True})
    
    def _info(self, **kwargs: Any) -> ToolResult:
        path = self._validate_path(kwargs["path"])
        if not path.exists():
            return ToolResult.fail(f"Path not found: {path}")
        stat = path.stat()
        return ToolResult.ok({
            "path": str(path),
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "permissions": oct(stat.st_mode)[-3:]
        })