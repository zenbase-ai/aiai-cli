"""
Entry point for the LangGraph lead processing example.

This script loads lead data, extracts lead information, and generates personalized sales emails
using a LangGraph workflow.
"""

import os
import sys

from dotenv import load_dotenv

from aiai.examples.langgraph.langgraph_agent import LeadProcessingGraph


def main():
    """Run the lead processing graph"""
    # Load environment variables from .env file
    load_dotenv()

    # Check for OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("Error: OpenAI API key not found.")
        print("Please set your OPENAI_API_KEY environment variable or add it to a .env file.")
        sys.exit(1)

    # Create sample data file if it doesn't exist
    sample_data = {
        "leads_text": "Amir Mehr is the CTO of Zenbase AI with a focus on optimizing LLM workflows. "
        "Sarah Johnson is a Lead Developer at Tech Solutions Inc. interested in prompt engineering and model "
        "selection."
    }

    raw_leads_text = sample_data.get("leads_text")

    # Run the LangGraph workflow, passing the data
    graph = LeadProcessingGraph()
    result = graph.run(raw_leads_text=raw_leads_text)
    return result


if __name__ == "__main__":
    main()
