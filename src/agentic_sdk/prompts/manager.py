from typing import Optional, List, Dict, Any
from .storage import PromptStorage
from .cache import PromptCache


class PromptManager:
    """High-level interface for managing prompts with caching and A/B testing"""
    
    def __init__(self, storage: PromptStorage, cache: Optional[PromptCache] = None,
                 ab_tester = None):
        self.storage = storage
        self.cache = cache or PromptCache()
        self.ab_tester = ab_tester  # Optional ABTester instance
    
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
            cache_key = f"{name}:active"
            self.cache.set(cache_key, template)
        
        return version
    
    def get_prompt(self, name: str, version: Optional[int] = None) -> tuple[str, Optional[int]]:
        """
        Get prompt template by name and optional version (with caching and A/B testing).
        
        Returns:
            (template, version_used) - version_used is set if A/B test is active
        """
        # Check if A/B test is active
        ab_version = None
        if self.ab_tester and version is None:
            ab_version = self.ab_tester.get_version_for_request(name)
            if ab_version:
                version = ab_version
        
        # Build cache key
        if version is None:
            cache_key = f"{name}:active"
        else:
            cache_key = f"{name}:v{version}"
        
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached, ab_version
        
        # Cache miss - query database
        prompt_data = self.storage.load_prompt(name, version)
        if prompt_data is None:
            raise ValueError(f"Prompt '{name}' version {version} not found")
        
        template = prompt_data['template']
        
        # Store in cache
        self.cache.set(cache_key, template)
        
        return template, ab_version
    
    def activate_version(self, name: str, version: int):
        """Deploy a specific version"""
        # Verify version exists
        prompt_data = self.storage.load_prompt(name, version)
        if prompt_data is None:
            raise ValueError(f"Prompt '{name}' version {version} not found")
        
        self.storage.set_active(name, version)
        
        # Update cache
        cache_key = f"{name}:active"
        self.cache.set(cache_key, prompt_data['template'])
    
    def rollback(self, name: str):
        """Rollback to previous version"""
        current_version = self.storage.get_active_version(name)
        if current_version is None:
            raise ValueError(f"No active version for prompt '{name}'")
        
        if current_version == 1:
            raise ValueError(f"Cannot rollback version 1")
        
        previous_version = current_version - 1
        self.storage.set_active(name, previous_version)
        
        # Invalidate cache
        cache_key = f"{name}:active"
        self.cache.invalidate(cache_key)
    
    def list_versions(self, name: str) -> List[Dict[str, Any]]:
        """List all versions of a prompt"""
        return self.storage.get_all_versions(name)
    
    def clear_cache(self):
        """Clear the entire prompt cache"""
        self.cache.clear()
    
    def cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return self.cache.stats()
