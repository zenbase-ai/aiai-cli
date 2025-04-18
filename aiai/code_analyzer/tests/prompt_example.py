"""
Sample file that contains various types of prompts for testing the context extraction.
"""

from pathlib import Path

# Define some system prompts
SYSTEM_PROMPT = """You are a helpful AI assistant. 
Your task is to provide clear and concise responses to questions."""

USER_PROMPT_TEMPLATE = "User question: {question}"


def load_prompt_from_file(filename):
    """
    Load a prompt from a file.

    Args:
        filename: The path to the file containing the prompt

    Returns:
        The prompt as a string
    """
    # Read the prompt from the file
    with open(filename, "r") as f:
        prompt = f.read()

    return prompt.strip()


def generate_response(question, system_prompt=SYSTEM_PROMPT):
    """
    Generate a response to a question using a prompt.

    Args:
        question: The user's question
        system_prompt: The system prompt to use

    Returns:
        The generated response
    """
    # Create the full prompt by combining the system prompt and the user question
    full_prompt = f"{system_prompt}\n\n{USER_PROMPT_TEMPLATE.format(question=question)}"

    # In a real implementation, this would call an LLM API
    response = call_llm_api(full_prompt)

    return response


def call_llm_api(prompt):
    """
    Call an LLM API with a prompt.

    Args:
        prompt: The prompt to send to the LLM

    Returns:
        The LLM's response
    """
    # This is a stub function - in a real implementation, this would call an actual API
    print(f"Sending prompt to LLM: {prompt[:50]}...")

    # Use a different text for demonstration purposes
    RESPONSE_TEMPLATE = """
    Based on your question, I would recommend the following:
    
    1. First, consider your specific requirements
    2. Then, evaluate available options
    3. Finally, make an informed decision
    """

    return RESPONSE_TEMPLATE


def load_prompts_from_directory(directory):
    """
    Load all prompt files from a directory.

    Args:
        directory: The directory containing prompt files

    Returns:
        A dictionary mapping prompt names to prompt contents
    """
    prompts = {}
    prompt_dir = Path(directory)

    for file_path in prompt_dir.glob("*.txt"):
        prompt_name = file_path.stem
        prompts[prompt_name] = load_prompt_from_file(file_path)

    return prompts


# Main function that ties everything together
def main():
    # Load a prompt from a file
    system_prompt = load_prompt_from_file("prompts/system_prompt.txt")

    # Generate a response to a question
    question = "How do I design a good prompt?"
    response = generate_response(question, system_prompt)

    print(response)


if __name__ == "__main__":
    main()
