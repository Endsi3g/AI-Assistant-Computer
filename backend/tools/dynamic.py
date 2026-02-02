import os
import importlib.util
import sys
from typing import List, Dict

class DynamicTooler:
    """
    Enables the agent to create and load its own tools at runtime.
    Tools are saved to backend/tools/custom/
    
    Convention:
    - Tool file must define a 'execute(**kwargs)' function.
    - Tool file must define a 'TOOL_DEFINITION' dictionary describing the tool.
    """
    
    def __init__(self, tools_dir: str = "backend/tools/custom"):
        # Fix path mapping
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.tools_dir = os.path.join(base_dir, "tools", "custom")
        
        os.makedirs(self.tools_dir, exist_ok=True)
        # Ensure __init__.py exists
        if not os.path.exists(os.path.join(self.tools_dir, "__init__.py")):
            open(os.path.join(self.tools_dir, "__init__.py"), 'w').close()
            
        self.loaded_tools = {} # name -> module
        self.convert_legacy_tools()
        self.refresh_tools()

    def convert_legacy_tools(self):
        """Convert any existing tools that might not match the new format (optional safety)"""
        pass

    def refresh_tools(self):
        """Scan directory and reload all tools"""
        self.loaded_tools = {}
        if not os.path.exists(self.tools_dir):
            return

        for filename in os.listdir(self.tools_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                try:
                    filepath = os.path.join(self.tools_dir, filename)
                    spec = importlib.util.spec_from_file_location(module_name, filepath)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        
                        if hasattr(module, 'TOOL_DEFINITION') and hasattr(module, 'execute'):
                            self.loaded_tools[module_name] = module
                except Exception as e:
                    print(f"Failed to load custom tool {filename}: {e}")

    def create_tool(self, name: str, python_code: str, description: str) -> str:
        """
        Create a new Python tool.
        Args:
            name: Name of the tool function (snake_case)
            python_code: Complete Python code. MUST define `TOOL_DEFINITION` and `execute(**kwargs)`.
            description: Tool description for the AI.
        """
        # Sanitize name
        name = "".join(x for x in name if x.isalnum() or x == "_")
        filename = f"{name}.py"
        filepath = os.path.join(self.tools_dir, filename)
        
        # Validation: check if code likely contains required exports
        if "TOOL_DEFINITION" not in python_code or "def execute" not in python_code:
            # Attempt to wrap simple code if it looks like a raw function
            pass 

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            # Verify load
            self.refresh_tools()
            
            if name in self.loaded_tools:
                return f"Tool '{name}' created and loaded successfully. usage: You can now use this tool in future steps."
            else:
                return f"Tool created at {filepath} but failed to load. Ensure it defines 'TOOL_DEFINITION' and 'execute'."
                
        except Exception as e:
            return f"Failed to create tool: {str(e)}"

    def execute_tool(self, tool_name: str, args: dict):
        """Execute a loaded custom tool"""
        if tool_name in self.loaded_tools:
            try:
                return self.loaded_tools[tool_name].execute(**args)
            except Exception as e:
                return f"Error executing custom tool {tool_name}: {str(e)}"
        return f"Custom tool {tool_name} not found."

    def get_definitions(self) -> List[Dict]:
        """Get definitions for the tool creation tool AND all loaded custom tools"""
        definitions = [
            {
                "type": "function",
                "function": {
                    "name": "create_tool",
                    "description": "Create a new permanent tool. Code MUST export 'TOOL_DEFINITION' (dict) and 'execute(**kwargs)' function.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the tool (snake_case)"
                            },
                            "python_code": {
                                "type": "string",
                                "description": "Python code. Must define TOOL_DEFINITION = {...} and def execute(**kwargs): ..."
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of what the tool does"
                            }
                        },
                        "required": ["name", "python_code", "description"]
                    }
                }
            }
        ]
        
        # Add loaded custom tools
        for name, module in self.loaded_tools.items():
            if hasattr(module, 'TOOL_DEFINITION'):
                definitions.append(module.TOOL_DEFINITION)
                
        return definitions
