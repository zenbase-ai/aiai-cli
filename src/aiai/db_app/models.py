# src/aiai/db_app/models.py
from django.db import models
from django.db.models import TextField
from django.db.models import DecimalField

class AgentRunLog(models.Model):
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    input_data: models.JSONField = models.JSONField()
    output_data: TextField = models.TextField()
    success: models.BooleanField = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Run at {self.timestamp} - Success: {self.success}"

class DiscoveredRule(models.Model):
    rule_text: TextField = models.TextField()
    confidence: DecimalField = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self) -> str:
        return f"Rule: {self.rule_text[:50]}... ({self.confidence}%)"