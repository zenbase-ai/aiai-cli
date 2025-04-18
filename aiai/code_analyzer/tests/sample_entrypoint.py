from textwrap import dedent

from crewai import Agent, Crew, Process, Task
from crewai_tools import FileReadTool


def get_crewai_agent():
    file_read_tool = FileReadTool(file_path="people_data.json")

    lead_extractor = Agent(
        role="Lead Profile Extractor",
        goal="Extract relevant details (name, company, role, specific interests/pain points) for each person from the "
        "provided data.",
        backstory=dedent("""\
            You are an expert analyst specializing in identifying key information 
            from unstructured data. Your goal is to pinpoint the most relevant details 
            about a potential lead that can be used for personalized outreach.
            """),
        verbose=True,
        allow_delegation=False,
        tools=[file_read_tool],
    )

    email_crafter = Agent(
        role="Zenbase Sales Email Crafter",
        goal="Write a concise and compelling personalized sales email to a potential lead, highlighting how Zenbase "
        "can address their specific needs related to LLM development, prompt engineering, and model optimization.",
        backstory=dedent("""\
            You are a persuasive sales copywriter with deep knowledge of Zenbase. 
            Zenbase helps developers automate prompt engineering and model selection, 
            leveraging DSPy to optimize LLM applications and improve performance. 
            You tailor your emails based on the lead's specific role and challenges 
            to maximize engagement.
            Key Zenbase benefits: Automates prompt engineering, optimizes model selection, 
            improves LLM performance, reduces development time, leverages DSPy algorithms.
            """),
        verbose=True,
        allow_delegation=False,
    )

    extract_task = Task(
        description=dedent("""\
            Read the 'people_data.json' file. The file contains a JSON object 
            with a key 'leads_text' which holds a single block of text describing multiple leads.
            Parse this text to identify and extract the key details 
            (name, company, role, specific details indicating needs/interests) 
            for each person mentioned. Format the output clearly for the email writer.
            """),
        expected_output=dedent("""\
            A structured summary for each lead found in the text, containing:
            - Name
            - Company
            - Role
            - Key Details/Pain Points relevant to LLM optimization or development efficiency.
            
            Example:
            Lead 1:
              Name: Amir Mehr
              Company: Zenbase AI
              Role: CTO
              Key Details: Interested in optimizing LLM workflows.
            Lead 2:
              Name: Bob Williams
              Company: Data Insights Inc.
              Role: Lead Data Scientist
              Key Details: Challenges with prompt variability.
            """),
        agent=lead_extractor,
    )

    email_task = Task(
        description=dedent("""\
            For each lead profile extracted in the previous step, write a personalized 
            sales email. Use the lead's specific details (role, company, pain points) 
            to explain how Zenbase can help them automate prompt engineering, 
            select the best models, and ultimately build better LLM applications faster.
            Reference Zenbase's connection to DSPy and its benefits.
            Keep the email concise (2-3 paragraphs) and professional.
            """),
        expected_output=dedent("""\ A series of personalized sales emails, one for each lead. Each email should: - Be 
        addressed to the lead by name. - Reference their role/company/specific details. - Clearly explain relevant 
        Zenbase benefits (automated prompt engineering, model optimization, faster development, DSPy foundation). - 
        Include a clear call to action (e.g., suggest a demo or provide a link).
            
            Example Email for Cyrus Nouroozi:
            
            Subject: Optimizing LLM Workflows at Innovate Solutions with Zenbase
            
            Hi Cyrus,
            
            Knowing your focus on AI integration and optimizing LLM workflows at Innovate Solutions, I wanted to 
            introduce Zenbase... [Explain how Zenbase helps with workflow optimization, automated prompting/model 
            selection]... ...Built on core contributions to Stanford's DSPy framework, Zenbase automates... [Call to 
            action - e.g., schedule a demo?]
            
            Best regards,
            [Your Name/Zenbase Team]
            """),
        agent=email_crafter,
        context=[extract_task],
    )

    crew = Crew(
        agents=[lead_extractor, email_crafter],
        tasks=[extract_task, email_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def main():
    print("Starting Crew execution...")
    get_crewai_agent()
