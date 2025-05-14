import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import instructor
import litellm
from docetl.api import Dataset, MapOp, Pipeline, PipelineOutput, PipelineStep
from pydantic import BaseModel, Field, model_validator

from aiai.utils import setup_django

if TYPE_CHECKING:
    from aiai.app.models import FunctionInfo

cwd = Path(__file__).parent


class CodeModification(BaseModel):
    """
    A code modification to be made to a function, selecting the relevant always, never, and tips.
    """

    function_id: int | None = Field(description="The ID of the function to modify")
    data_file_id: int | None = Field(description="The ID of the data file to modify")
    always: list[str] = Field(description="The always rules to add")
    never: list[str] = Field(description="The never rules to add")
    tips: list[str] = Field(description="The tips to add")

    @model_validator(mode="after")
    def validate_function_or_data_file(self):
        if self.function_id is None and self.data_file_id is None:
            raise ValueError("Either function_id or data_file_id must be provided")
        return self


@dataclass
class RuleLocator:
    rules: dict
    model: str = "openai/o4-mini"
    max_workers = 8

    def _add_line_numbers(self, source_code: str, line_start: int) -> str:
        """
        Add line numbers to the source code.
        """
        return "\n".join(f"{i + line_start}. {line}" for i, line in enumerate(source_code.splitlines()))

    def _build_prompt_finder_pipeline(self, **kwargs) -> Pipeline:
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
                        - Template strings with placeholders
                        ({% raw %}{{variable}}{% endraw %}, {% raw %}{variable}{% endraw %}, etc.)
                        - Variables/objects named "prompt", "template", "system_message", etc.
                        - Agent definitions or configurations
                        - LLM API calls with prompt content
                    </instructions>

                    <function>
                        Name: {{input.name}}
                        File Path: {{input.file_path}}
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
                        prompt_type: What type of prompt/agent is used?
                            (e.g., "instruction_prompt", "agent_definition", "chain_of_thought", etc.)
                        prompt_lines: The line numbers where the prompt is defined (e.g., "15-25")
                        prompt_segments: A list of the specific prompt segments in the function
                        explanation: Brief explanation of why you believe this function contains a prompt/agent
                        confidence: A percentage (0-100) indicating your confidence in this analysis
                    </output>
                """,
                output={
                    "schema": {
                        "contains_prompt": "boolean",
                        "prompt_type": "string",
                        "prompt_lines": "string",
                        "prompt_segments": "list[string]",
                        "explanation": "string",
                        "confidence": "integer",
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

    def _build_datafile_prompt_finder_pipeline(self, **kwargs) -> Pipeline:
        """
        Build a pipeline for identifying prompts in JSON and YAML data files.

        Args:
            **kwargs: Additional arguments to pass to the Pipeline constructor

        Returns:
            Pipeline: A configured pipeline instance
        """
        operations = [
            MapOp(
                name="identify_data_file_prompts",
                type="map",
                prompt="""
                    <instructions>
                        You are an expert in code and data analysis. Your task is to identify
                        LLM prompts or agent definitions within JSON or YAML data files.

                        You will be given the content of a data file. Analyze it to determine if it contains:
                        1. Prompt templates (strings with placeholders for LLM calls)
                        2. Agent definitions or configurations
                        3. System messages, user messages, or other LLM-related content

                        Look for:
                        - String literals with XML/HTML-like tags (<instructions>, <o>, etc.)
                        - Template strings with placeholders
                        ({% raw %}{{variable}}{% endraw %}, {% raw %}{variable}{% endraw %}, etc.)
                        - Keys like "prompt", "template", "system_message", "user_message", etc.
                        - Agent definitions or configurations
                    </instructions>

                    <data_file>
                        File Path: {{input.file_path}}
                        File Type: {{input.file_type}}
                        Content:
                        {{input.content}}
                    </data_file>

                    <output>
                        contains_prompt: Does this file contain prompts or agent definitions? (true/false)
                        prompt_type: What type of prompt/agent is defined?
                            (e.g., "instruction_prompt", "agent_definition", "chain_of_thought", etc.)
                        prompt_segments: A list of the specific prompt segments in the file
                        explanation: Brief explanation of why you believe this file contains prompts/agents
                        confidence: A percentage (0-100) indicating your confidence in this analysis
                    </output>
                """,
                output={
                    "schema": {
                        "contains_prompt": "boolean",
                        "prompt_type": "string",
                        "prompt_segments": "list[string]",
                        "explanation": "string",
                        "confidence": "integer",
                    }
                },
                optimize=True,
            ),
        ]

        steps = [
            PipelineStep(
                name="data_file_analysis",
                input="data_files",
                operations=["identify_data_file_prompts"],
            ),
        ]

        return Pipeline(
            name="data-file-prompt-finder-pipeline",
            operations=operations,
            steps=steps,
            **kwargs,
        )

    def _find_prompt_functions(self, functions: list["FunctionInfo"]) -> list[dict]:
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
                "id": function.id,
                "name": function.name,
                "file_path": function.file_path,
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
                pipeline = self._build_prompt_finder_pipeline(
                    datasets=datasets,
                    output=PipelineOutput(type="file", path=out_path),
                    default_model=self.model,
                )
                pipeline.run()

                # Read back the results
                with open(out_path) as f:
                    all_functions = json.load(f)

                # Filter to only functions that contain prompts with high confidence
                prompt_functions = [
                    f for f in all_functions if f.get("contains_prompt", False) and f.get("confidence", 0) >= 70
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

    def _find_prompt_data_files(self, data_files):
        """
        Identify JSON and YAML files that contain prompts or agent definitions.

        Args:
            data_files: List of DataFileInfo objects
            model: The model to use for the analysis

        Returns:
            list: List of data files that contain prompts, with detailed analysis
        """
        # Format data files
        data_files_data = [
            {
                "id": data_file.id,
                "file_path": data_file.file_path,
                "file_type": data_file.file_type,
                "content": data_file.content,
            }
            for data_file in data_files
        ]

        if not data_files_data:
            return []

        # Write data files to a temp JSON file
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as inf:
                json.dump(data_files_data, inf)
                in_path = inf.name

            # Reserve a temp file for the pipeline output
            out_fd, out_path = tempfile.mkstemp(suffix=".json")
            os.close(out_fd)

            try:
                datasets = {
                    "data_files": Dataset(
                        type="file",
                        path=in_path,
                    )
                }
                pipeline = self._build_datafile_prompt_finder_pipeline(
                    datasets=datasets,
                    output=PipelineOutput(type="file", path=out_path),
                    default_model=self.model,
                )
                pipeline.run()

                # Read back the results
                with open(out_path) as f:
                    all_data_files = json.load(f)

                # Filter to only data files that contain prompts with high confidence
                prompt_data_files = [
                    f for f in all_data_files if f.get("contains_prompt", False) and f.get("confidence", 0) >= 70
                ]

                # Add the original content and other details back to the results
                for pdf in prompt_data_files:
                    for df in data_files_data:
                        if df["file_path"] == pdf["file_path"]:
                            pdf.update(df)
                            break

                formatted_data_files = []
                for df in prompt_data_files:
                    formatted_data_file = {
                        "id": df["id"],
                        "name": f"data_file_{os.path.basename(df['file_path'])}",
                        "file_path": df["file_path"],
                        "signature": f"DataFile ({df['file_type']})",
                        "source_code": df["content"],
                        "docstring": "",
                        "prompt_type": df.get("prompt_type", ""),
                        "prompt_segments": df.get("prompt_segments", []),
                    }
                    formatted_data_files.append(formatted_data_file)

                return formatted_data_files

            finally:
                # Clean up temp files
                if os.path.exists(in_path):
                    os.remove(in_path)
                if os.path.exists(out_path):
                    os.remove(out_path)
        except Exception as e:
            print(f"Error in find_prompt_data_files: {str(e)}")
            return []

    def _locate_rules(self, prompt_functions: list[dict], prompt_data_files: list[dict]) -> list[CodeModification]:
        """
        Locate which prompts should be updated with which rules, matching each individual rule separately.

        Args:
            prompt_functions: List of functions that contain prompts
            prompt_data_files: List of data files that contain prompts

        Returns:
            list: List of rule placement recommendations, one for each individual rule
        """
        if not prompt_functions and not prompt_data_files:
            print("No sources with prompts found")
            return []

        # Extract individual rules
        individual_rules = []

        # Process always rules
        for rule in self.rules.get("always", []):
            individual_rules.append({"type": "always", "rule": rule["rule"], "reasoning": rule.get("reasoning", "")})

        # Process never rules
        for rule in self.rules.get("never", []):
            individual_rules.append({"type": "never", "rule": rule["rule"], "reasoning": rule.get("reasoning", "")})

        # Process tips
        for tip in self.rules.get("tips", []):
            individual_rules.append({"type": "tips", "rule": tip["rule"], "reasoning": tip.get("reasoning", "")})

        if not individual_rules:
            print("No rules to apply")
            return []

        lm = instructor.from_litellm(litellm.completion)

        # Use ThreadPool to process rules in parallel
        all_modifications = []

        def process_rule(rule_item):
            rule_type = rule_item["type"]
            rule = rule_item["rule"]
            reasoning = rule_item["reasoning"]

            # Ask the LLM to find the best placement for this specific rule
            return lm.create(
                model=self.model,
                response_model=list[CodeModification],
                max_retries=3,
                messages=[
                    {
                        "role": "system",
                        "content": dedent(
                            """\
                            You are an expert in analyzing LLM prompts. Your task is to determine
                            where to insert a specific rule into existing prompts.

                            You will be given:
                            1. Source code with function and data file IDs
                            2. A single rule ("always"/"never") or tip that needs to be added to a function or data file
                            3. The reasoning behind this rule, which explains why it's important

                            You need to determine which function(s) and data file(s) should
                            be modified to add this specific rule/tip.

                            A good match is one where:
                            - The rule enhances the prompt's purpose
                            - The rule is relevant to the prompt's context
                            - The rule complements the existing instructions
                            - The reasoning aligns with the function's purpose

                            IMPORTANT: You are NOT being asked to apply or implement the rule/tip by
                            rewriting the prompt. Your task is to map the rule/tip to the prompt that
                            should be modified.

                            Take a deep breath and think step by step.
                            """
                        ),
                    },
                    {
                        "role": "user",
                        "content": dedent(
                            f"""\
                            Here are the functions and their source code:

                            <functions>
                            {json.dumps(prompt_functions)}
                            </functions>

                            <data_files>
                            {json.dumps(prompt_data_files)}
                            </data_files>

                            Here is the specific rule to add:
                            
                            <rule>
                                <{rule_type}>
                                    {rule}
                                </{rule_type}>
                            </rule>

                            <reasoning>
                                {reasoning}
                            </reasoning>
                            """
                        ),
                    },
                ],
            )

        # Process rules in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_rule = {executor.submit(process_rule, rule_item): rule_item for rule_item in individual_rules}

            # Process results as they complete
            for future in as_completed(future_to_rule):
                try:
                    modifications = future.result()
                    all_modifications.extend(modifications)
                except Exception as exc:
                    rule_item = future_to_rule[future]
                    print(f"Processing rule '{rule_item['rule']}' generated an exception: {exc}")

        return all_modifications

    def _locate_precise_rule_positions(self, raw_code_mods: list[CodeModification]) -> list[dict]:
        """
        For each identified function or data file that needs a rule applied,
        determine precise location to insert the rule within the source code.

        Args:
            raw_code_mods: List of CodeModification objects identifying which functions/files
                          need individual rules applied

        Returns:
            list: Enhanced list of dictionaries with precise insertion points for each rule
        """
        from aiai.app.models import DataFileInfo, FunctionInfo

        lm = instructor.from_litellm(litellm.completion)

        # Function to process a single modification
        def process_modification(mod):
            try:
                # Fetch the full source code from the database
                if mod.function_id:
                    target_type = "function"
                    function = FunctionInfo.objects.get(id=mod.function_id)
                    # Add line numbers to the source code
                    source_code = self._add_line_numbers(function.source_code, function.line_start)
                    target_info = {
                        "id": function.id,
                        "name": function.name,
                        "file_path": function.file_path,
                        "signature": function.signature,
                        "docstring": function.docstring or "",
                    }
                else:  # data_file
                    target_type = "data_file"
                    data_file = DataFileInfo.objects.get(id=mod.data_file_id)
                    source_code = self._add_line_numbers(data_file.content, line_start=1)
                    target_info = {
                        "id": data_file.id,
                        "file_path": data_file.file_path,
                        "file_type": data_file.file_type,
                    }

                # Determine the rule type, content and reasoning from the original rules list
                rule_type = None
                rule_content = None
                rule_reasoning = ""

                if mod.always:
                    rule_type = "always"
                    rule_content = mod.always[0]  # Since we're handling individual rules

                    # Find the matching rule in original rules list to get the reasoning
                    for rule_item in self.rules.get("always", []):
                        if isinstance(rule_item, dict) and rule_item.get("rule") == rule_content:
                            rule_reasoning = rule_item.get("reasoning", "")
                            break

                elif mod.never:
                    rule_type = "never"
                    rule_content = mod.never[0]

                    # Find the matching rule in original rules list to get the reasoning
                    for rule_item in self.rules.get("never", []):
                        if isinstance(rule_item, dict) and rule_item.get("rule") == rule_content:
                            rule_reasoning = rule_item.get("reasoning", "")
                            break

                elif mod.tips:
                    rule_type = "tips"
                    rule_content = mod.tips[0]

                    # Find the matching rule in original rules list to get the reasoning
                    for rule_item in self.rules.get("tips", []):
                        if isinstance(rule_item, dict) and rule_item.get("rule") == rule_content:
                            rule_reasoning = rule_item.get("reasoning", "")
                            break

                if not rule_type or not rule_content:
                    return None  # Skip if no rule found

                # Define a structure to capture precise insertion points
                class PreciseModification(BaseModel):
                    position_description: str = Field(
                        description="Description of where to insert this rule (e.g., 'After the instructions tag')"
                    )
                    line_number: int | None = Field(
                        description="Approximate line number for insertion, if determinable", default=None
                    )
                    context_before: str = Field(description="A few words of text that come before the insertion point")
                    context_after: str = Field(description="A few words of text that come after the insertion point")

                # Ask the LLM for precise placement
                precise_mod = lm.create(
                    model=self.model,
                    response_model=PreciseModification,
                    max_retries=3,
                    messages=[
                        {
                            "role": "system",
                            "content": dedent(
                                """\
                                You are an expert in analyzing prompts in code. Your task is to determine 
                                PRECISELY where a specific rule should be inserted into a source code.
                                
                                You'll be given:
                                1. The source code
                                2. A single rule that needs to be added
                                3. The reasoning behind this rule, explaining why it's important
                                
                                You need to identify the EXACT position to insert this rule, such as:
                                - After an <instructions> tag
                                - Within a specific section of the prompt
                                - After other similar rules
                                
                                For the insertion point, provide:
                                - The context before and after the insertion point (a few words)
                                - A clear description of the position
                                - Approximately the line number
                                
                                Focus on finding the most natural and effective position where this rule 
                                would enhance the existing prompt without disrupting its structure.
                                Use the reasoning to understand the rule's purpose and find the most
                                contextually appropriate location.
                                """
                            ),
                        },
                        {
                            "role": "user",
                            "content": dedent(
                                f"""\
                                Here is the source code:
                                
                                <source_code>
                                {source_code}
                                </source_code>
                                
                                Here is the rule to add:
                                
                                <rule>
                                    <{rule_type}>
                                        {rule_content}
                                    </{rule_type}>
                                </rule>

                                <reasoning>
                                    {rule_reasoning}
                                </reasoning>

                                Please identify the precise position in the source code where this rule 
                                should be inserted.
                                """
                            ),
                        },
                    ],
                )

                # Build the enhanced modification
                return {
                    "target_type": target_type,
                    "target": target_info,
                    "rule_type": rule_type,
                    "rule_content": rule_content,
                    "rule_reasoning": rule_reasoning,
                    "precise_insertion_point": precise_mod.model_dump(),
                    "target_file_path": target_info["file_path"] + f":{precise_mod.line_number}",
                    "source_code": source_code,
                }
            except Exception as e:
                print(f"Error processing modification: {str(e)}")
                return None

        # Process all modifications in parallel
        precise_code_mods = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_mod = {executor.submit(process_modification, mod): mod for mod in raw_code_mods}

            # Process results as they complete
            for future in as_completed(future_to_mod):
                result = future.result()
                if result:
                    precise_code_mods.append(result)

        return precise_code_mods

    def perform(self):
        setup_django()
        from aiai.app.models import DataFileInfo, FunctionInfo

        prompt_functions = self._find_prompt_functions(FunctionInfo.objects.all())
        prompt_data_files = self._find_prompt_data_files(DataFileInfo.objects.all())

        # prompt_sources = prompt_functions + formatted_data_files

        print("Locating optimal modifications...")
        raw_code_mods = self._locate_rules(prompt_functions, prompt_data_files)

        print("Finding precise insertion points for rules...")
        code_mods = self._locate_precise_rule_positions(raw_code_mods)

        return code_mods


if __name__ == "__main__":
    setup_django()

    from aiai.app.models import OtelSpan
    from aiai.optimizer.rule_extractor import generate_rules_and_tips

    logs = OtelSpan.objects.all()
    rules = generate_rules_and_tips(logs)

    placements = RuleLocator(rules).perform()
