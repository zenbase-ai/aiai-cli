from django.db import models


class OtelSpan(models.Model):
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    agent_run_id = models.CharField(max_length=32, db_index=True, null=True, blank=True)
    input_data: models.JSONField = models.JSONField(null=True, blank=True)
    output_data: models.TextField = models.TextField(null=True, blank=True)
    raw_span: models.JSONField = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Run at {self.timestamp} - OtelSpan: {self.agent_run_id}"


class DiscoveredRule(models.Model):
    rule_text: models.TextField = models.TextField()
    confidence: models.DecimalField = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self) -> str:
        return f"Rule: {self.rule_text[:50]}... ({self.confidence}%)"


class FunctionInfo(models.Model):
    name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=512)
    line_start = models.IntegerField()
    line_end = models.IntegerField()
    signature = models.TextField()
    source_code = models.TextField()
    docstring = models.TextField(null=True, blank=True)
    comments = models.JSONField(null=True, blank=True)
    string_literals = models.JSONField(null=True, blank=True)
    variables = models.JSONField(null=True, blank=True)
    constants = models.JSONField(null=True, blank=True)

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
