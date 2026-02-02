
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy import Flag
CREWAI_AVAILABLE = False

try:
    from crewai import Agent, Task, Crew, Process
    # We might need custom tools here later
    CREWAI_AVAILABLE = True
except ImportError:
    logger.warning("CrewAI not currently installed. Proactive agents disabled.")

class ProactiveCore:
    """
    Manages the multi-agent swarm for proactive behavior.
    Uses CrewAI to orchestrate Researcher, Planner, and Executor agents.
    """
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider
        self.crew = None
        
        if CREWAI_AVAILABLE:
            self._init_agents()
        else:
            logger.info("CrewAI agents not initialized (dependency missing).")

    def _init_agents(self):
        """Initialize the default swarm agents."""
        if not CREWAI_AVAILABLE:
            return

        # 1. Researcher: Finds information
        self.researcher = Agent(
            role='Senior Technical Researcher',
            goal='Uncover groundbreaking technologies and specific implementation details',
            backstory="""You are an expert researcher with a keen eye for detail. 
            You can traverse the web and documentation to find the exact code snippets 
            and architectural patterns needed.""",
            verbose=True,
            allow_delegation=False,
            # llm=self.ai_provider # We will wire this up to our unified router later
        )

        # 2. Planner: Strategies
        self.planner = Agent(
            role='Strategic Planner',
            goal='Break down complex objectives into actionable steps',
            backstory="""You are a veteran project manager. You see the big picture 
            and can slice a 2-week feature into 4-hour tasks.""",
            verbose=True,
            allow_delegation=True
        )

    def run_swarm(self, objective: str) -> str:
        """Kickoff a crew to solve a complex objective."""
        if not CREWAI_AVAILABLE:
            return "Proactive Core is currently offline (installing dependencies)."
            
        try:
            # Dynamic Task Creation
            task1 = Task(
                description=f"Research the following objective thoroughly: {objective}",
                agent=self.researcher,
                expected_output="A detailed technical summary"
            )
            
            task2 = Task(
                description=f"Create a step-by-step execution plan for: {objective}",
                agent=self.planner,
                expected_output="A list of actionable steps with estimated times",
                context=[task1]
            )
            
            # Instantiate Crew
            self.crew = Crew(
                agents=[self.researcher, self.planner],
                tasks=[task1, task2],
                verbose=2, 
                process=Process.sequential
            )
            
            result = self.crew.kickoff()
            return str(result)
            
        except Exception as e:
            logger.error(f"Swarm failed: {e}")
            return f"Swarm execution failed: {str(e)}"
