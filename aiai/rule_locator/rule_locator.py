import json
import os
import tempfile
from pathlib import Path
import re

from docetl.api import (
    Dataset,
    MapOp,
    Pipeline,
    PipelineOutput,
    PipelineStep,
)
from utils import setup_django

cwd = Path(__file__).parent


def build_rule_locator_pipeline(**kwargs) -> Pipeline:
    """
    Build a pipeline for locating where rules should be placed in prompts.
    
    The pipeline has two steps:
    1. Identify functions that create agents or contain prompts
    2. For each rule, determine where and how to integrate it into those prompts
    
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
                    You are an expert in code analysis focusing on LLM applications. Your task is to identify 
                    functions that either create LLM agents or contain prompts for LLM calls.
                    
                    Analyze the provided function to determine if it:
                    1. Creates an AI agent or assistant
                    2. Contains a prompt used for LLM calls
                    3. Builds or configures a prompt template
                    
                    Look for indicators such as:
                    - String literals containing templating syntax (e.g., {{variable}})
                    - XML-like tags in strings (e.g., <instructions>, <output>)
                    - Function calls to LLM APIs (e.g., OpenAI, Anthropic)
                    - Agent or assistant creation/configuration
                    - Pipeline or prompt building
                    
                    If the function does contain a prompt or create an agent, identify:
                    - The specific location(s) of the prompt within the function
                    - The purpose of the prompt (what it's asking the LLM to do)
                    - Any specific sections where rules could be integrated (e.g., instructions, constraints)
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
                    contains_prompt: Whether this function contains a prompt or creates an agent (true/false)
                    prompt_locations: If contains_prompt is true, a list of prompt locations, each containing:
                      - line_start: The starting line number of the prompt
                      - line_end: The ending line number of the prompt
                      - prompt_type: The type of prompt (e.g., "instruction", "chat", "agent_config")
                      - prompt_purpose: A brief description of what the prompt is for
                      - integration_points: List of sections where rules could be integrated (e.g., "instructions", "constraints")
                    reasoning: Your reasoning for this determination
                </output>
            """,
            output={
                "schema": {
                    "contains_prompt": "boolean",
                    "prompt_locations": "list[object]",
                    "reasoning": "string",
                }
            },
            optimize=True,
        ),
        MapOp(
            name="place_rule_in_prompt",
            type="map",
            prompt="""
                <instructions>
                    You are an expert in improving LLM prompts by integrating rules. Your task is to determine 
                    how to integrate a specific rule into a function that contains prompts.
                    
                    You will be given:
                    1. A rule that needs to be integrated
                    2. Information about a function containing prompts
                    3. Analysis of where prompts are located in the function
                    
                    For each prompt location in the function, determine:
                    1. Is this rule relevant to this prompt?
                    2. If relevant, where in the prompt should the rule be integrated?
                    3. How should the rule be worded to fit with the existing prompt?
                    4. What is the confidence level (0-100%) that this integration will improve the prompt?
                    
                    Only make changes that would improve the prompt's effectiveness for its purpose.
                </instructions>
                
                <rule>
                    Type: {{input.rule_type}}
                    Text: {{input.rule_text}}
                </rule>
                
                <function>
                    Name: {{input.function_name}}
                    File Path: {{input.function_file_path}}
                    Line Range: {{input.function_line_start}}-{{input.function_line_end}}
                    Signature: {{input.function_signature}}
                    
                    Source Code:
                    {{input.function_source_code}}
                    
                    {% if input.function_docstring %}
                    Docstring:
                    {{input.function_docstring}}
                    {% endif %}
                </function>
                
                <prompt_analysis>
                    {% for location in input.prompt_locations %}
                    <prompt_location id="{{loop.index}}">
                        Line Range: {{location.line_start}}-{{location.line_end}}
                        Type: {{location.prompt_type}}
                        Purpose: {{location.prompt_purpose}}
                        Integration Points: {{location.integration_points|join(', ')}}
                    </prompt_location>
                    {% endfor %}
                </prompt_analysis>
                
                <output>
                    prompt_updates: A list of update objects, each containing:
                      - prompt_location_id: The ID of the prompt location (from the input prompt_analysis)
                      - line_start: The exact line where the update should start
                      - line_end: The exact line where the update should end
                      - section_to_update: The section being updated (e.g., "instructions", "validation")
                      - original_text: The exact text to be replaced or modified
                      - updated_text: The new text with the rule integrated
                      - integration_method: How to integrate (e.g., "append", "replace", "insert_after")
                      - confidence: A percentage (0-100) indicating your confidence in this update
                      - reasoning: Your reasoning for this update
                </output>
            """,
            output={
                "schema": {
                    "prompt_updates": "list[object]",
                }
            },
            optimize=True,
        ),
    ]

    steps = [
        PipelineStep(
            name="identify_prompts",
            input="functions",
            operations=["identify_prompt_functions"],
        ),
        PipelineStep(
            name="place_rules",
            input="rules_with_prompt_functions",
            operations=["place_rule_in_prompt"],
        ),
    ]

    return Pipeline(
        name="rule-locator-pipeline",
        operations=operations,
        steps=steps,
        **kwargs,
    )


def locate_rules(rules, functions, model="gpt-4o"):
    """
    Locate which prompts in functions should be updated with rules.
    
    Args:
        rules: Dictionary containing 'always', 'never', and 'tips' rules
        functions: List of FunctionInfo objects representing the codebase
        model: The model to use for the analysis
    
    Returns:
        list: List of prompt update recommendations
    """
    try:
        # Step 1: Identify functions with prompts
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
        
        # Write functions to a temp JSON file
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as inf:
            json.dump(functions_data, inf)
            functions_path = inf.name

        # Create temp file for the intermediate results
        prompt_functions_fd, prompt_functions_path = tempfile.mkstemp(suffix=".json")
        os.close(prompt_functions_fd)
        
        # Create temp file for the final results
        final_results_fd, final_results_path = tempfile.mkstemp(suffix=".json")
        os.close(final_results_fd)
        
        try:
            # Run step 1: Identify functions with prompts
            step1_datasets = {
                "functions": Dataset(
                    type="file",
                    path=functions_path,
                )
            }
            step1_pipeline = Pipeline(
                name="identify-prompts-pipeline",
                operations=[op for op in build_rule_locator_pipeline().operations if op.name == "identify_prompt_functions"],
                steps=[
                    PipelineStep(
                        name="identify_prompts",
                        input="functions",
                        operations=["identify_prompt_functions"],
                    ),
                ],
                datasets=step1_datasets,
                output=PipelineOutput(type="file", path=prompt_functions_path),
                default_model=model
            )
            step1_pipeline.run()
            
            # Read the prompt functions results
            with open(prompt_functions_path) as f:
                prompt_functions_results = json.load(f)
            
            # Filter to functions that contain prompts
            prompt_functions = [
                {**func_data, **result}
                for func_data, result in zip(functions_data, prompt_functions_results)
                if result.get("contains_prompt", False)
            ]
            
            if not prompt_functions:
                print("No functions containing prompts were found")
                return []
                
            print(f"Found {len(prompt_functions)} functions containing prompts")
            
            # Step 2: For each rule, check where to place it
            rules_with_functions = []
            
            # Process each type of rule
            for rule_type in ["always", "never", "tips"]:
                for rule_text in rules.get(rule_type, []):
                    # For each rule, pair it with every function that has prompts
                    for prompt_function in prompt_functions:
                        rules_with_functions.append({
                            "rule_type": rule_type,
                            "rule_text": rule_text,
                            "function_name": prompt_function["name"],
                            "function_file_path": prompt_function["file_path"],
                            "function_line_start": prompt_function["line_start"],
                            "function_line_end": prompt_function["line_end"],
                            "function_signature": prompt_function["signature"],
                            "function_source_code": prompt_function["source_code"],
                            "function_docstring": prompt_function.get("docstring", ""),
                            "prompt_locations": prompt_function.get("prompt_locations", []),
                        })
            
            if not rules_with_functions:
                return []
                
            # Write rule-function pairs to a temp JSON file
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as inf:
                json.dump(rules_with_functions, inf)
                rules_with_functions_path = inf.name
                
            # Run step 2: Place rules in prompts
            step2_datasets = {
                "rules_with_prompt_functions": Dataset(
                    type="file",
                    path=rules_with_functions_path,
                )
            }
            step2_pipeline = Pipeline(
                name="place-rules-pipeline",
                operations=[op for op in build_rule_locator_pipeline().operations if op.name == "place_rule_in_prompt"],
                steps=[
                    PipelineStep(
                        name="place_rules",
                        input="rules_with_prompt_functions",
                        operations=["place_rule_in_prompt"],
                    ),
                ],
                datasets=step2_datasets,
                output=PipelineOutput(type="file", path=final_results_path),
                default_model=model
            )
            step2_pipeline.run()
            
            # Read the final results
            with open(final_results_path) as f:
                rule_placement_results = json.load(f)
                
            # Flatten updates from all rules
            all_updates = []
            for idx, result in enumerate(rule_placement_results):
                rule_info = rules_with_functions[idx]
                updates = result.get("prompt_updates", [])
                # Add rule and function info to each update
                for update in updates:
                    update["rule_type"] = rule_info["rule_type"]
                    update["rule_text"] = rule_info["rule_text"]
                    update["function_name"] = rule_info["function_name"]
                    update["file_path"] = rule_info["function_file_path"]
                all_updates.extend(updates)
            
            return all_updates
            
        finally:
            # Clean up temp files
            for path in [functions_path, prompt_functions_path, final_results_path]:
                if os.path.exists(path):
                    os.remove(path)
                    
            # Clean up any extra temp files that may have been created
            if 'rules_with_functions_path' in locals() and os.path.exists(rules_with_functions_path):
                os.remove(rules_with_functions_path)
                
    except Exception as e:
        print(f"Error in locate_rules: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def save_prompt_updates(updates):
    """
    Save prompt update recommendations to the database.
    
    Args:
        updates: List of prompt update recommendations
    """
    from aiai.app.models import DiscoveredRule
    
    for update in updates:
        # Only process high confidence updates
        if update.get("confidence", 0) >= 70:
            # Create or update rule record
            rule_text = f"{update.get('rule_type', 'rule')}: {update.get('rule_text', '')}"
            prompt_info = f"For {update.get('function_name')} - {update.get('section_to_update')}"
            
            # Get or create the rule
            rule, created = DiscoveredRule.objects.get_or_create(
                rule_text=rule_text,
                defaults={"confidence": update.get("confidence", 0)}
            )
            
            # Update confidence if not created
            if not created and update.get("confidence", 0) > rule.confidence:
                rule.confidence = update.get("confidence", 0)
                rule.save()


def apply_prompt_updates(updates, dry_run=True):
    """
    Apply the recommended prompt updates to the codebase.
    
    Args:
        updates: List of prompt update recommendations
        dry_run: If True, only print changes without applying them
    
    Returns:
        list: Summary of changes applied or that would be applied
    """
    changes_summary = []
    
    for update in updates:
        if update.get("confidence", 0) < 70:
            continue
            
        file_path = update.get("file_path")
        start_line = update.get("line_start")
        end_line = update.get("line_end")
        original = update.get("original_text")
        updated = update.get("updated_text")
        
        if not all([file_path, start_line, end_line, original, updated]):
            continue
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            # Convert to 0-indexed
            start_idx = start_line - 1
            end_idx = end_line - 1
            
            # Extract the code segment to update
            code_segment = ''.join(lines[start_idx:end_idx+1])
            
            # Check if original text is found
            if original not in code_segment:
                print(f"Warning: Original text not found in {file_path} lines {start_line}-{end_line}")
                continue
                
            # Replace the text
            new_segment = code_segment.replace(original, updated)
            
            # Create updated file content
            new_lines = lines[:start_idx] + [new_segment] + lines[end_idx+1:]
            
            change = {
                "file": file_path,
                "function": update.get("function_name"),
                "lines": f"{start_line}-{end_line}",
                "integration": update.get("integration_method"),
                "applied": not dry_run
            }
            changes_summary.append(change)
            
            if not dry_run:
                with open(file_path, 'w') as f:
                    f.writelines(new_lines)
                    
        except Exception as e:
            print(f"Error applying update to {file_path}: {str(e)}")
    
    return changes_summary


if __name__ == '__main__':
    setup_django()
    from aiai.app.models import DiscoveredRule, FunctionInfo
    from aiai.optimizer.rule_extractor import extract_rules
    
    # Get all functions from the database
    functions = FunctionInfo.objects.all()
    
    # Get rules (example: could also load from database if already extracted)
    from aiai.app.models import OtelSpan
    logs = OtelSpan.objects.all()
    rules = extract_rules(logs)
    
    # Locate prompts to update with rules
    updates = locate_rules(rules, functions)
    
    # Save prompt updates
    save_prompt_updates(updates)
    
    # Dry run of applying updates
    changes = apply_prompt_updates(updates, dry_run=True)
    
    # Print summary
    print(f"Found {len(updates)} relevant prompt updates")
    for u in updates:
        print(f"Rule: {u.get('rule_type')} - {u.get('rule_text')[:50]}...")
        print(f"Function: {u.get('function_name')} ({u.get('file_path')}:{u.get('line_start')}-{u.get('line_end')})")
        print(f"Update section: {u.get('section_to_update')} ({u.get('integration_method')})")
        print(f"Confidence: {u.get('confidence')}%")
        print("-" * 80) 