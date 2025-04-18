"""
LangGraph example implementation of a lead processing agent.

This example demonstrates using LangGraph to create a workflow that:
1. Loads lead data from a JSON file
2. Extracts lead information using an LLM
3. Generates personalized sales emails for each lead
"""

from aiai.examples.langgraph.langgraph_agent import LeadProcessingGraph as LeadProcessingGraph
