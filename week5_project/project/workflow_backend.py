"""
Backend workflow module for the multi-agent Medium article generator.
This module provides clean interfaces for Streamlit to interact with the LangGraph workflow.
"""

from typing import List, Tuple, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage
from reflection_agent import (
    research_node, generate_node, fact_check_node, reflect_node,
    RESEARCH, GENERATE, FACT_CHECK, REFLECT
)

class WorkflowManager:
    """Manages the multi-agent workflow execution for Streamlit UI"""
    
    def __init__(self):
        self.current_step = None
        self.workflow_state = []
        
    def reset_workflow(self):
        """Reset the workflow state"""
        self.current_step = None
        self.workflow_state = []
        
    def initialize_workflow(self, topic: str):
        """Initialize workflow with a topic"""
        self.workflow_state = [HumanMessage(content=topic)]
        self.current_step = RESEARCH
        
    def run_single_step(self) -> Tuple[List[BaseMessage], str]:
        """
        Run a single workflow step and return updated state and next step
        Returns: (new_state, next_step)
        """
        try:
            if self.current_step == RESEARCH:
                new_state = research_node(self.workflow_state)
                next_step = GENERATE
                
            elif self.current_step == GENERATE:
                result = generate_node(self.workflow_state)
                new_state = self.workflow_state + [result]
                next_step = FACT_CHECK
                
            elif self.current_step == FACT_CHECK:
                new_state = fact_check_node(self.workflow_state)
                next_step = "HUMAN_REVIEW"
                
            elif self.current_step == REFLECT:
                result = reflect_node(self.workflow_state)
                new_state = self.workflow_state + result
                # Check if we should continue (simplified logic)
                if len(new_state) > 12:
                    next_step = "END"
                else:
                    next_step = GENERATE
                    
            else:
                return self.workflow_state, "END"
                
            self.workflow_state = new_state
            self.current_step = next_step
            return new_state, next_step
            
        except Exception as e:
            return self.workflow_state, f"ERROR: {str(e)}"
    
    def process_human_feedback(self, feedback: str) -> str:
        """
        Process human feedback and determine next step
        Returns: next_step
        """
        # Add human feedback to state
        self.workflow_state.append(HumanMessage(content=feedback))
        
        if "approve" in feedback.lower():
            self.current_step = "END"
            return "END"
        else:
            self.current_step = REFLECT
            return REFLECT
    
    def extract_content(self, content_type: str) -> str:
        """Extract specific content from the workflow state"""
        if not self.workflow_state:
            return "No content available"
        
        if content_type == "research":
            for msg in self.workflow_state:
                if isinstance(msg, SystemMessage) and "Research on" in msg.content:
                    return msg.content
                    
        elif content_type == "article":
            # Find the actual generated article (AIMessage from generate_node)
            for msg in reversed(self.workflow_state):
                # Look for AIMessage (the actual generated content) that's not research or fact-check
                if (isinstance(msg, AIMessage) and 
                    hasattr(msg, 'content') and 
                    len(msg.content) > 100 and
                    "Research on" not in msg.content and
                    not self._is_fact_check_content(msg.content) and
                    not self._is_reflection_content(msg.content)):
                    return msg.content
                        
        elif content_type == "fact_check":
            for msg in reversed(self.workflow_state):
                if isinstance(msg, HumanMessage) and self._is_fact_check_content(msg.content):
                    return msg.content
                    
        elif content_type == "reflection":
            for msg in reversed(self.workflow_state):
                if isinstance(msg, HumanMessage) and self._is_reflection_content(msg.content):
                    return msg.content
        
        return "Content not available yet"
    
    def _is_fact_check_content(self, content: str) -> bool:
        """Check if content is fact-check feedback"""
        fact_check_indicators = [
            "fact-check", "accuracy", "factual claims", "misinformation", 
            "corrections", "verify", "assessment", "detailed fact-check"
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in fact_check_indicators)
    
    def _is_reflection_content(self, content: str) -> bool:
        """Check if content is reflection/critique"""
        reflection_indicators = [
            "critique", "recommendation", "improve", "suggestions", 
            "feedback", "revise", "enhance", "better"
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in reflection_indicators)
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "current_step": self.current_step,
            "message_count": len(self.workflow_state),
            "is_complete": self.current_step == "END",
            "needs_human_review": self.current_step == "HUMAN_REVIEW"
        }

# Global workflow manager instance
workflow_manager = WorkflowManager()
