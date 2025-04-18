# ruff: noqa: E501

from textwrap import dedent

import pytest

from aiai.app.models import FunctionInfo


@pytest.fixture(scope="session")
def mock_function_info():
    return [
        FunctionInfo(
            name="get_crewai_agent",
            file_path="crewai_agent.py",
            line_start=8,
            line_end=83,
            signature="get_crewai_agent()",
            source_code="""def get_crewai_agent():
    email_crafter = Agent(
        role="Zenbase Sales Email Crafter",
        goal=dedent(
            \"\"\"\
            Write a concise and compelling personalized sales email to a potential lead,
            highlighting how Zenbase can address their specific needs related to
            LLM development, prompt engineering, and model optimization.
            \"\"\"
        ),
        backstory=dedent(
            \"\"\"\
            You are a persuasive sales copywriter with deep knowledge of Zenbase.
            Zenbase helps developers automate prompt engineering and model selection,
            leveraging DSPy to optimize LLM applications and improve performance.
            You tailor your emails based on the lead's specific role and challenges
            to maximize engagement.
            Key Zenbase benefits: Automates prompt engineering, optimizes model selection,
            improves LLM performance, reduces development time, leverages DSPy algorithms.
            \"\"\"
        ),
        verbose=True,
        allow_delegation=False,
    )

    email_task = Task(
        description=dedent(
            \"\"\"\
            Write a personalized sales email. Use the lead's specific details
            (role, company, pain points) to explain how Zenbase can help them
            automate prompt engineering, select the best models, and ultimately
            build better LLM applications faster. Reference Zenbase's connection
            to DSPy and its benefits. Keep the email concise (2-3 paragraphs)
            and professional.

            <lead>
            {lead}
            </lead>
            \"\"\"
        ),
        expected_output=dedent(
            \"\"\"\
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
            \"\"\"
        ),
        agent=email_crafter,
    )

    crew = Crew(
        agents=[email_crafter],
        tasks=[email_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew""",
            docstring="",
            comments=["# This is a test function"],
            string_literals=[
                {"text": "Zenbase Sales Email Crafter", "line": 10},
                {
                    "text": '""\\\n            Write a concise and compelling personalized sales email to a potential lead,\n            highlighting how Zenbase can address their specific needs related to\n            LLM development, prompt engineering, and model optimization.\n            ""',
                    "line": 12,
                },
                {
                    "text": '""\\\n            You are a persuasive sales copywriter with deep knowledge of Zenbase.\n            Zenbase helps developers automate prompt engineering and model selection,\n            leveraging DSPy to optimize LLM applications and improve performance.\n            You tailor your emails based on the lead\'s specific role and challenges\n            to maximize engagement.\n            Key Zenbase benefits: Automates prompt engineering, optimizes model selection,\n            improves LLM performance, reduces development time, leverages DSPy algorithms.\n            ""',
                    "line": 19,
                },
                {
                    "text": '""\\\n            Write a personalized sales email. Use the lead\'s specific details\n            (role, company, pain points) to explain how Zenbase can help them\n            automate prompt engineering, select the best models, and ultimately\n            build better LLM applications faster. Reference Zenbase\'s connection\n            to DSPy and its benefits. Keep the email concise (2-3 paragraphs)\n            and professional.\n\n            <lead>\n            {lead}\n            </lead>\n            ""',
                    "line": 35,
                },
                {
                    "text": '""\\\n            A series of personalized sales emails, one for each lead.\n            Each email should:\n            - Be addressed to the lead by name.\n            - Reference their role/company/specific details.\n            - Clearly explain relevant Zenbase benefits (automated prompt engineering,\n              model optimization, faster development, DSPy foundation).\n            - Include a clear call to action (e.g., suggest a demo or provide a link).\n\n            Example Email for Cyrus Nouroozi:\n\n            Subject: Optimizing LLM Workflows at Innovate Solutions with Zenbase\n\n            Hi Cyrus,\n\n            Knowing your focus on AI integration and optimizing LLM workflows at\n            Innovate Solutions, I wanted to introduce Zenbase...\n            [Explain how Zenbase helps with workflow optimization, automated prompting/model selection]...\n            ...Built on core contributions to Stanford\'s DSPy framework, Zenbase automates...\n            [Call to action - e.g., schedule a demo?]\n\n            Best regards,\n            [Your Name/Zenbase Team]\n            ""',
                    "line": 49,
                },
            ],
            variables=[
                {
                    "name": "email_crafter",
                    "value": 'Agent(\n        role="Zenbase Sales Email Crafter",\n        goal=dedent(\n            """\\\n            Write a concise and compelling personalized sales email to a potential lead,\n            highlighting how Zenbase can address their specific needs related to\n            LLM development, prompt engineering, and model optimization.\n            """\n        ),\n        backstory=dedent(\n            """\\\n            You are a persuasive sales copywriter with deep knowledge of Zenbase.\n            Zenbase helps developers automate prompt engineering and model selection,\n            leveraging DSPy to optimize LLM applications and improve performance.\n            You tailor your emails based on the lead\'s specific role and challenges\n            to maximize engagement.\n            Key Zenbase benefits: Automates prompt engineering, optimizes model selection,\n            improves LLM performance, reduces development time, leverages DSPy algorithms.\n            """\n        ),\n        verbose=True,\n        allow_delegation=False,\n    )',
                    "line": 9,
                },
                {
                    "name": "email_task",
                    "value": 'Task(\n        description=dedent(\n            """\\\n            Write a personalized sales email. Use the lead\'s specific details\n            (role, company, pain points) to explain how Zenbase can help them\n            automate prompt engineering, select the best models, and ultimately\n            build better LLM applications faster. Reference Zenbase\'s connection\n            to DSPy and its benefits. Keep the email concise (2-3 paragraphs)\n            and professional.\n\n            <lead>\n            {lead}\n            </lead>\n            """\n        ),\n        expected_output=dedent(\n            """\\\n            A series of personalized sales emails, one for each lead.\n            Each email should:\n            - Be addressed to the lead by name.\n            - Reference their role/company/specific details.\n            - Clearly explain relevant Zenbase benefits (automated prompt engineering,\n              model optimization, faster development, DSPy foundation).\n            - Include a clear call to action (e.g., suggest a demo or provide a link).\n\n            Example Email for Cyrus Nouroozi:\n\n            Subject: Optimizing LLM Workflows at Innovate Solutions with Zenbase\n\n            Hi Cyrus,\n\n            Knowing your focus on AI integration and optimizing LLM workflows at\n            Innovate Solutions, I wanted to introduce Zenbase...\n            [Explain how Zenbase helps with workflow optimization, automated prompting/model selection]...\n            ...Built on core contributions to Stanford\'s DSPy framework, Zenbase automates...\n            [Call to action - e.g., schedule a demo?]\n\n            Best regards,\n            [Your Name/Zenbase Team]\n            """\n        ),\n        agent=email_crafter,\n    )',
                    "line": 33,
                },
                {
                    "name": "crew",
                    "value": "Crew(\n        agents=[email_crafter],\n        tasks=[email_task],\n        process=Process.sequential,\n        verbose=True,\n    )",
                    "line": 77,
                },
            ],
            constants=[],
        )
    ]


@pytest.fixture(scope="session")
def mock_examples():
    return [
        dedent(
            """\
            Jessica Collins, CTO at FinOptima, a mid-sized fintech startup, struggles
            with balancing model selection trade-offs, managing complex versioning of
            multiple LLMs in fraud detection pipelines, latency, and cost-per-token
            ratios during peak times.
            """
        )
    ]
