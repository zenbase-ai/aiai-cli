from datetime import datetime
from typing import Any

from django.db import models


class OtelSpan(models.Model):
    trace_id: str = models.TextField(null=False, blank=False)
    span_id: str = models.TextField(primary_key=True, db_index=True, null=False, blank=False)
    start_time: datetime = models.DateTimeField(null=False, blank=False)
    end_time: datetime = models.DateTimeField(null=False, blank=False)
    attributes: dict[str, Any] = models.JSONField(null=False, blank=False)
    prompt: str = models.TextField(null=False, blank=False)
    completion: str = models.TextField(null=False, blank=False)


class DiscoveredRule(models.Model):
    rule_type: str = models.TextField(default="")
    rule_text: str = models.TextField(default="")
    function_name: str = models.TextField(default="")
    file_path: str = models.TextField(default="")
    target_code_section: str = models.TextField(default="")


class SyntheticEval(models.Model):
    class Kinds(models.TextChoices):
        RULES = "rules"
        HEAD_TO_HEAD = "head_to_head"

    kind: str = models.CharField(max_length=20, choices=Kinds.choices)
    prompt: str = models.TextField(null=False, blank=False)
    fields: dict[str, Any] = models.JSONField(null=False, blank=False)

    def __str__(self) -> str:
        return f"{self.id} - {self.kind}"


class SyntheticDatum(models.Model):
    input_data = models.TextField(null=False, blank=False)


class EvalRun(models.Model):
    trace_id: str = models.TextField(null=False, blank=False)
    eval: SyntheticEval | None = models.ForeignKey(SyntheticEval, on_delete=models.CASCADE, null=True)
    input_data: str = models.TextField(null=False, blank=False)
    output_data: str = models.TextField(null=False, blank=False)
    reward: str = models.TextField(null=False, blank=True)


class FunctionInfo(models.Model):
    name: str = models.CharField(max_length=255)
    file_path: str = models.CharField(max_length=512)
    line_start: int = models.IntegerField()
    line_end: int = models.IntegerField()
    signature: str = models.TextField()
    source_code: str = models.TextField()
    docstring: str | None = models.TextField(null=True, blank=True)
    comments: list | None = models.JSONField(null=True, blank=True)
    string_literals: list | None = models.JSONField(null=True, blank=True)
    variables: list | None = models.JSONField(null=True, blank=True)
    constants: list | None = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ("file_path", "name", "line_start")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["file_path"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.file_path}:{self.line_start}-{self.line_end})"


class DataFileInfo(models.Model):
    file_path = models.CharField(max_length=500, unique=True)
    file_type = models.CharField(max_length=10)  # "json" or "yaml"
    content = models.TextField(null=True, blank=True)  # Actual file content
    reference_contexts = models.JSONField(
        default=list, null=True, blank=True
    )  # Store line numbers and context snippets
    last_analyzed = models.DateTimeField(auto_now=True)

    # Relationship with functions that reference this file
    referenced_by = models.ManyToManyField(FunctionInfo, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["file_type"]),
            models.Index(fields=["file_path"]),
        ]

    def __str__(self) -> str:
        return f"DataFile: {self.file_path} ({self.file_type})"


class DataFileAnalysis(models.Model):
    data_file = models.OneToOneField(DataFileInfo, on_delete=models.CASCADE, related_name="analysis")
    is_valid_reference = models.BooleanField(default=False)  # True reference or false positive?
    file_purpose = models.TextField(null=True, blank=True)  # Description of what this file is used for
    content_category = models.CharField(
        max_length=50, null=True, blank=True
    )  # "prompt", "data", "configuration", "other"
    confidence_score = models.FloatField(default=0.0)  # Confidence level of analysis
    analysis_date = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_valid_reference"]),
            models.Index(fields=["content_category"]),
        ]

    def __str__(self) -> str:
        return f"Analysis of {self.data_file.file_path} - {self.content_category or 'Uncategorized'}"
