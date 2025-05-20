from typing import Optional, TypedDict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph


class ContentState(TypedDict, total=False):
    topic: str
    outline: Optional[str]
    content: Optional[str]
    output: Optional[str]


def create_agent():
    """
    Simple content creation using LangGraph

    Takes a topic as input, creates an outline, and then
    expands it into content using a minimal LangGraph.
    """
    llm = ChatOpenAI(model="gpt-4o-mini")

    # Define simple functions for each step
    def create_outline(state: ContentState) -> ContentState:
        """Create an outline based on the topic"""
        prompt = f"Create a brief outline with 2-3 main points about: {state['topic']}"
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"topic": state["topic"], "outline": response.content.strip()}

    def expand_content(state: ContentState) -> ContentState:
        """Expand the outline into content"""
        prompt = f"Write a short article using this outline. Keep it concise:\n\n{state['outline']}"
        response = llm.invoke([HumanMessage(content=prompt)])
        return {**state, "content": response.content.strip()}

    def format_result(state: ContentState) -> ContentState:
        """Format the final output"""
        output = f"OUTLINE:\n{state['outline']}\n\nCONTENT:\n{state['content']}"
        return {**state, "output": output}

    # Create a minimal graph with state schema
    workflow = StateGraph(ContentState)

    # Add our simple nodes
    workflow.add_node("create_outline", create_outline)
    workflow.add_node("expand_content", expand_content)
    workflow.add_node("format_result", format_result)

    # Connect the nodes in sequence
    workflow.add_edge(START, "create_outline")
    workflow.add_edge("create_outline", "expand_content")
    workflow.add_edge("expand_content", "format_result")
    workflow.add_edge("format_result", END)

    # Compile the graph
    return workflow.compile()
