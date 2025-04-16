"""
CrewAI example for lead email generation.

This example requires the crewai optional dependency:
`rye sync --features crewai` or `pip install -e ".[crewai]"`
"""

try:
    from .crew import LeadEmailCrew
except ImportError:
    # This allows the package to be imported even if crewai is not installed
    pass

__all__ = ["LeadEmailCrew"]
