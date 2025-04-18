"""
LangGraph agent implementation for processing lead data and generating emails.
"""

import json
from textwrap import dedent
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# Define the State for the graph
class AgentState(TypedDict):
    raw_leads_text: str  # Now required at input
    extracted_leads: list[dict[str, str]] | None
    generated_emails: list[str] | None
    # Using 'messages' for potential conversation history if needed later
    messages: Annotated[list[BaseMessage], add_messages]


class LeadProcessingGraph:
    """A LangGraph implementation for processing lead data and generating emails."""

    def __init__(self):
        """Initialize the lead processing graph."""
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build and compile the LangGraph."""
        # Build the Graph
        graph_builder = StateGraph(AgentState)

        # Add nodes
        # graph_builder.add_node("load_data", self.load_data) # Removed
        graph_builder.add_node("extract_leads", self.extract_leads)
        graph_builder.add_node("craft_emails", self.craft_emails)

        graph_builder.add_edge(START, "extract_leads")  # Start directly with extraction
        graph_builder.add_edge("extract_leads", "craft_emails")
        graph_builder.add_edge("craft_emails", END)

        # Compile the graph
        return graph_builder.compile()

    def extract_leads(self, state: AgentState) -> AgentState:
        """Extracts lead details using an LLM."""
        print("---EXTRACTING LEADS---")
        raw_text = state.get("raw_leads_text")
        if not raw_text:
            print("Error: No raw lead text found to process.")
            return {"extracted_leads": None}

        llm = ChatOpenAI(model="gpt-4o", temperature=0)  # Or another suitable model

        prompt = dedent(
            f"""
            You are an expert analyst specializing in identifying key information from unstructured data.
            Your goal is to pinpoint the most relevant details about potential leads from the provided text.

            Text containing lead information:
            ---
            {raw_text}
            ---

            Parse this text to identify and extract the key details (name, company, role, specific details indicating 
            needs/interests related to LLM optimization or development efficiency) for each person mentioned.

            Respond ONLY with a JSON list of objects, where each object represents a lead and has the keys: 'name', 
            'company', 'role', 'key_details'.

            Example JSON Output:
            [
              {{
                "name": "Amir Mehr",
                "company": "Zenbase AI",
                "role": "CTO",
                "key_details": "Interested in optimizing LLM workflows."
              }},
              {{
                "name": "Bob Williams",
                "company": "Data Insights Inc.",
                "role": "Lead Data Scientist",
                "key_details": "Challenges with prompt variability."
              }}
            ]
        """
        )

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            # Clean the response content
            content_str = response.content.strip()
            if content_str.startswith("```json"):  # Check for markdown fences
                content_str = content_str[7:-3].strip()  # Remove ```json\n and ```
            elif content_str.startswith("```"):  # Check for generic fences
                content_str = content_str[3:-3].strip()  # Remove ```\n and ```

            # Attempt to parse the cleaned JSON response
            extracted_data = json.loads(content_str)
            print(f"Extracted leads: {extracted_data}")
            return {"extracted_leads": extracted_data}
        except json.JSONDecodeError:
            print("Error: Failed to parse LLM response as JSON after cleaning.")
            print(f"Original LLM Response: {response.content}")
            print(f"Cleaned String: {content_str}")  # Log the cleaned string for debugging
            return {"extracted_leads": None}  # Handle error state
        except Exception as e:
            print(f"An error occurred during LLM call for extraction: {e}")
            return {"extracted_leads": None}

    def craft_emails(self, state: AgentState) -> AgentState:
        """Generates personalized emails for each extracted lead."""
        print("---CRAFTING EMAILS---")
        leads = state.get("extracted_leads")
        if not leads:
            print("Error: No extracted leads found to craft emails.")
            return {"generated_emails": None}

        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)  # Allow more creativity

        emails = []
        for lead in leads:
            prompt = dedent(
                f"""
                You are a persuasive sales copywriter with deep knowledge of Zenbase.
                Zenbase helps developers automate prompt engineering and model selection,
                leveraging DSPy to optimize LLM applications and improve performance.
                Key Zenbase benefits: Automates prompt engineering, optimizes model selection,
                improves LLM performance, reduces development time, leverages DSPy algorithms.

                Write a concise (2-3 paragraphs) and compelling personalized sales email to the following lead:
                Name: {lead.get("name", "N/A")}
                Company: {lead.get("company", "N/A")}
                Role: {lead.get("role", "N/A")}
                Key Details/Pain Points: {lead.get("key_details", "N/A")}

                Tailor the email based on the lead's specific role and challenges to maximize engagement. Highlight how 
                Zenbase can address their specific needs related to LLM development, prompt engineering, 
                and model optimization. Reference Zenbase's connection to DSPy and its benefits. 
                Include a clear call to 
                action (e.g., suggest a demo or provide a link to learn more). Sign off as 'The Zenbase Team'.

                Format the output as a single email text block. Start directly with the subject line.
                Example Subject: Subject: Optimizing LLM Workflows at [Company Name] with Zenbase

                --- EMAIL TEXT BELOW ---
            """
            )
            try:
                response = llm.invoke([HumanMessage(content=prompt)])
                email_text = response.content
                print(f"Generated email for {lead.get('name', 'Unknown')}:{email_text}---")
                emails.append(email_text)
            except Exception as e:
                print(f"An error occurred during LLM call for crafting email for {lead.get('name', 'Unknown')}: {e}")
                # Decide whether to skip this email or stop

        return {"generated_emails": emails}

    def run(self, raw_leads_text: str):
        """Run the lead processing graph with the provided raw leads text."""
        print("Starting LangGraph execution...")
        # Set up initial state with the provided text
        initial_state = {
            "raw_leads_text": raw_leads_text,
            "messages": [],
        }
        # Execute the graph
        result = self.graph.invoke(initial_state)

        # Display results
        if result.get("generated_emails"):
            print("\n\n########################")
            print("## Generated Emails:")
            print("########################\n")
            for i, email in enumerate(result["generated_emails"]):
                print(f"\n--- Email {i + 1} ---\n{email}\n")
        else:
            print("No emails were generated. Check for errors in the previous steps.")

        return result
