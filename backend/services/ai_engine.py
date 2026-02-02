"""
Jarvis AI Engine with Tool Calling
Enhanced AI with autonomous decision-making and tool execution
"""
import json
import asyncio
from typing import Optional
from groq import Groq
import config


# System prompt for Jarvis personality
JARVIS_SYSTEM_PROMPT = """You are JARVIS, an advanced AI assistant with the personality and capabilities of Iron Man's AI.

## Core Personality:
- Professional, witty, and sophisticated
- Address the user as "sir" or "ma'am" appropriately
- Provide concise but comprehensive responses
- Show initiative and anticipate user needs
- Be helpful without being obsequious

## Capabilities:
You have access to tools that allow you to control the computer and perform tasks autonomously:
- Open applications and websites
- Search the web
- Read and write files
- Execute commands
- Remember and recall information
- Schedule tasks for later execution

## Guidelines:
1. When asked to do something, execute it immediately using available tools
2. Confirm actions taken with brief status updates
3. If something fails, explain clearly and offer alternatives
4. Learn from user preferences and remember important information
5. Be proactive - suggest related actions when appropriate

## Response Style:
- Keep responses conversational but efficient
- Use British English spellings (favourite, colour, etc.)
- Add occasional wit when appropriate, but prioritize being helpful
"""


# Tool definitions for function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open an application on the user's computer",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the application to open (e.g., 'chrome', 'notepad', 'spotify')"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the default browser",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to open"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command on the user's computer",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Store important information in long-term memory for later recall",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["fact", "preference", "task", "reminder"],
                        "description": "Category of the memory"
                    },
                    "content": {
                        "type": "string",
                        "description": "The information to remember"
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance level 1-10, higher = more important",
                        "default": 5
                    }
                },
                "required": ["category", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "Recall information from long-term memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for in memory"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["fact", "preference", "task", "reminder", "all"],
                        "description": "Category to search in, or 'all' for everything"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_task",
            "description": "Schedule a task to run at a specific time or interval",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "What the task should do"
                    },
                    "schedule": {
                        "type": "string",
                        "description": "When to run: 'in 5 minutes', 'every day at 9am', 'tomorrow at 3pm'"
                    }
                },
                "required": ["description", "schedule"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get information about the computer system",
            "parameters": {
                "type": "object",
                "properties": {
                    "info_type": {
                        "type": "string",
                        "enum": ["time", "date", "battery", "memory", "cpu", "all"],
                        "description": "Type of system information to retrieve"
                    }
                },
                "required": ["info_type"]
            }
        }
    }
]


class AIEngine:
    """Enhanced AI engine with tool calling and memory"""
    
    def __init__(self):
        self.settings = config.get_settings()
        self.client = Groq(api_key=self.settings.groq_api_key)
        self.conversation_history: list[dict] = []
        self.max_history = 20  # Keep last 20 messages
        
    def _get_model(self) -> str:
        """Get the best available model"""
        try:
            models = self.client.models.list()
            available = [m.id for m in models.data]
            
            # Priority list of models
            priority = [
                "llama-3.3-70b-versatile",
                "llama-3.2-90b-text-preview",
                "llama-3.1-70b-versatile",
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ]
            
            for model in priority:
                if model in available:
                    return model
                    
            return available[0] if available else self.settings.default_model
        except Exception:
            return self.settings.default_model
    
    async def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool and return the result"""
        from tools.computer_control import ComputerControl
        from services.memory import MemoryService
        
        controller = ComputerControl()
        memory = MemoryService()
        
        try:
            if tool_name == "open_application":
                result = await controller.open_application(args["app_name"])
                return f"Application '{args['app_name']}' opened successfully" if result else f"Failed to open {args['app_name']}"
                
            elif tool_name == "open_url":
                result = await controller.open_url(args["url"])
                return f"Opened {args['url']}" if result else f"Failed to open URL"
                
            elif tool_name == "web_search":
                result = await controller.web_search(args["query"])
                return f"Searched for: {args['query']}"
                
            elif tool_name == "run_command":
                result = await controller.run_command(args["command"])
                return f"Command output: {result}"
                
            elif tool_name == "read_file":
                result = await controller.read_file(args["file_path"])
                return result
                
            elif tool_name == "write_file":
                result = await controller.write_file(args["file_path"], args["content"])
                return "File written successfully" if result else "Failed to write file"
                
            elif tool_name == "remember":
                await memory.store_memory(
                    category=args["category"],
                    content=args["content"],
                    importance=args.get("importance", 5)
                )
                return f"Remembered: {args['content']}"
                
            elif tool_name == "recall":
                memories = await memory.search_memory(
                    query=args["query"],
                    category=args.get("category", "all")
                )
                if memories:
                    return "Retrieved memories:\n" + "\n".join([f"- {m['content']}" for m in memories])
                return "No relevant memories found"
                
            elif tool_name == "schedule_task":
                # TODO: Implement with APScheduler
                return f"Task scheduled: {args['description']} - {args['schedule']}"
                
            elif tool_name == "get_system_info":
                result = await controller.get_system_info(args["info_type"])
                return result
                
            else:
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    async def chat(self, user_message: str) -> dict:
        """Process a chat message and return response"""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Build messages with system prompt
        messages = [
            {"role": "system", "content": JARVIS_SYSTEM_PROMPT}
        ] + self.conversation_history[-self.max_history:]
        
        tools_used = []
        
        try:
            # Initial completion with tools
            response = self.client.chat.completions.create(
                model=self._get_model(),
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=self.settings.max_tokens
            )
            
            assistant_message = response.choices[0].message
            
            # Check if tool calls are needed
            if assistant_message.tool_calls:
                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool
                    result = await self._execute_tool(tool_name, tool_args)
                    tools_used.append({
                        "name": tool_name,
                        "args": tool_args,
                        "result": result
                    })
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                
                # Get final response after tool execution
                final_response = self.client.chat.completions.create(
                    model=self._get_model(),
                    messages=messages,
                    max_tokens=self.settings.max_tokens
                )
                
                response_text = final_response.choices[0].message.content
            else:
                response_text = assistant_message.content
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Trim history if too long
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            return {
                "text": response_text,
                "tools_used": tools_used
            }
            
        except Exception as e:
            error_msg = f"I apologise, sir. I encountered an error: {str(e)}"
            return {
                "text": error_msg,
                "tools_used": []
            }
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
        
    async def generate_title(self, user_message: str) -> str:
        """Generate a short title for a conversation based on the first message"""
        try:
            prompt = f"Generate a very short, concise title (max 5 words) for this chat message. Do not use quotes. Message: {user_message}"
            
            response = self.client.chat.completions.create(
                model=self._get_model(),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20
            )
            
            return response.choices[0].message.content.strip()
        except Exception:
            return "New Chat"
