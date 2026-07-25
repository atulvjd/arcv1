"""
ArcV1 Prompt Service

Manages prompt templates with variable substitution and versioning.
Provides a centralized repository for all prompts used by agents.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from services.base import BaseService


class PromptTemplate:
    """
    Represents a prompt template with variable substitution support.
    
    Templates use {variable_name} syntax for variable placeholders.
    """
    
    def __init__(
        self,
        name: str,
        template: str,
        description: str = "",
        version: str = "1.0.0",
        default_vars: dict[str, Any] | None = None
    ) -> None:
        """
        Initialize a prompt template.
        
        Args:
            name: Unique template name.
            template: Template string with {variable} placeholders.
            description: Human-readable description of the template.
            version: Semantic version of the template.
            default_vars: Default values for template variables.
        """
        self.name = name
        self.template = template
        self.description = description
        self.version = version
        self.default_vars = default_vars or {}
        self._variables = self._extract_variables()
    
    def _extract_variables(self) -> list[str]:
        """
        Extract variable names from the template.
        
        Returns:
            List of variable names found in the template.
        """
        pattern = r'\{(\w+)\}'
        return list(set(re.findall(pattern, self.template)))
    
    @property
    def variables(self) -> list[str]:
        """Return list of variable names in this template."""
        return self._variables.copy()
    
    def render(self, **kwargs: Any) -> str:
        """
        Render the template with provided variables.
        
        Variables are substituted in order. Default values are used
        if a variable is not provided.
        
        Args:
            **kwargs: Variable values to substitute.
            
        Returns:
            Rendered template string.
            
        Raises:
            ValueError: If a required variable is missing.
        """
        # Merge default vars with provided kwargs
        vars_dict = {**self.default_vars, **kwargs}
        
        # Check for missing required variables
        missing = [v for v in self._variables if v not in vars_dict]
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")
        
        # Perform substitution
        result = self.template
        for key, value in vars_dict.items():
            placeholder = '{' + key + '}'
            result = result.replace(placeholder, str(value))
        
        return result
    
    def validate(self, **kwargs: Any) -> bool:
        """
        Validate that all required variables are provided.
        
        Args:
            **kwargs: Variable values to check.
            
        Returns:
            True if all variables can be satisfied.
        """
        vars_dict = {**self.default_vars, **kwargs}
        return all(v in vars_dict for v in self._variables)
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert template to dictionary representation.
        
        Returns:
            Dictionary with template metadata.
        """
        return {
            "name": self.name,
            "template": self.template,
            "description": self.description,
            "version": self.version,
            "variables": self._variables,
            "default_vars": self.default_vars
        }
    
    def __repr__(self) -> str:
        return f"PromptTemplate(name='{self.name}', version='{self.version}')"


class PromptService(BaseService):
    """
    Service for managing prompt templates.
    
    Provides centralized storage, retrieval, and rendering of prompt templates
    used by agents throughout the system.
    """
    
    def __init__(self, name: str = "PromptService") -> None:
        """
        Initialize the prompt service.
        
        Args:
            name: Service name.
        """
        super().__init__(name)
        self._templates: dict[str, PromptTemplate] = {}
    
    def on_initialize(self) -> None:
        """
        Initialize the prompt service.
        
        Loads any configured templates.
        """
        self.logger.info("Prompt service initialized.")
    
    def on_start(self) -> None:
        """Start the prompt service."""
        self.logger.info(f"Prompt service started with {len(self._templates)} templates.")
    
    def on_stop(self) -> None:
        """Stop the prompt service."""
        self.logger.info("Prompt service stopped.")
    
    def register(self, template: PromptTemplate) -> None:
        """
        Register a prompt template.
        
        Args:
            template: The template to register.
            
        Raises:
            ValueError: If a template with the same name already exists.
        """
        if template.name in self._templates:
            raise ValueError(f"Template '{template.name}' already registered.")
        
        self._templates[template.name] = template
        self.logger.debug(f"Registered template: {template.name}")
    
    def unregister(self, name: str) -> None:
        """
        Unregister a prompt template.
        
        Args:
            name: Name of the template to remove.
            
        Raises:
            KeyError: If template not found.
        """
        if name not in self._templates:
            raise KeyError(f"Template '{name}' not found.")
        
        del self._templates[name]
        self.logger.debug(f"Unregistered template: {name}")
    
    def get(self, name: str) -> PromptTemplate | None:
        """
        Retrieve a template by name.
        
        Args:
            name: Template name.
            
        Returns:
            The template if found, None otherwise.
        """
        return self._templates.get(name)
    
    def render(self, name: str, **kwargs: Any) -> str:
        """
        Retrieve and render a template by name.
        
        Args:
            name: Template name.
            **kwargs: Variables to substitute.
            
        Returns:
            Rendered template string.
            
        Raises:
            KeyError: If template not found.
        """
        template = self.get(name)
        if template is None:
            raise KeyError(f"Template '{name}' not found.")
        
        return template.render(**kwargs)
    
    def list_templates(self) -> list[str]:
        """
        Return list of all registered template names.
        
        Returns:
            Sorted list of template names.
        """
        return sorted(self._templates.keys())
    
    def count(self) -> int:
        """Return number of registered templates."""
        return len(self._templates)
    
    def exists(self, name: str) -> bool:
        """Check if a template is registered."""
        return name in self._templates
    
    def clear(self) -> None:
        """Remove all registered templates."""
        self._templates.clear()
        self.logger.info("All templates cleared.")
    
    def health_check(self) -> dict[str, Any]:
        """Perform health check."""
        base_health = super().health_check()
        base_health["template_count"] = self.count()
        return base_health
