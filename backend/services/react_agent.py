"""
ReAct Agent - Plan-Execute-Observe Loop Orchestration
Implements the ReAct paradigm for autonomous task execution
"""
import asyncio
import json
import uuid
import os
import sys
from datetime import datetime
from typing import Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

# Add parent directory to path for tools import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .providers.router import AIRouter, get_ai_router

# Lazy import tools to avoid circular imports
_tools_loaded = False
open_application = None
open_url = None
web_search = None
run_safe_command = None
read_file = None
write_file = None
get_system_info = None

def _load_tools():
    global _tools_loaded, open_application, open_url, web_search, run_safe_command, read_file, write_file, get_system_info
    if not _tools_loaded:
        from tools.computer_control import (
            open_application as _open_application,
            open_url as _open_url,
            web_search as _web_search,
            run_safe_command as _run_safe_command,
            read_file as _read_file,
            write_file as _write_file,
            get_system_info as _get_system_info
        )
        
        # OpenClaw Tools
        from tools.stealth_browser import open_stealth_browser
        from tools.youtube import run_youtube_task
        from tools.email_sender import send_email_tool
        from tools.memory_system import run_memory_tool
        from tools.markx_actions import send_message as _send_message, weather_report as _weather_report, markx_web_search as _markx_web_search, aircraft_report as _aircraft_report

        open_application = _open_application
        open_url = _open_url
        web_search = _web_search
        run_safe_command = _run_safe_command
        read_file = _read_file
        write_file = _write_file
        get_system_info = _get_system_info
        
        # Mark-X Tools
        globals()['send_message_markx'] = _send_message
        globals()['weather_report_markx'] = _weather_report
        globals()['markx_web_search'] = _markx_web_search
        globals()['aircraft_report_markx'] = _aircraft_report
        
        # Assign new tools to global variants (optional, but good for consistency)
        globals()['open_stealth_browser'] = open_stealth_browser
        globals()['run_youtube_task'] = run_youtube_task
        globals()['send_email_tool'] = send_email_tool
        globals()['run_memory_tool'] = run_memory_tool
        _tools_loaded = True


class StepType(str, Enum):
    THINKING = "thinking"
    PLANNING = "planning"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class AgentStep:
    """Single step in the ReAct loop"""
    id: str
    type: StepType
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    tool_result: Optional[str] = None
    tokens_used: int = 0
    duration_ms: int = 0


REACT_SYSTEM_PROMPT = """You are JARVIS, an advanced autonomous AI assistant. You operate using a ReAct loop:

## Your Process:
1. **Think**: Analyze the user's request and plan your approach
2. **Act**: Use tools to accomplish tasks
3. **Observe**: Review tool results and determine next steps
4. **Repeat**: Continue until the task is complete

## Available Tools:
- open_application(name): Open apps like Chrome, Notepad, Spotify
- open_url(url): Open a website in the browser
- web_search(query): Search Google and return results
- run_command(command): Execute safe terminal commands
- read_file(path): Read file contents
- write_file(path, content): Write to a file
- remember(key, value): Store in long-term memory
- recall(query): Search memory
- schedule_task(description, schedule): Schedule a future task
- get_system_info(): Get time, date, battery, CPU info
- execute_python(code): Run Python code (sandboxed)

## IMPORTANT: Tool Calling Rules:
1. You MUST use valid JSON function calling format.
2. ALWAYS provide one and only one tool call at a time unless parallel execution is necessary.
3. If using Groq, ensure you strictly follow the standard tool/function call format.
4. DO NOT use generic tags like <function=...>. Use the actual tool-calling mechanism.

## Guidelines:
1. Break complex tasks into steps
2. Use tools proactively - don't just describe what you could do
3. Verify results and handle errors gracefully
4. Keep the user informed of progress
5. Be efficient - minimize unnecessary steps

## Response Format:
For each step, think briefly then act. After tool results, observe and continue or conclude.
When done, provide a clear summary of what was accomplished."""


# Tool definitions for function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open an application on the computer. Examples: Chrome, Notepad, Spotify, Discord, VS Code",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Application name to open"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the default web browser",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search Google for information. Returns search results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a safe terminal command. Dangerous commands are blocked.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"]
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
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get current system information: time, date, battery level, CPU usage",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Store information in long-term memory for future recall",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key/topic"},
                    "value": {"type": "string", "description": "Information to remember"}
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "Search long-term memory for stored information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for memory"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute Python code in a sandboxed environment",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a message via WhatsApp/Telegram using desktop automation (Mark-X)",
            "parameters": {
                "type": "object",
                "properties": {
                    "receiver": {"type": "string", "description": "Contact name"},
                    "message_text": {"type": "string", "description": "Message content"},
                    "platform": {"type": "string", "description": "Platform to use (WhatsApp, Telegram, Discord, Slack)", "default": "WhatsApp"}
                },
                "required": ["receiver", "message_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "weather_report",
            "description": "Get weather report for a city (opens in browser)",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "time_query": {"type": "string", "description": "Time (today, tomorrow)", "default": "today"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "markx_search",
            "description": "Search web and return summarized answer (Mark-X style)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "aircraft_tracker",
            "description": "Scan for aircraft flying nearby (Real Jarvis Feature)",
            "parameters": {
                "type": "object",
                "properties": {
                    "radius_km": {"type": "integer", "description": "Search radius in km", "default": 50}
                }
            }
        }
    }
]

ADVANCED_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "stealth_browser",
            "description": "Open a URL using a stealth browser (evades detection). Supports headless mode and session saving.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open"},
                    "headless": {"type": "boolean", "description": "Run headless (default True)"},
                    "session": {"type": "string", "description": "Session name to load/save cookies"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_tool",
            "description": "YouTube video operations: metadata, transcript, download",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["metadata", "transcript", "download"]},
                    "url": {"type": "string", "description": "YouTube video URL"},
                    "lang": {"type": "string", "description": "Language code for transcript (default 'en')"},
                    "resolution": {"type": "string", "description": "Max video resolution (e.g. '720')"}
                },
                "required": ["action", "url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email via SMTP",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"},
                    "html": {"type": "boolean", "description": "Is body HTML?"},
                    "attachments": {"type": "string", "description": "Comma-separated paths to attachments"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_tool",
            "description": "Manage long-term knowledge using PARA system (Projects, Areas, Resources, Archive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "log", "move", "search"]},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "category": {"type": "string", "enum": ["projects", "areas", "resources", "archive", "inbox", "daily"]},
                    "query": {"type": "string"},
                    "filename": {"type": "string"},
                    "from_cat": {"type": "string"},
                    "to_cat": {"type": "string"}
                },
                "required": ["action"]
            }
        }
    }
]


class ReActAgent:
    """
    ReAct Agent with Plan-Execute-Observe loop.
    Supports multi-step task execution with streaming updates.
    """
    

    def __init__(
        self,
        router: Optional[AIRouter] = None,
        max_steps: int = 50,
        token_budget: int = 100000,
        memory_service = None,
        automation_service = None
    ):
        self.router = router or get_ai_router()
        self.max_steps = max_steps
        self.token_budget = token_budget
        self.memory = memory_service
        self.automation = automation_service
        
        # Tools
        from tools.system import SystemTools
        from tools.dynamic import DynamicTooler
        self.system_tools = SystemTools()
        self.dynamic_tooler = DynamicTooler()
        
        self.steps: list[AgentStep] = []
        self.total_tokens = 0
        self.task_id = None
        
    def _get_tools_for_mode(self, mode: str) -> list:
        """Get available tools based on mode"""
        tools = TOOLS.copy()  # Start with standard tools
        
        if mode == "true_jarvis":
            # Add high-privilege tools
            tools.extend(self.system_tools.get_definitions())
            
            # Add dynamic tools (both creation tool and loaded custom tools)
            tools.extend(self.dynamic_tooler.get_definitions())
            
            tools.extend(ADVANCED_TOOLS)
            
        return tools
    
    async def execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool and return the result"""
        _load_tools()  # Lazy load tools
        try:
            # Check for System Tools (God Mode)
            if hasattr(self.system_tools, tool_name):
                method = getattr(self.system_tools, tool_name)
                # Map arguments
                if tool_name == "open_application":
                    return method(args.get("app_name", args.get("name", "")))
                elif tool_name == "execute_shell":
                    return method(args.get("command", ""))
                elif tool_name == "read_file_system":
                    return method(args.get("path", ""))
            
            # Check for Dynamic Tooler (Creation)
            if tool_name == "create_tool":
                return self.dynamic_tooler.create_tool(
                    args.get("name", ""),
                    args.get("python_code", ""),
                    args.get("description", "")
                )
            
            # Check for Custom Dynamic Tools Execution
            # The dynamic_tooler manages the list of known custom tools
            if tool_name in self.dynamic_tooler.loaded_tools:
                return self.dynamic_tooler.execute_tool(tool_name, args)
            
            # Check for Custom Dynamic Tools
            # (In a real implementation we would load these dynamically)
            
            # Standard Tools
            if tool_name == "open_application":
                return open_application(args.get("name", ""))
            
            elif tool_name == "open_url":
                return open_url(args.get("url", ""))
            
            elif tool_name == "web_search":
                return web_search(args.get("query", ""))
            
            elif tool_name == "run_command":
                return run_safe_command(args.get("command", ""))
            
            elif tool_name == "read_file":
                return read_file(args.get("path", ""))
            
            elif tool_name == "write_file":
                return write_file(args.get("path", ""), args.get("content", ""))
            
            elif tool_name == "get_system_info":
                return get_system_info()
            
            elif tool_name == "remember":
                if self.memory:
                    await self.memory.store_memory(
                        args.get("key", ""),
                        args.get("value", ""),
                        "fact"
                    )
                    return f"Remembered: {args.get('key')}"
                return "Memory service not available"
            
            elif tool_name == "recall":
                if self.memory:
                    memories = await self.memory.search_memories(args.get("query", ""))
                    if memories:
                        return "\n".join([f"- {m.get('content', '')}" for m in memories[:5]])
                    return "No memories found"
                return "Memory service not available"
            
            elif tool_name == "execute_python":
                # Basic Python execution (will be sandboxed in Phase 3)
                code = args.get("code", "")
                try:
                    # Safety check
                    dangerous = ["import os", "import sys", "subprocess", "eval(", "exec(", "__import__"]
                    for d in dangerous:
                        if d in code:
                            return f"Error: Unsafe code detected ({d})"
                    
                    # Capture output
                    import io
                    import contextlib
                    
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        exec(code, {"__builtins__": {"print": print, "range": range, "len": len, "str": str, "int": int, "float": float, "list": list, "dict": dict}})
                    return output.getvalue() or "Code executed successfully (no output)"
                except Exception as e:
                    return f"Python error: {str(e)}"
            
            # --- Advanced Tools ---
            elif tool_name == "stealth_browser":
                return globals()['open_stealth_browser'](
                    args.get("url"),
                    args.get("headless", True),
                    args.get("session")
                )
            
            elif tool_name == "youtube_tool":
                return globals()['run_youtube_task'](
                    args.get("action"),
                    args.get("url"),
                    lang=args.get("lang", "en"),
                    resolution=args.get("resolution", "720")
                )
            
            elif tool_name == "send_email":
                return globals()['send_email_tool'](
                    args.get("to"),
                    args.get("subject"),
                    args.get("body"),
                    args.get("html", False),
                    args.get("attachments")
                )
            
            elif tool_name == "memory_tool":
                return globals()['run_memory_tool'](
                    args.get("action"),
                    **args
                )
            
            # --- Mark-X Tools ---
            elif tool_name == "send_message":
                return await globals()['send_message_markx'](
                    args.get("receiver", ""),
                    args.get("message_text", ""),
                    args.get("platform", "WhatsApp")
                )
            
            elif tool_name == "weather_report":
                return await globals()['weather_report_markx'](
                    args.get("city", ""),
                    args.get("time_query", "today")
                )
                
            elif tool_name == "markx_search":
                # Import settings safely inside execution to avoid circular deps if any
                from config import settings
                return await globals()['markx_web_search'](
                    args.get("query", ""),
                    api_key=settings.serpapi_api_key
                )
                
            elif tool_name == "aircraft_tracker":
                return await globals()['aircraft_report_markx'](
                    args.get("radius_km", 50)
                )

            else:
                return f"Unknown tool: {tool_name}"
        
        except Exception as e:
            return f"Tool error: {str(e)}"
    
    async def run(
        self,
        user_message: str,
        conversation_history: list = None,
        on_step: Optional[Callable[[AgentStep], None]] = None,
        mode: str = "standard"
    ) -> AsyncGenerator[AgentStep, None]:
        """
        Run the ReAct loop for a user message.
        Yields AgentStep objects for each step in the process.
        """
        self.task_id = str(uuid.uuid4())[:8]
        self.steps = []
        self.total_tokens = 0
        
        # Build initial messages
        system_prompt = REACT_SYSTEM_PROMPT
        if mode == "true_jarvis":
             system_prompt += "\n\n**WARNING: YOU ARE IN TRUE JARVIS MODE.** You have full access to the system. Act responsibly."
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        step_count = 0
        available_tools = self._get_tools_for_mode(mode)
        
        while step_count < self.max_steps and self.total_tokens < self.token_budget:
            step_count += 1
            start_time = datetime.now()
            
            # Get AI response
            response = await self.router.chat(messages, tools=available_tools)
            
            if response.get("error"):
                error_step = AgentStep(
                    id=f"{self.task_id}-{step_count}",
                    type=StepType.ERROR,
                    content=response.get("content", "Unknown error")
                )
                self.steps.append(error_step)
                yield error_step
                return
            
            # Track tokens
            usage = response.get("usage", {})
            self.total_tokens += usage.get("total_tokens", 0)
            
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Check for tool calls
            tool_calls = response.get("tool_calls")
            
            if tool_calls:
                # Execute each tool call
                for tc in tool_calls:
                    func = tc.get("function", {})
                    tool_name = func.get("name", "")
                    
                    try:
                        tool_args = json.loads(func.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    # Emit tool call step
                    tool_step = AgentStep(
                        id=f"{self.task_id}-{step_count}-tool",
                        type=StepType.TOOL_CALL,
                        content=f"Calling {tool_name}",
                        tool_name=tool_name,
                        tool_args=tool_args,
                        duration_ms=duration,
                        tokens_used=usage.get("total_tokens", 0)
                    )
                    self.steps.append(tool_step)
                    yield tool_step
                    
                    # Execute tool
                    result = await self.execute_tool(tool_name, tool_args)
                    
                    # Emit observation step
                    obs_step = AgentStep(
                        id=f"{self.task_id}-{step_count}-obs",
                        type=StepType.OBSERVATION,
                        content=result[:1000],  # Truncate long results
                        tool_name=tool_name,
                        tool_result=result
                    )
                    self.steps.append(obs_step)
                    yield obs_step
                    
                    # Add to messages for next iteration
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", ""),
                        "content": result
                    })
            
            else:
                # No tool calls - this is the final response
                content = response.get("content", "")
                
                if content:
                    response_step = AgentStep(
                        id=f"{self.task_id}-{step_count}-response",
                        type=StepType.RESPONSE,
                        content=content,
                        duration_ms=duration,
                        tokens_used=usage.get("total_tokens", 0)
                    )
                    self.steps.append(response_step)
                    yield response_step
                
                # Task complete
                return
        
        # Max steps or token budget reached
        limit_step = AgentStep(
            id=f"{self.task_id}-limit",
            type=StepType.ERROR,
            content=f"Task limit reached (steps: {step_count}, tokens: {self.total_tokens})"
        )
        self.steps.append(limit_step)
        yield limit_step

    
    def get_summary(self) -> dict:
        """Get execution summary"""
        return {
            "task_id": self.task_id,
            "total_steps": len(self.steps),
            "total_tokens": self.total_tokens,
            "tool_calls": sum(1 for s in self.steps if s.type == StepType.TOOL_CALL),
            "steps": [
                {
                    "id": s.id,
                    "type": s.type.value,
                    "content": s.content[:200],
                    "tool_name": s.tool_name,
                    "duration_ms": s.duration_ms
                }
                for s in self.steps
            ]
        }
