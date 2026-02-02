"""
Tasks Router
HTTP endpoints for task automation and scheduling
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from services.automation import AutomationService
from services.ai_engine import AIEngine


router = APIRouter()
automation_service = AutomationService()
ai_engine = AIEngine()


class TaskCreate(BaseModel):
    """Create a new scheduled task"""
    description: str
    schedule: str  # Natural language: "in 5 minutes", "every day at 9am"
    action_type: str = "speak"  # "speak", "command", "reminder"
    action_data: Optional[str] = None


class TaskResponse(BaseModel):
    """Task creation response"""
    task_id: str
    description: str
    schedule: str
    next_run: Optional[str] = None
    status: str


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    """Create a new scheduled task"""
    task_id = str(uuid.uuid4())[:8]
    
    # Define the action based on type
    async def task_action():
        if task.action_type == "speak":
            # AI will respond to the task description
            from services.tts import TTSService
            tts = TTSService()
            response = await ai_engine.chat(f"Execute scheduled task: {task.description}")
            audio = await tts.synthesize(response["text"])
            print(f"[TASK] {task.description}: {response['text']}")
        elif task.action_type == "command":
            from tools.computer_control import ComputerControl
            controller = ComputerControl()
            result = await controller.run_command(task.action_data or task.description)
            print(f"[TASK] Command result: {result}")
        elif task.action_type == "reminder":
            print(f"[REMINDER] {task.description}")
    
    result = await automation_service.schedule_task(
        task_id=task_id,
        description=task.description,
        schedule=task.schedule,
        action=task_action
    )
    
    return TaskResponse(
        task_id=result["task_id"],
        description=result["description"],
        schedule=task.schedule,
        next_run=result.get("next_run"),
        status=result["status"]
    )


@router.get("/")
async def list_tasks():
    """List all scheduled tasks"""
    tasks = automation_service.list_tasks()
    return {"tasks": tasks, "count": len(tasks)}


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a scheduled task"""
    success = automation_service.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted", "task_id": task_id}


@router.post("/{task_id}/pause")
async def pause_task(task_id: str):
    """Pause a scheduled task"""
    success = automation_service.pause_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "paused", "task_id": task_id}


@router.post("/{task_id}/resume")
async def resume_task(task_id: str):
    """Resume a paused task"""
    success = automation_service.resume_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "resumed", "task_id": task_id}


@router.get("/memory")
async def get_memories(category: str = "all", query: str = ""):
    """Search and retrieve memories"""
    from services.memory import MemoryService
    memory = MemoryService()
    
    if query:
        memories = await memory.search_memory(query=query, category=category)
    else:
        # Get all recent memories
        memories = await memory.search_memory(query="", category=category)
    
    return {"memories": memories, "count": len(memories)}


@router.post("/memory")
async def create_memory(category: str, content: str, importance: int = 5):
    """Manually store a memory"""
    from services.memory import MemoryService
    memory = MemoryService()
    
    await memory.store_memory(
        category=category,
        content=content,
        importance=importance
    )
    
    return {
        "status": "stored",
        "category": category,
        "content": content,
        "importance": importance
    }
