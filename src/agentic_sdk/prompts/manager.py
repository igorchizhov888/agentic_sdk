from typing import Optional, List, Dict, Any
from .storage import PromptStorage


class PromptManager:
    """High-level interface for managing prompts"""
    
    def __init__(self, storage: PromptStorage):
        self.storage = storage
    
    def register_prompt(self, name: str, template: str, 
                       variables: Optional[List[str]] = None,
                       created_by: str = "system",
                       metadata: Optional[Dict[str, Any]] = None) -> int:
        """Create a new prompt version"""
        if variables is None:
            variables = []
        if metadata is None:
            metadata = {}
        
        version = self.storage.get_next_version(name)
        
        self.storage.save_prompt(
            name=name,
            version=version,
            template=template,
            variables=variables,
            created_by=created_by,
            metadata=metadata
        )
        
        # Auto-activate if this is version 1
        if version == 1:
            self.storage.set_active(name, version)
        
        return version
    
    def get_prompt(self, name: str, version: Optional[int] = None) -> str:
        """Get prompt template by name and optional version"""
        prompt_data = self.storage.load_prompt(name, version)
        if prompt_data is None:
            raise ValueError(f"Prompt '{name}' version {version} not found")
        return prompt_data['template']
    
    def activate_version(self, name: str, version: int):
        """Deploy a specific version"""
        # Verify version exists
        prompt_data = self.storage.load_prompt(name, version)
        if prompt_data is None:
            raise ValueError(f"Prompt '{name}' version {version} not found")
        
        self.storage.set_active(name, version)
    
    def rollback(self, name: str):
        """Rollback to previous version"""
        current_version = self.storage.get_active_version(name)
        if current_version is None:
            raise ValueError(f"No active version for prompt '{name}'")
        
        if current_version == 1:
            raise ValueError(f"Cannot rollback version 1")
        
        previous_version = current_version - 1
        self.storage.set_active(name, previous_version)
    
    def list_versions(self, name: str) -> List[Dict[str, Any]]:
        """List all versions of a prompt"""
        return self.storage.get_all_versions(name)
