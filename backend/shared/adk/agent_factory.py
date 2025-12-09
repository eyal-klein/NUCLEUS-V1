"""
NUCLEUS V1.2 - ADK Agent Factory
Creates and manages Google ADK-based agents
"""

import logging
from typing import List, Dict, Any, Optional
import os

# Google ADK imports
try:
    from google import genai
    from google.genai import types
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    logging.warning("Google ADK not available. Install with: pip install google-genai")

from langchain.tools import BaseTool

logger = logging.getLogger(__name__)


class ADKAgentFactory:
    """
    Factory for creating Google ADK agents with LangChain tools.
    
    Combines the power of Google ADK with the flexibility of LangChain tools.
    """
    
    def __init__(self):
        if not ADK_AVAILABLE:
            raise ImportError("Google ADK is not installed")
        
        # Initialize ADK client
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable required")
        
        self.client = genai.Client(api_key=api_key)
        logger.info("ADK Agent Factory initialized")
    
    def create_agent(
        self,
        agent_name: str,
        system_prompt: str,
        tools: Optional[List[BaseTool]] = None,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7
    ) -> "ADKAgent":
        """
        Create a new ADK agent.
        
        Args:
            agent_name: Name of the agent
            system_prompt: System instructions for the agent
            tools: List of LangChain tools (optional)
            model: Gemini model to use
            temperature: Sampling temperature
            
        Returns:
            ADKAgent instance
        """
        logger.info(f"Creating ADK agent: {agent_name}")
        
        # Convert LangChain tools to ADK format
        adk_tools = []
        if tools:
            for tool in tools:
                adk_tool = self._langchain_to_adk_tool(tool)
                if adk_tool:
                    adk_tools.append(adk_tool)
        
        # Create agent config
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            tools=adk_tools if adk_tools else None
        )
        
        agent = ADKAgent(
            client=self.client,
            agent_name=agent_name,
            model=model,
            config=config,
            langchain_tools={tool.name: tool for tool in (tools or [])}
        )
        
        logger.info(f"Agent {agent_name} created with {len(adk_tools)} tools")
        
        return agent
    
    def _langchain_to_adk_tool(self, langchain_tool: BaseTool) -> Optional[types.Tool]:
        """
        Convert LangChain tool to ADK tool format.
        
        ADK uses function declarations that match the tool's schema.
        """
        try:
            # Get tool schema
            tool_name = langchain_tool.name
            tool_description = langchain_tool.description
            
            # Create function declaration
            function_declaration = types.FunctionDeclaration(
                name=tool_name,
                description=tool_description,
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
            
            # Wrap in Tool
            adk_tool = types.Tool(
                function_declarations=[function_declaration]
            )
            
            return adk_tool
            
        except Exception as e:
            logger.error(f"Failed to convert tool {langchain_tool.name}: {e}")
            return None


class ADKAgent:
    """
    Google ADK Agent with LangChain tool support.
    
    This agent uses Google's ADK for the core agent loop,
    but executes LangChain tools when function calls are made.
    """
    
    def __init__(
        self,
        client: "genai.Client",
        agent_name: str,
        model: str,
        config: types.GenerateContentConfig,
        langchain_tools: Dict[str, BaseTool]
    ):
        self.client = client
        self.agent_name = agent_name
        self.model = model
        self.config = config
        self.langchain_tools = langchain_tools
        self.conversation_history = []
        
        logger.info(f"ADK Agent '{agent_name}' initialized")
    
    async def run(self, user_message: str, max_iterations: int = 5) -> str:
        """
        Run the agent with a user message.
        
        Args:
            user_message: User's input message
            max_iterations: Maximum tool call iterations
            
        Returns:
            Agent's final response
        """
        logger.info(f"Agent '{self.agent_name}' processing: {user_message[:100]}...")
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.conversation_history,
                config=self.config
            )
            
            # Check if response has function calls
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                if hasattr(candidate, 'function_calls') and candidate.function_calls:
                    # Execute function calls
                    function_results = []
                    
                    for function_call in candidate.function_calls:
                        result = await self._execute_function(function_call)
                        function_results.append(result)
                    
                    # Add function call and results to history
                    self.conversation_history.append({
                        "role": "model",
                        "parts": [{"function_call": fc} for fc in candidate.function_calls]
                    })
                    
                    self.conversation_history.append({
                        "role": "function",
                        "parts": [{"function_response": fr} for fr in function_results]
                    })
                    
                    # Continue loop to get final response
                    continue
            
            # No function calls, extract text response
            if hasattr(response, 'text'):
                final_response = response.text
            else:
                final_response = str(response)
            
            # Add to history
            self.conversation_history.append({
                "role": "model",
                "parts": [{"text": final_response}]
            })
            
            logger.info(f"Agent '{self.agent_name}' responded after {iteration} iterations")
            
            return final_response
        
        logger.warning(f"Agent '{self.agent_name}' reached max iterations")
        return "I apologize, but I've reached my processing limit. Please try rephrasing your request."
    
    async def _execute_function(self, function_call) -> Dict[str, Any]:
        """Execute a LangChain tool based on function call"""
        
        function_name = function_call.name
        function_args = function_call.args
        
        logger.info(f"Executing function: {function_name}")
        
        # Get LangChain tool
        tool = self.langchain_tools.get(function_name)
        
        if not tool:
            logger.error(f"Tool '{function_name}' not found")
            return {
                "name": function_name,
                "response": {
                    "error": f"Tool '{function_name}' not available"
                }
            }
        
        try:
            # Execute tool
            if hasattr(tool, 'arun'):
                result = await tool.arun(**function_args)
            else:
                result = tool.run(**function_args)
            
            logger.info(f"Function '{function_name}' executed successfully")
            
            return {
                "name": function_name,
                "response": {
                    "result": result
                }
            }
            
        except Exception as e:
            logger.error(f"Function '{function_name}' failed: {e}")
            return {
                "name": function_name,
                "response": {
                    "error": str(e)
                }
            }
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        logger.info(f"Agent '{self.agent_name}' conversation reset")


# Singleton factory instance
_factory_instance = None


def get_adk_factory() -> ADKAgentFactory:
    """Get singleton ADK factory instance"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ADKAgentFactory()
    return _factory_instance
