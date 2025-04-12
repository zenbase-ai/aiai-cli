from django.db import models

class AgentRunLog(models.Model):
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    agent_run_id = models.CharField(max_length=32, db_index=True, null=True, blank=True)
    input_data: models.JSONField = models.JSONField(null=True, blank=True)
    output_data: models.TextField = models.TextField(null=True, blank=True)
    success: models.JSONField = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Run at {self.timestamp} - Agent Run Id: {self.agent_run_id} - Success: {self.success}"

class DiscoveredRule(models.Model):
    rule_text: models.TextField = models.TextField()
    confidence: models.DecimalField = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self) -> str:
        return f"Rule: {self.rule_text[:50]}... ({self.confidence}%)"
