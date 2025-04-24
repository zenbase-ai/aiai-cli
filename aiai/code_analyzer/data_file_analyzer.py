"""
DataFileAnalyzer class for analyzing JSON/YAML files in a codebase.

This module determines whether data files are related to LLM operations,
their purpose, and categorizes them accordingly.
"""

import json
import logging
import os
import tempfile
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import yaml

if TYPE_CHECKING:
    from aiai.app.models import DataFileInfo

logger = logging.getLogger(__name__)


class DataFileAnalyzer:
    """
    Analyzes JSON/YAML files to determine their purpose in the codebase.
    Identifies files containing prompts, configuration, or data for LLMs.
    """

    def __init__(self, model="openai/o4-mini"):
        """Initialize with specified LLM model."""
        self.model = model

    def analyze(
        self, file_path: Optional[str] = None, return_results: bool = False
    ) -> Union[int, Dict[str, Any], List[Dict[str, Any]]]:
        from aiai.app.models import DataFileInfo

        """
        Analyze data files in the codebase using the docetl pipeline.

        Args:
            file_path: Optional path to analyze a specific file. If None, analyzes all unanalyzed files.
            return_results: If True, returns analysis results instead of count. For a specific file,
                            returns a single result dict. For all files, returns a list of results.

        Returns:
            If return_results=False: Number of files analyzed
            If return_results=True and file_path provided: Analysis results dict for that file
            If return_results=True and file_path=None: List of analysis results for all files
        """
        # Case 1: Analyze a specific file
        if file_path:
            logger.info(f"Analyzing specific file: {file_path}")
            try:
                # Get the file from database or return None
                try:
                    data_file = DataFileInfo.objects.get(file_path=file_path)
                except DataFileInfo.DoesNotExist:
                    logger.error(f"File not found: {file_path}")
                    return {} if return_results else 0

                # Prepare file data
                file_data = self._prepare_file_data(data_file)
                if not file_data:
                    return {} if return_results else 0

                # Run docetl pipeline
                try:
                    results = self._run_pipeline([file_data])
                    if results and len(results) > 0:
                        result = results[0]
                        self._save_analysis(data_file, result)
                        logger.info(f"Successfully analyzed {file_path}")
                        return result if return_results else 1
                    logger.warning(f"No results from pipeline for {file_path}")
                    return {} if return_results else 0
                except Exception as e:
                    logger.error(f"Pipeline error analyzing {file_path}: {str(e)}")
                    return {} if return_results else 0

            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {str(e)}")
                return {} if return_results else 0

        # Case 2: Analyze all unanalyzed files
        else:
            # Get files that need analysis
            data_files = DataFileInfo.objects.filter(analysis__isnull=True)

            if not data_files:
                logger.info("No files to analyze")
                return [] if return_results else 0

            logger.info(f"Found {len(data_files)} files to analyze")

            # Prepare all file data
            all_file_data = []
            file_data_map = {}  # Maps file_path to data_file object

            for data_file in data_files:
                try:
                    file_data = self._prepare_file_data(data_file)
                    if file_data:
                        all_file_data.append(file_data)
                        file_data_map[file_data["file_path"]] = data_file
                except Exception as e:
                    logger.error(f"Error preparing data for {data_file.file_path}: {str(e)}")

            if not all_file_data:
                logger.warning("No valid files to analyze after preparation")
                return [] if return_results else 0

            # Process all files with docetl
            try:
                # Process files in a single batch
                results = self._run_pipeline(all_file_data)

                analyzed_count = 0
                saved_results = []

                # Map results back to data files
                for i, result in enumerate(results):
                    if i < len(all_file_data):
                        file_data = all_file_data[i]
                        if file_data["file_path"] in file_data_map:
                            data_file = file_data_map[file_data["file_path"]]
                            self._save_analysis(data_file, result)
                            analyzed_count += 1
                            saved_results.append(result)
                            logger.info(f"Analyzed {data_file.file_path}")

                logger.info(f"Completed analysis of {analyzed_count} files")
                return saved_results if return_results else analyzed_count

            except Exception as e:
                logger.error(f"Error in batch analysis: {str(e)}")
                return [] if return_results else 0

    def _run_pipeline(self, file_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run the docetl pipeline on the provided file data.

        Args:
            file_data_list: List of prepared file data dictionaries

        Returns:
            List of analysis results
        """
        try:
            # Import docetl
            from docetl.api import Dataset, MapOp, Pipeline, PipelineOutput, PipelineStep

            # Create temp files for pipeline I/O
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as inf:
                json.dump(file_data_list, inf)
                in_path = inf.name

            out_fd, out_path = tempfile.mkstemp(suffix=".json")
            os.close(out_fd)

            # Create intermediate directory if needed
            temp_dir = os.path.dirname(out_path)

            try:
                # Create analysis operation
                analyze_op = MapOp(
                    name="analyze_file",
                    type="map",
                    prompt=self._get_file_analysis_prompt(),
                    output={
                        "schema": {
                            "is_valid_reference": "bool",
                            "file_purpose": "string",
                            "content_category": "string",
                            "confidence_score": "float",
                        }
                    },
                )

                # Define steps
                steps = [PipelineStep(name="analyze_files", input="input", operations=["analyze_file"])]

                # Define datasets
                datasets = {"input": Dataset(type="file", path=in_path, source="local")}

                # Create output
                output = PipelineOutput(type="file", path=out_path, intermediate_dir=temp_dir)

                # Create the pipeline
                pipeline = Pipeline(
                    name="data_file_analyzer",
                    datasets=datasets,
                    operations=[analyze_op],
                    steps=steps,
                    output=output,
                    default_model=self.model,
                )

                # Run the pipeline
                pipeline.run()

                # Process results
                with open(out_path) as f:
                    results = json.load(f)

                if not results:
                    logger.warning("Empty results from pipeline")
                    results = []

                # Ensure we have results for all files
                if len(results) < len(file_data_list):
                    logger.warning(f"Expected {len(file_data_list)} results, got {len(results)}")
                    # Pad with default values if needed
                    for _ in range(len(file_data_list) - len(results)):
                        results.append(
                            {
                                "is_valid_reference": False,
                                "file_purpose": "Unknown purpose",
                                "content_category": "unknown",
                                "confidence_score": 0.0,
                            }
                        )

                return results

            finally:
                # Clean up temp files
                for path in [in_path, out_path]:
                    if os.path.exists(path):
                        os.remove(path)

        except ImportError:
            logger.error("docetl is not available")
            # Return default results if docetl is not available
            return [
                {
                    "is_valid_reference": False,
                    "file_purpose": "Could not analyze (docetl not available)",
                    "content_category": "unknown",
                    "confidence_score": 0.0,
                }
                for _ in file_data_list
            ]

        except Exception as e:
            logger.error(f"Error running docetl pipeline: {str(e)}")
            # Return default results on pipeline error
            return [
                {
                    "is_valid_reference": False,
                    "file_purpose": f"Could not analyze (pipeline error: {str(e)})",
                    "content_category": "unknown",
                    "confidence_score": 0.0,
                }
                for _ in file_data_list
            ]

    def _prepare_file_data(self, data_file: "DataFileInfo") -> Optional[Dict[str, Any]]:
        """Prepare file data for analysis."""
        if not data_file.content:
            logger.warning(f"No content available for {data_file.file_path}")
            return None

        try:
            # Parse file content
            if data_file.file_type == "json":
                content = json.loads(data_file.content)
                formatted_content = json.dumps(content, indent=2)
            elif data_file.file_type in ["yaml", "yml"]:
                content = yaml.safe_load(data_file.content)
                formatted_content = yaml.dump(content, default_flow_style=False)
            else:
                logger.warning(f"Unsupported file type: {data_file.file_type}")
                return None

            # Format references
            references = data_file.reference_contexts or []
            formatted_references = self._format_references(references)

            return {
                "file_path": data_file.file_path,
                "file_type": data_file.file_type,
                "content": content,
                "formatted_content": formatted_content,
                "references": references,
                "formatted_references": formatted_references,
                "basename": os.path.basename(data_file.file_path),
            }
        except Exception as e:
            logger.error(f"Error preparing data for {data_file.file_path}: {str(e)}")
            return None

    def _format_references(self, references: List[Dict[str, Any]]) -> str:
        """Format references for the LLM prompt."""
        if not references:
            return "No references found in code."

        formatted = []
        for i, ref in enumerate(references, 1):
            func_name = ref.get("function_name", "Unknown function")
            func_path = ref.get("function_path", "Unknown path")
            line = ref.get("line", 0)
            content = ref.get("content", "")

            formatted.append(f"Reference {i}:")
            formatted.append(f"- Function: {func_name} ({func_path}, line {line})")
            formatted.append(f"- Content: {content}")
            formatted.append("")

        return "\n".join(formatted)

    def _get_file_analysis_prompt(self):
        """Get the prompt for file analysis."""
        return dedent("""\
        <instructions>
            You are analyzing a file to determine its purpose in relation to LLM (Large Language Model) operations.
            Your task is to categorize the file and explain its purpose based on its content and code references.

            For categorization, use these criteria:

            1. PROMPT files:
               - Contains templates, system messages, or user/assistant exchanges
               - May have fields like "prompt", "system", "user", "assistant", "messages", "template"
               - Used to guide LLM interactions or define conversation structure

            2. CONFIGURATION files:
               - Contains settings, parameters, or options for LLM or application behavior
               - May include fields like "model", "temperature", "max_tokens", "settings", "config"
               - Used to control behavior of LLMs or related systems

            3. DATA files:
               - Contains structured information used by the application
               - May include lists, records, entries, items, or any domain-specific information
               - Often has array/list structures with multiple objects or records
               - Common fields include: "items", "entries", "data", "records", "id", "name"
               - Used to store and retrieve information for application logic
               - If the file contains entries, records, or listings and doesn't match the prompt or
                 configuration criteria, it's most likely a DATA file
               - IMPORTANT: Files containing collections of items, entities, or records should be
                 classified as DATA files even if they don't have code references

            4. OTHER files:
               - Files that are LLM-related but don't fit the above categories

            IMPORTANT: DEFAULT TO "data" CATEGORY IF THE FILE:
             - Contains array/collection of items/records/entries
             - Has "id" and "name" fields or other typical entity identifiers
             - Appears to be storing application data rather than configuration or prompts
        </instructions>

        <file>
            Path: {{input.file_path}}

            Content:
            ```{{input.file_type}}
            {{input.formatted_content}}
            ```

            Code References:
            {{input.formatted_references}}
        </file>

        <o>
            is_valid_reference: Is this file related to LLM operations or application data? (true if either)
            file_purpose: Detailed description of what this file is used for.
            content_category: One of "prompt", "configuration", "data", or "other".
            confidence_score: Your confidence in this assessment (0.0 to 1.0).
        </o>
        """)

    def _save_analysis(self, data_file: "DataFileInfo", results: Dict[str, Any]) -> None:
        from aiai.app.models import DataFileAnalysis

        """Save analysis results to database."""
        DataFileAnalysis.objects.update_or_create(
            data_file=data_file,
            defaults={
                "is_valid_reference": results.get("is_valid_reference", False),
                "file_purpose": results.get("file_purpose", ""),
                "content_category": results.get("content_category", "unknown"),
                "confidence_score": results.get("confidence_score", 0.0),
            },
        )
