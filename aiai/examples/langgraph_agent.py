import json
from textwrap import dedent
from typing import Annotated, TypedDict

import openlit
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from aiai.runner.otel_exporter import DjangoSpanExporter

provider = TracerProvider()
trace.set_tracer_provider(provider)

my_processor = BatchSpanProcessor(DjangoSpanExporter())
provider.add_span_processor(my_processor)

openlit.init()

# Ensure the OpenAI API key is set (consider a more secure method in production)
# Make sure you have a 'people_data.json' file in the same directory
# with the structure: {"leads_text": "Text containing lead info..."}
# Example: {"leads_text": "Amir Mehr is the CTO at Zenbase AI, focused on optimizing LLM workflows.
# Bob Williams, Lead Data Scientist at Data Insights Inc., faces challenges with prompt variability."}


# 1. Define the State for the graph
class AgentState(TypedDict):
    raw_leads_text: str | None
    extracted_leads: list[dict[str, str]] | None
    generated_emails: list[str] | None
    # Using 'messages' for potential conversation history if needed later
    messages: Annotated[list[BaseMessage], add_messages]


# 2. Define Node Functions
def load_data(state: AgentState) -> AgentState:
    """Loads the raw lead text from the JSON file."""
    print("---LOADING DATA---")
    file_path = "people_data.json"  # Assumes file is in the same directory
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        raw_text = data.get("leads_text")
        if not raw_text:
            raise ValueError("'leads_text' key not found or empty in people_data.json")
        print(f"Loaded text: {raw_text[:100]}...")  # Print snippet
        return {"raw_leads_text": raw_text}
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        # Stop execution or return a specific state indicating failure
        return {"raw_leads_text": None}  # Or handle error differently
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}.")
        return {"raw_leads_text": None}
    except Exception as e:
        print(f"An unexpected error occurred during data loading: {e}")
        return {"raw_leads_text": None}


def extract_leads(state: AgentState) -> AgentState:
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

        Respond ONLY with a JSON list of objects, where each object represents a lead and has the keys:
        'name', 'company', 'role', 'key_details'.

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


def craft_emails(state: AgentState) -> AgentState:
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

            Tailor the email based on the lead's specific role and challenges to maximize engagement.
            Highlight how Zenbase can address their specific needs related to LLM development, prompt engineering,
            and model optimization.

            Reference Zenbase's connection to DSPy and its benefits.
            Include a clear call to action (e.g., suggest a demo or provide a link to learn more).
            Sign off as 'The Zenbase Team'.

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


# 3. Build the Graph
graph_builder = StateGraph(AgentState)

# Add nodes
graph_builder.add_node("load_data", load_data)
graph_builder.add_node("extract_leads", extract_leads)
graph_builder.add_node("craft_emails", craft_emails)

# Define edges
graph_builder.add_edge(START, "load_data")
graph_builder.add_edge("load_data", "extract_leads")
graph_builder.add_edge("extract_leads", "craft_emails")
graph_builder.add_edge("craft_emails", END)

# 4. Compile the graph
app = graph_builder.compile()

# 5. Run the graph
if __name__ == "__main__":
    print("Starting LangGraph execution...")

    initial_state = {"messages": []}
    final_state = app.invoke(initial_state)

    print("########################")
    print("## LangGraph Execution Result:")
    print("########################")

    if final_state.get("generated_emails"):
        print("Generated Emails:")
        for i, email in enumerate(final_state["generated_emails"]):
            print(f"--- Email {i + 1} ---")
            print(email)
            print("-" * 20)
    else:
        print("No emails were generated. Check logs for errors.")
