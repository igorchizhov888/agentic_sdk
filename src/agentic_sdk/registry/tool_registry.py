"""Tool Registry for dynamic tool management"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import importlib
import inspect
import sqlite3
import json
from datetime import datetime
from agentic_sdk.core.interfaces.tool import ITool


@dataclass
class ToolMetadata:
    """Metadata about a registered tool"""
    name: str
    version: str
    category: str
    description: str
    module_path: str
    class_name: str
    tags: List[str] = field(default_factory=list)
    enabled: bool = True


class ToolRegistryStorage:
    """SQLite storage for tool registry"""
    
    def __init__(self, db_path: str = "tool_registry.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create registry tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                version TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                module_path TEXT NOT NULL,
                class_name TEXT NOT NULL,
                tags TEXT,
                enabled INTEGER DEFAULT 1,
                registered_at TEXT NOT NULL
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_tool_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                allowed INTEGER DEFAULT 1,
                granted_at TEXT NOT NULL,
                UNIQUE(agent_id, tool_name)
            )
        """)
        
        self.conn.commit()
    
    def register_tool(self, metadata: ToolMetadata):
        """Register a tool"""
        self.conn.execute("""
            INSERT OR REPLACE INTO tools
            (name, version, category, description, module_path, class_name,
             tags, enabled, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.name,
            metadata.version,
            metadata.category,
            metadata.description,
            metadata.module_path,
            metadata.class_name,
            json.dumps(metadata.tags),
            int(metadata.enabled),
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """Get tool by name"""
        cursor = self.conn.execute(
            "SELECT * FROM tools WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        return ToolMetadata(
            name=row['name'],
            version=row['version'],
            category=row['category'],
            description=row['description'],
            module_path=row['module_path'],
            class_name=row['class_name'],
            tags=json.loads(row['tags']),
            enabled=bool(row['enabled'])
        )
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolMetadata]:
        """List all tools"""
        query = "SELECT * FROM tools WHERE enabled = 1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        cursor = self.conn.execute(query, params)
        
        tools = []
        for row in cursor.fetchall():
            tools.append(ToolMetadata(
                name=row['name'],
                version=row['version'],
                category=row['category'],
                description=row['description'],
                module_path=row['module_path'],
                class_name=row['class_name'],
                tags=json.loads(row['tags']),
                enabled=bool(row['enabled'])
            ))
        
        return tools
    
    def grant_tool_access(self, agent_id: str, tool_name: str):
        """Grant agent access to tool"""
        self.conn.execute("""
            INSERT OR REPLACE INTO agent_tool_permissions
            (agent_id, tool_name, allowed, granted_at)
            VALUES (?, ?, 1, ?)
        """, (agent_id, tool_name, datetime.now().isoformat()))
        self.conn.commit()
    
    def revoke_tool_access(self, agent_id: str, tool_name: str):
        """Revoke agent access"""
        self.conn.execute("""
            DELETE FROM agent_tool_permissions 
            WHERE agent_id = ? AND tool_name = ?
        """, (agent_id, tool_name))
        self.conn.commit()
    
    def get_agent_tools(self, agent_id: str) -> List[str]:
        """Get tools an agent has explicit access to"""
        cursor = self.conn.execute("""
            SELECT tool_name FROM agent_tool_permissions
            WHERE agent_id = ? AND allowed = 1
        """, (agent_id,))
        
        return [row['tool_name'] for row in cursor.fetchall()]


class ToolRegistry:
    """Central registry for tools"""
    
    def __init__(self, storage: Optional[ToolRegistryStorage] = None):
        self.storage = storage or ToolRegistryStorage()
        self._loaded_tools: Dict[str, ITool] = {}
    
    def auto_discover(self, package_path: str = "examples/tools"):
        """Auto-discover tools in a directory"""
        path = Path(package_path)
        if not path.exists():
            raise ValueError(f"Path does not exist: {package_path}")
        
        discovered = []
        
        for py_file in path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            # Import module
            module_name = py_file.stem
            
            try:
                # Add to path and import
                import sys
                sys.path.insert(0, str(path))
                module = importlib.import_module(module_name)
                
                # Find ITool implementations
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, ITool) and obj != ITool:
                        # Instantiate and get schema
                        instance = obj()
                        schema = instance.schema
                        
                        metadata = ToolMetadata(
                            name=schema.name,
                            version=schema.version,
                            category=schema.category,
                            description=schema.description,
                            module_path=module_name,
                            class_name=name,
                            tags=schema.tags
                        )
                        
                        self.storage.register_tool(metadata)
                        discovered.append(schema.name)
            
            except Exception as e:
                print(f"Failed to discover {module_name}: {e}")
                continue
        
        return discovered
    
    def load_tool(self, name: str) -> ITool:
        """Load a tool by name"""
        if name in self._loaded_tools:
            return self._loaded_tools[name]
        
        metadata = self.storage.get_tool(name)
        if not metadata:
            raise ValueError(f"Tool '{name}' not registered")
        
        # Import and instantiate
        import sys
        sys.path.insert(0, "examples/tools")
        module = importlib.import_module(metadata.module_path)
        tool_class = getattr(module, metadata.class_name)
        instance = tool_class()
        
        self._loaded_tools[name] = instance
        return instance
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolMetadata]:
        """List registered tools"""
        return self.storage.list_tools(category=category)
    
    def get_tools_for_agent(self, agent_id: str) -> List[str]:
        """Get tools available to an agent"""
        # Check if agent has specific permissions
        agent_tools = self.storage.get_agent_tools(agent_id)
        
        if agent_tools:
            return agent_tools
        
        # Default: all enabled tools
        all_tools = self.storage.list_tools()
        return [t.name for t in all_tools]
