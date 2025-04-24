from textwrap import dedent

import rich
from crewai import Agent, Crew, CrewOutput, Process, Task
from dotenv import load_dotenv


def get_crewai_agent():
    email_crafter = Agent(
        role="Zenbase Sales Email Crafter",
        goal=dedent(
            """\
            Write a concise and compelling personalized sales email to a potential lead,
            highlighting how Zenbase can address their specific needs related to
            LLM development, prompt engineering, and model optimization.
            """
        ),
        backstory=dedent(
            """\
            You are a persuasive sales copywriter with deep knowledge of Zenbase.
            Zenbase helps developers automate prompt engineering and model selection,
            leveraging DSPy to optimize LLM applications and improve performance.
            You tailor your emails based on the lead's specific role and challenges
            to maximize engagement.
            Key Zenbase benefits: Automates prompt engineering, optimizes model selection,
            improves LLM performance, reduces development time, leverages DSPy algorithms.
            """
        ),
        verbose=True,
        allow_delegation=False,
    )

    email_task = Task(
        description=dedent(
            """\
            Write a personalized sales email. Use the lead's specific details
            (role, company, pain points) to explain how Zenbase can help them
            automate prompt engineering, select the best models, and ultimately
            build better LLM applications faster. Reference Zenbase's connection
            to DSPy and its benefits. Keep the email concise (2-3 paragraphs)
            and professional.

            <lead>
            {lead}
            </lead>
            """
        ),
        expected_output=dedent(
            """\
            A series of personalized sales emails, one for each lead.
            Each email should:
            - Be addressed to the lead by name.
            - Reference their role/company/specific details.
            - Clearly explain relevant Zenbase benefits (automated prompt engineering,
              model optimization, faster development, DSPy foundation).
            - Include a clear call to action (e.g., suggest a demo or provide a link).

            Example Email for Cyrus Nouroozi:

            Subject: Optimizing LLM Workflows at Innovate Solutions with Zenbase

            Hi Cyrus,

            Knowing your focus on AI integration and optimizing LLM workflows at
            Innovate Solutions, I wanted to introduce Zenbase...
            [Explain how Zenbase helps with workflow optimization, automated prompting/model selection]...
            ...Built on core contributions to Stanford's DSPy framework, Zenbase automates...
            [Call to action - e.g., schedule a demo?]

            Best regards,
            [Your Name/Zenbase Team]
            """
        ),
        agent=email_crafter,
    )

    crew = Crew(
        agents=[email_crafter],
        tasks=[email_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def main(example=None):
    load_dotenv()
    print("Starting Crew execution...")
    crew = get_crewai_agent()
    example = example or dedent(
        """\
        Jessica Collins, CTO at FinOptima, a mid-sized fintech startup, struggles
        with balancing model selection trade-offs, managing complex versioning of
        multiple LLMs in fraud detection pipelines, latency, and cost-per-token
        ratios during peak times.
        """
    )
    result: CrewOutput = crew.kickoff({"lead": example})
    return result.raw


if __name__ == "__main__":
    rich.print(main())
