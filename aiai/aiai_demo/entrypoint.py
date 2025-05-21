import os

import openai


def create_outline(topic):
    """
    Step 1: Create a simple outline based on the provided topic
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Create short, simple outlines with 2-3 main points."},
            {"role": "user", "content": f"Create a brief outline about: {topic}"},
        ],
    )

    return response.choices[0].message.content


def expand_to_content(outline):
    """
    Step 2: Expand the outline into concise content
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Create brief, concise content from outlines."},
            {"role": "user", "content": f"Write a short article using this outline. Keep it concise:\n\n{outline}"},
        ],
    )

    return response.choices[0].message.content


def main(example=None):
    """
    Entry point for the content creation agent.
    Takes a topic, creates an outline, then expands it into brief content.
    """
    example = example or "Benefits of exercise"

    outline = create_outline(example)
    full_content = expand_to_content(outline)

    final_output = f"OUTLINE:\n{outline}\n\nCONTENT:\n{full_content}"
    return final_output
