"""
DataFileAnalyzer class implementation.

This module analyzes data files (JSON/YAML) to determine their purpose
and relevance to the codebase, particularly for LLM-related data.
"""

import logging
from typing import Optional, Dict, List, Any
import json
import yaml

from aiai.app.models import DataFileInfo, DataFileAnalysis

logger = logging.getLogger(__name__)


class DataFileAnalyzer:
    """
    A service that analyzes data files using docetl pipeline.

    This analyzer determines if files are relevant to LLM operations,
    what purpose they serve, and their content category.
    """

    def __init__(self, docetl_pipeline=None):
        """
        Initialize the data file analyzer.

        Args:
            docetl_pipeline: Optional docetl pipeline to use for analysis
        """
        self.pipeline = docetl_pipeline or self._create_default_pipeline()

    def _create_default_pipeline(self):
        """
        Create a default pipeline if none is provided.

        Returns:
            A simple analysis pipeline
        """
        # This is a placeholder for the actual docetl pipeline implementation
        # In a real implementation, this would configure the docetl pipeline

        # For now, we'll return a dummy function that will be replaced later
        def simple_pipeline(data):
            """Simple placeholder until docetl is properly implemented"""
            return {
                "is_valid_reference": True,
                "content_category": "unknown",
                "file_purpose": "To be analyzed",
                "confidence_score": 0.5,
            }

        return simple_pipeline

    def analyze(self):
        """
        Analyze all data files that need analysis.

        This method:
        1. Fetches all DataFileInfo objects from the database
        2. For each file, determines if it's related to LLM operations
        3. Categorizes the file and determines its purpose
        4. Saves the results to the DataFileAnalysis model

        Returns:
            Number of files analyzed
        """
        # Get all data files that haven't been analyzed yet or need re-analysis
        data_files = self._get_files_for_analysis()
        logger.info(f"Found {len(data_files)} files to analyze")

        analyzed_count = 0
        for data_file in data_files:
            try:
                # Analyze the file
                analysis_result = self._analyze_file(data_file)

                if analysis_result:
                    # Save the analysis results
                    self._update_analysis_results(data_file, analysis_result)
                    analyzed_count += 1
                    logger.info(f"Successfully analyzed {data_file.file_path}")
                else:
                    logger.warning(f"Analysis failed for {data_file.file_path}")
            except Exception as e:
                logger.error(f"Error analyzing {data_file.file_path}: {str(e)}")

        logger.info(f"Completed analysis of {analyzed_count} files")
        return analyzed_count

    def _get_files_for_analysis(self) -> List[DataFileInfo]:
        """
        Get all files that need analysis.

        Returns:
            List of DataFileInfo objects that need analysis
        """
        # Fetch all data files that don't have an analysis yet
        return DataFileInfo.objects.filter(analysis__isnull=True)

    def _analyze_file(self, data_file: DataFileInfo) -> Optional[Dict[str, Any]]:
        """
        Analyze a single data file.

        Args:
            data_file: The DataFileInfo object to analyze

        Returns:
            Dictionary with analysis results or None if analysis failed
        """
        # Skip if no content
        if not data_file.content:
            logger.warning(f"No content available for {data_file.file_path}")
            return None

        # Parse the file content based on type
        try:
            if data_file.file_type == "json":
                content = json.loads(data_file.content)
            elif data_file.file_type in ("yaml", "yml"):
                content = yaml.safe_load(data_file.content)
            else:
                logger.warning(f"Unsupported file type: {data_file.file_type}")
                return None
        except Exception as e:
            logger.error(f"Error parsing {data_file.file_path}: {str(e)}")
            return None

        # Prepare the analysis data
        analysis_data = {
            "file_path": data_file.file_path,
            "file_type": data_file.file_type,
            "content": content,
            "references": data_file.reference_contexts or [],
        }

        # Run the analysis using the pipeline
        try:
            result = self.pipeline(analysis_data)
            return result
        except Exception as e:
            logger.error(f"Pipeline error for {data_file.file_path}: {str(e)}")
            return None

    def _update_analysis_results(
        self, data_file: DataFileInfo, results: Dict[str, Any]
    ) -> None:
        """
        Update the database with analysis results.

        Args:
            data_file: The DataFileInfo object that was analyzed
            results: The analysis results to save
        """
        # Create or update the analysis object
        DataFileAnalysis.objects.update_or_create(
            data_file=data_file,
            defaults={
                "is_valid_reference": results.get("is_valid_reference", False),
                "file_purpose": results.get("file_purpose", ""),
                "content_category": results.get("content_category", "unknown"),
                "confidence_score": results.get("confidence_score", 0.0),
            },
        )

    def get_prompt_files(self):
        """
        Get all files that have been identified as containing prompts.

        Returns:
            QuerySet of DataFileAnalysis objects for prompt files
        """
        return DataFileAnalysis.objects.filter(
            is_valid_reference=True, content_category="prompt"
        )

    def get_data_files(self):
        """
        Get all files that have been identified as containing data for LLMs.

        Returns:
            QuerySet of DataFileAnalysis objects for data files
        """
        return DataFileAnalysis.objects.filter(
            is_valid_reference=True, content_category="data"
        )
