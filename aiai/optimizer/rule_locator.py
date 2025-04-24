import json
import os
import tempfile
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
        Locate which prompts should be updated with which rules.

        Args:
            rules: Dictionary containing 'always', 'never', and 'tips' rules
            prompt_sources: List of sources (functions and data files) that contain prompts
            model: The model to use for the analysis

        Returns:
            list: List of rule placement recommendations
        """
        if not prompt_functions and not prompt_data_files:
            print("No sources with prompts found")
            return []

        # Prepare data for pipeline - one entry per rule

        lm = instructor.from_litellm(litellm.completion)

        modifications = lm.create(
            model=self.model,
            response_model=list[CodeModification],
            max_retries=3,
            messages=[
                {
                    "role": "system",
                    "content": dedent(
                        """\
                        You are an expert in analyzing LLM prompts. Your task is to determine
                        where to insert specific rules into existing prompts.

                        You will be given:
                        1. Source code with function and data file IDs
                        2. Rules ("always"/"never") and tips that need to be added to the functions

                        You need to determine which function(s) and data file(s) should
                        be modified to add the rules/tips.

                        A good match is one where:
                        - The rule enhances the prompt's purpose
                        - The rule is relevant to the prompt's context
                        - The rule complements the existing instructions

                        IMPORTANT: You are NOT being asked to apply or implement the rule/tips by
                        rewriting the prompt. Your task is to map the rules/tips to the prompt that
                        should be modified.

                        Ensure that all rules/tips are mapped to a prompt.

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

                        Here are the rules and tips to add:

                        <rules_and_tips>
                        {json.dumps(self.rules)}
                        </rules_and_tips>
                        """
                    ),
                },
            ],
        )
        return modifications

    def perform(self):
        setup_django()
        from aiai.app.models import DataFileInfo, FunctionInfo

        prompt_functions = self._find_prompt_functions(FunctionInfo.objects.all())
        prompt_data_files = self._find_prompt_data_files(DataFileInfo.objects.all())

        # prompt_sources = prompt_functions + formatted_data_files

        print("Locating optimal modifications...")
        raw_code_mods = self._locate_rules(prompt_functions, prompt_data_files)

        code_mods: list[dict] = []
        for mod in raw_code_mods:
            if mod.function_id:
                code_mods.append(
                    {
                        "target_type": "function",
                        "target": next(f for f in prompt_functions if f["id"] == mod.function_id),
                        "mods": mod.model_dump(include=["always", "never", "tips"]),
                    }
                )
            elif mod.data_file_id:
                code_mods.append(
                    {
                        "target_type": "data_file",
                        "target": next(f for f in prompt_data_files if f["id"] == mod.data_file_id),
                        "mods": mod.model_dump(include=["always", "never", "tips"]),
                    }
                )
        return code_mods


if __name__ == "__main__":
    setup_django()

    from aiai.app.models import OtelSpan
    from aiai.optimizer.rule_extractor import generate_rules_and_tips

    logs = OtelSpan.objects.all()
    rules = generate_rules_and_tips(logs)

    placements = RuleLocator(rules).perform()
