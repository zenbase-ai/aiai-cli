import json
import os
import tempfile
from pathlib import Path

from docetl.api import (
    Dataset,
    MapOp,
    Pipeline,
    PipelineOutput,
    PipelineStep,
)
from utils import setup_django

cwd = Path(__file__).parent


def build_prompt_finder_pipeline(**kwargs) -> Pipeline:
    """
    Build a pipeline for identifying functions that contain prompts or define agents.

    Args:
        **kwargs: Additional arguments to pass to the Pipeline constructor

    Returns:
        Pipeline: A configured pipeline instance
    """
    operations = [
        MapOp(
            name="identify_prompt_functions",
            type="map",
            prompt="""
                <instructions>
                    You are an expert in code analysis. Your task is to identify functions that contain 
                    prompts for LLMs or define LLM agents within them.
                    
                    You will be given the source code of a function. Analyze it to determine if:
                    1. It contains prompt templates (strings with placeholders for LLM calls)
                    2. It defines an agent or agent system that interacts with LLMs
                    3. It creates or configures prompts that will be sent to LLMs
                    
                    Look for:
                    - String literals with XML/HTML-like tags (<instructions>, <output>, etc.)
                    - Template strings with placeholders ({% raw %}{{variable}}{% endraw %}, {% raw %}{variable}{% endraw %}, etc.)
                    - Variables/objects named "prompt", "template", "system_message", etc.
                    - Agent definitions or configurations
                    - LLM API calls with prompt content
                </instructions>
                
                <function>
                    Name: {{input.name}}
                    File Path: {{input.file_path}}
                    Line Range: {{input.line_start}}-{{input.line_end}}
                    Signature: {{input.signature}}
                    
                    Source Code:
                    {{input.source_code}}
                    
                    {% if input.docstring %}
                    Docstring:
                    {{input.docstring}}
                    {% endif %}
                </function>
                
                <output>
                    contains_prompt: Does this function contain a prompt or define an agent? (true/false)
                    prompt_type: What type of prompt/agent is used? (e.g., "instruction_prompt", "agent_definition", "chain_of_thought", etc.)
                    prompt_lines: The line numbers where the prompt is defined (e.g., "15-25")
                    prompt_segments: A list of the specific prompt segments in the function
                    confidence: A percentage (0-100) indicating your confidence in this analysis
                    explanation: Brief explanation of why you believe this function contains a prompt/agent
                </output>
            """,
            output={
                "schema": {
                    "contains_prompt": "boolean",
                    "prompt_type": "string",
                    "prompt_lines": "string",
                    "prompt_segments": "list[string]",
                    "confidence": "integer",
                    "explanation": "string",
                }
            },
            optimize=True,
        ),
    ]

    steps = [
        PipelineStep(
            name="function_analysis",
            input="functions",
            operations=["identify_prompt_functions"],
        ),
    ]

    return Pipeline(
        name="prompt-finder-pipeline",
        operations=operations,
        steps=steps,
        **kwargs,
    )


def build_rule_locator_pipeline(**kwargs) -> Pipeline:
    """
    Build a pipeline for locating where rules should be placed in prompts.

    Args:
        **kwargs: Additional arguments to pass to the Pipeline constructor

    Returns:
        Pipeline: A configured pipeline instance
    """
    operations = [
        MapOp(
            name="locate_rule_placement",
            type="map",
            prompt="""
                <instructions>
                    You are an expert in analyzing LLM prompts. Your task is to determine 
                    where to insert specific rules into existing prompts.
                    
                    You will be given:
                    1. A rule that needs to be added to prompts (as an exact string)
                    2. Information about multiple functions that contain prompts/agents
                    
                    For this rule, determine which prompt(s) it should be added to.
                    A good match is one where:
                    - The rule enhances the prompt's purpose
                    - The rule is relevant to the prompt's context
                    - The rule complements the existing instructions
                    
                    IMPORTANT: You are NOT being asked to apply or implement the rule by
                    rewriting the prompt. Your task is to identify the EXACT CODE SECTION where
                    the rule should be added.
                    
                    For each suitable prompt, determine:
                    1. The specific code section (could be multiple lines of code) where the rule belongs
                    2. Why this code section is the appropriate place for the rule
                    3. The confidence level (0-100%) that adding this rule will improve results
                    
                    The code section should be a direct copy of the relevant lines from the source code,
                    such as a specific part of a role definition, backstory, goal, or description.
                    
                    Only include placements that would meaningfully improve the system.
                </instructions>
                
                <rule>
                    {{input.rule_type}}: {{input.rule_text}}
                </rule>
                
                <prompt_functions>
                    {% for function in input.prompt_functions %}
                    <function id="{{loop.index}}">
                        Name: {{function.name}}
                        File Path: {{function.file_path}}
                        Line Range: {{function.line_start}}-{{function.line_end}}
                        Prompt Type: {{function.prompt_type}}
                        Prompt Lines: {{function.prompt_lines}}
                        
                        Source Code:
                        {{function.source_code}}
                        
                        {% if function.docstring %}
                        Docstring:
                        {{function.docstring}}
                        {% endif %}
                        
                        Prompt Segments:
                        {% for segment in function.prompt_segments %}
                        ---
                        {{segment}}
                        ---
                        {% endfor %}
                    </function>
                    {% endfor %}
                </prompt_functions>
                
                <output>
                    Respond **only** with a JSON object matching this exact schema (no extra keys!):
                    
                    placements: list[{function_id: int, function_name: str, file_path: str, target_code_section: str, confidence: float, reasoning: str}]
                    
                    So your entire output should look like:
                    
                    ```json
                    {
                      "placements": [
                        {
                          "function_id": 1,
                          "function_name": "example_function",
                          "file_path": "src/foo.py",
                          "target_code_section": "…exact lines…",
                          "confidence": 92.5,
                          "reasoning": "This rule fits here because…"
                        },
                        …
                      ]
                    }
                </output>
            """,
            output={
                "schema": {
                    "placements": "list[{function_id: int, function_name: str, file_path: str, target_code_section: str, confidence: float, reasoning: str}]"
                }
            },
            optimize=True,
        ),
    ]

    steps = [
        PipelineStep(
            name="rule_placement",
            input="rules_with_prompt_functions",
            operations=["locate_rule_placement"],
        ),
    ]

    return Pipeline(
        name="rule-locator-pipeline",
        operations=operations,
        steps=steps,
        **kwargs,
    )


def find_prompt_functions(functions, model="gpt-4o"):
    """
    Identify functions that contain prompts or define agents.

    Args:
        functions: List of FunctionInfo objects
        model: The model to use for the analysis

    Returns:
        list: List of functions that contain prompts, with detailed analysis
    """
    # Format functions data
    functions_data = [
        {
            "name": function.name,
            "file_path": function.file_path,
            "line_start": function.line_start,
            "line_end": function.line_end,
            "signature": function.signature,
            "source_code": function.source_code,
            "docstring": function.docstring,
        }
        for function in functions
    ]

    if not functions_data:
        return []

    # Write functions to a temp JSON file
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as inf:
            json.dump(functions_data, inf)
            in_path = inf.name

        # Reserve a temp file for the pipeline output
        out_fd, out_path = tempfile.mkstemp(suffix=".json")
        os.close(out_fd)

        try:
            datasets = {
                "functions": Dataset(
                    type="file",
                    path=in_path,
                )
            }
            pipeline = build_prompt_finder_pipeline(
                datasets=datasets,
                output=PipelineOutput(type="file", path=out_path),
                default_model=model,
            )
            pipeline.run()

            # Read back the results
            with open(out_path) as f:
                all_functions = json.load(f)

            # Filter to only functions that contain prompts with high confidence
            prompt_functions = [
                f
                for f in all_functions
                if f.get("contains_prompt", False) and f.get("confidence", 0) >= 70
            ]

            # Add the original source code and other details back to the results
            for pf in prompt_functions:
                for f in functions_data:
                    if f["name"] == pf["name"] and f["file_path"] == pf["file_path"]:
                        pf.update(f)
                        break

            return prompt_functions

        finally:
            # Clean up temp files
            if os.path.exists(in_path):
                os.remove(in_path)
            if os.path.exists(out_path):
                os.remove(out_path)
    except Exception as e:
        print(f"Error in find_prompt_functions: {str(e)}")
        return []


def locate_rules(rules, prompt_functions, model="gpt-4o"):
    """
    Locate which prompts should be updated with which rules.

    Args:
        rules: Dictionary containing 'always', 'never', and 'tips' rules
        prompt_functions: List of functions that contain prompts (from find_prompt_functions)
        model: The model to use for the analysis

    Returns:
        list: List of rule placement recommendations
    """
    if not prompt_functions:
        print("No functions with prompts found")
        return []

    # Prepare data for pipeline - one entry per rule
    rules_with_prompt_functions = []

    # Process each type of rule
    for rule in rules:
        for rule_type in ["always", "never", "tips"]:
            for rule_text in rule.get(rule_type, []):
                # Create entry with the rule and all prompt functions
                rules_with_prompt_functions.append(
                    {
                        "rule_type": rule_type,
                        "rule_text": rule_text,
                        "prompt_functions": prompt_functions,
                    }
                )

    if not rules_with_prompt_functions:
        return []

    # Write rule data to a temp JSON file
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as inf:
            json.dump(rules_with_prompt_functions, inf)
            in_path = inf.name

        # Reserve a temp file for the pipeline output
        out_fd, out_path = tempfile.mkstemp(suffix=".json")
        os.close(out_fd)

        try:
            datasets = {
                "rules_with_prompt_functions": Dataset(
                    type="file",
                    path=in_path,
                )
            }
            pipeline = build_rule_locator_pipeline(
                datasets=datasets,
                output=PipelineOutput(type="file", path=out_path),
                default_model=model,
            )
            pipeline.run()

            # Read back the results
            with open(out_path) as f:
                results = json.load(f)

            # Flatten placements from all rules
            all_placements = []
            for result in results:
                placements = result.get("placements", [])
                for placement in placements:
                    placement["rule_type"] = result.get("rule_type")
                    placement["rule_text"] = result.get("rule_text")
                all_placements.extend(placements)

            return all_placements

        finally:
            # Clean up temp files
            if os.path.exists(in_path):
                os.remove(in_path)
            if os.path.exists(out_path):
                os.remove(out_path)
    except Exception as e:
        print(f"Error in locate_rules: {str(e)}")
        return []


def save_rule_placements(placements):
    """
    Save rule placement recommendations to the database.

    Args:
        placements: List of rule placement recommendations
    """
    from aiai.app.models import DiscoveredRule

    for placement in placements:
        # Only process high confidence placements
        if placement.get("confidence", 0) >= 70:
            # Create or update rule record
            rule_text = f"{placement.get('rule_type', 'rule')}: {placement.get('rule_text', '')}"
            prompt_info = f"For {placement.get('function_name')} - {placement.get('section_to_update')}"

            # Get or create the rule
            rule, created = DiscoveredRule.objects.get_or_create(
                rule_text=rule_text,
                defaults={"confidence": placement.get("confidence", 0)},
            )

            # Update confidence if not created
            if not created and placement.get("confidence", 0) > rule.confidence:
                rule.confidence = placement.get("confidence", 0)
                rule.save()


def main():
    setup_django()
    from aiai.app.models import FunctionInfo
    from aiai.optimizer.rule_extractor import extract_rules

    # Get all functions from the database
    functions = FunctionInfo.objects.all()

    # Step 1: Identify functions that contain prompts
    print("Identifying functions with prompts...")
    prompt_functions = find_prompt_functions(functions)
    print(f"Found {len(prompt_functions)} functions with prompts")

    # Get rules
    from aiai.app.models import OtelSpan

    logs = OtelSpan.objects.all()
    rules = extract_rules(logs)

    # Step 2: For each rule, determine which prompt it should be placed in
    print("Locating optimal rule placements...")
    placements = locate_rules(rules, prompt_functions)
    return placements


if __name__ == "__main__":
    placements = main()
    from aiai.app.models import DiscoveredRule

    objects = [
        DiscoveredRule(
            rule_type=p.get("rule_type", ""),
            rule_text=p.get("rule_text", ""),
            function_name=p.get("function_name", ""),
            file_path=p.get("file_path", ""),
            target_code_section=p.get("target_code_section", ""),
            confidence=p.get("confidence", 0),
        )
        for p in placements
    ]
    DiscoveredRule.objects.bulk_create(objects)
