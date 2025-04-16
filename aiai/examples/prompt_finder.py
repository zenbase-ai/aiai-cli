#!/usr/bin/env python
"""
Prompt Finder

This script analyzes AgentRunLog objects to find where prompts are defined or used
in the codebase, specifically focusing on FunctionInfo objects in the database.
"""

from typing import Any, Optional
import typer

from dotenv import load_dotenv
from pydantic import BaseModel, Field
import instructor
from litellm import completion

from aiai.utils import setup_django

load_dotenv()

# Initialize typer app
app = typer.Typer(help="Find prompts from logs in the codebase")


# Pydantic models for LLM structured output
class PromptFragment(BaseModel):
    """Represents a fragment of a prompt found in code."""

    function_name: str = Field(
        description="Name of the function where the fragment was found"
    )
    file_path: str = Field(description="Path to the file containing the function")
    line_number: int = Field(description="Exact line number where the fragment appears")
    fragment_code: str = Field(
        description="The exact code that defines or constructs the prompt fragment"
    )


class PromptAnalysis(BaseModel):
    """Analysis of where a prompt is constructed in the codebase."""

    fragments: list[PromptFragment] = Field(
        description="Code fragments that make up the prompt"
    )
    composite_locations: list[str] = Field(
        description="Functions that assemble multiple fragments"
    )


def analyze_prompt_with_llm(
    prompt_text: str, function_info_list: list[Any]
) -> PromptAnalysis:
    """
    Use LLM to find where prompt fragments are defined and used within functions.

    Args:
        prompt_text: The prompt text to search for
        function_info_list: List of FunctionInfo objects from database

    Returns:
        PromptAnalysis with fragment locations and composite functions
    """
    client = instructor.from_litellm(completion)

    # Prepare function code samples with line numbers for precise location
    function_samples = []
    for func in function_info_list:
        # Add line numbers to code for easier reference
        code_with_lines = ""
        for i, line in enumerate(func.source_code.split("\n"), func.line_start):
            code_with_lines += f"{i}: {line}\n"

        function_samples.append(
            f"FUNCTION: {func.name}\nFILE: {func.file_path}\nLINES: {func.line_start}-{func.line_end}\n"
            f"```python\n{code_with_lines}```\n"
        )

    # Clear, structured system prompt for smaller models
    system_prompt = (
        "You are a code analyzer specialized in finding text prompts in Python code. "
        "Your task is to locate exactly where prompt text is defined, constructed, or assembled. "
        "Respond with the precise file paths, line numbers, and code snippets. "
        "Focus only on finding the most relevant code that defines or constructs the prompt."
    )

    # Highly structured user prompt with clear sections and instructions
    user_prompt = f"""
TASK: Find where the following prompt text is defined in code

PROMPT TO FIND:
<prompt>
{prompt_text}
</prompt>

SEARCH INSTRUCTIONS:
1. Find EXACT STRING LITERALS that match parts of the prompt
2. Identify VARIABLE ASSIGNMENTS that later form the prompt
3. Look for STRING CONCATENATION or F-STRINGS that build the prompt
4. Note any FUNCTIONS that combine text fragments into the prompt

CODE TO SEARCH:
{chr(10).join(function_samples)}

REQUIRED OUTPUT FORMAT:
- For each match, provide exact line number and code snippet
- Only include relevant code that defines or builds the prompt
"""

    # Call LLM with structured output - using o3-mini model
    try:
        response = client.chat.completions.create(
            model="o3-mini",  # Using o3-mini as requested
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_model=PromptAnalysis,
        )
        return response
    except Exception as e:
        print(f"LLM API error: {e}")
        # Return empty analysis on error
        return PromptAnalysis(fragments=[], composite_locations=[])


@app.command()
def find_prompts(
    log_id: Optional[int] = typer.Option(
        None, help="Specific AgentRunLog ID to analyze"
    )
):
    """
    Find where prompts from AgentRunLogs are defined and constructed in code.
    """
    # Import models after Django setup
    from aiai.app.models import AgentRunLog, FunctionInfo

    # Load all functions once
    functions = list(FunctionInfo.objects.all())
    print(f"Loaded {len(functions)} functions from database")

    # Query for logs
    if log_id:
        logs = AgentRunLog.objects.filter(id=log_id)
        if not logs:
            print(f"No log found with ID {log_id}")
            return
    else:
        logs = AgentRunLog.objects.all()

    # Process each log
    for log in logs:
        # Extract prompt from input_data
        prompt = None
        if (
            log.input_data
            and "prompt" in log.input_data
            and isinstance(log.input_data["prompt"], str)
        ):
            prompt = log.input_data["prompt"]

        if not prompt:
            continue

        print(f"\n{'='*60}")
        print(f"LOG ID: {log.id} | RUN ID: {log.agent_run_id or 'N/A'}")
        print(f"{'='*60}")

        # Show prompt snippet
        print(f"PROMPT: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        # Analyze with LLM
        analysis = analyze_prompt_with_llm(prompt, functions)

        # Print results in a clear format
        if analysis.fragments:
            print("\nPROMPT DEFINITION LOCATIONS:")
            print("-" * 50)

            for fragment in analysis.fragments:
                print(
                    f"\n{fragment.file_path}:{fragment.line_number} in {fragment.function_name}()"
                )
                print(f"Code: {fragment.fragment_code.strip()}")

        if analysis.composite_locations:
            print("\nPROMPT ASSEMBLY LOCATIONS:")
            print("-" * 50)
            for location in analysis.composite_locations:
                print(f"• {location}")

        if not analysis.fragments and not analysis.composite_locations:
            print("\nNo matches found for this prompt")


if __name__ == "__main__":
    # Setup Django before importing models
    setup_django()

    # Run the Typer app
    app()
