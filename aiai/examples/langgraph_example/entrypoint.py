"""
Entry point for the LangGraph lead processing example.

This script loads lead data, extracts lead information, and generates personalized sales emails
using a LangGraph workflow.
"""

from textwrap import dedent

from dotenv import load_dotenv

from aiai.examples.langgraph.langgraph_agent import LeadProcessingGraph


def main():
    """Run the lead processing graph"""
    load_dotenv()

    example = dedent(
        """\
        Amir Mehr is the CTO of Zenbase AI with a focus on optimizing LLM workflows.
        Sarah Johnson is a Lead Developer at Tech Solutions Inc.
        interested in prompt engineering and model selection.
        """
    )

    graph = LeadProcessingGraph()
    result = graph.run(raw_leads_text=example)
    return result


if __name__ == "__main__":
    main()
