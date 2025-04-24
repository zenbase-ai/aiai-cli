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

            <guidelines>
                <always>
                    1. Begin each email by personally addressing the lead by name and explicitly
                       referencing their role and company in the opening sentence.
                    2. Clearly state at least two Zenbase benefits, mapping each directly to
                       the lead's specific pain points or goals.
                    3. Mention DSPy by name as a foundational differentiator for Zenbase within the email body.
                    4. Structure the email in two to three concise paragraphs with a clear, logical flow.
                    5. Conclude every email with a clear, direct, and actionable call to action
                       (e.g., propose a demo or next step).
                </always>
                <never>
                    1. Use generic, templated, or boilerplate language or structure.
                    2. Return emails that omit the recipient's name, role, company, or specific pain points.
                    3. Write emails that exceed three paragraphs or are less than two paragraphs.
                    4. Leave out mention of Zenbase's DSPy foundation or misrepresent its relationship to Zenbase.
                    5. Return an email without a clear, actionable call to action.
                </never>
                <tips>
                    1. Personalize the subject line by referencing the recipient's company, role,
                       or a primary pain point for increased engagement.
                    2. Acknowledge the lead's challenges or context early in the email
                       to demonstrate relevance and empathy.
                    3. Match Zenbase benefits and messaging to the recipient's industry,
                       technical background, and specific business needs.
                    4. Use concise, professional, and benefit-oriented language that
                       remains readable and free from unnecessary jargon.
                    5. Ensure the call to action is specific, actionable, and easy for the lead to respond to
                       (e.g., scheduling a demo tailored to their workflow).
                </tips>
            </guidelines>
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
