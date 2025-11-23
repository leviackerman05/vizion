"""
Template-based animation system for Manim.

Templates define the structure and layout of animations,
while LLM-extracted parameters customize the content.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class TemplateMetadata:
    """Metadata describing a template's purpose and parameters."""
    name: str
    description: str
    required_params: list[str]
    optional_params: list[str] = None
    
    def __post_init__(self):
        if self.optional_params is None:
            self.optional_params = []


class AnimationTemplate:
    """
    Base class for animation templates.
    
    Each template:
    1. Defines metadata (what parameters it needs)
    2. Generates Manim code with guaranteed good layout
    3. Accepts parameters from LLM extraction
    """
    
    metadata: TemplateMetadata = None
    
    @classmethod
    def generate_code(cls, params: Dict[str, Any]) -> str:
        """
        Generate Manim code using the template structure
        and provided parameters.
        
        Args:
            params: Dictionary of parameters extracted by LLM
            
        Returns:
            Complete Python/Manim code as string
        """
        raise NotImplementedError("Subclasses must implement generate_code")
    
    @classmethod
    def validate_params(cls, params: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate that required parameters are present.
        
        Returns:
            (is_valid, error_message)
        """
        if not cls.metadata:
            return False, "Template has no metadata defined"
        
        missing = []
        for param in cls.metadata.required_params:
            if param not in params:
                missing.append(param)
        
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"
        
        return True, ""
