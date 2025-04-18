import instructor
import litellm
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Rules(BaseModel):
    model_config = ConfigDict(extra="ignore")

    always: list[str] = Field(description="Things to always do")
    never: list[str] = Field(description="Things to never do")
    tips: list[str] = Field(default=[], description="Any additional, useful tips")

    @field_validator("always", "never", "tips")
    def remove_template_fields(cls, v):
        return [item.replace("{{", "").replace("}}", "") for item in v]


def merge_rules(before: Rules, after: Rules, lm: str = instructor.from_litellm(litellm.completion)) -> Rules:
    rules: Rules = lm.create(
        response_model=Rules,
        model="openai/o4-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert prompt engineer. "
                    "You are tasked with combining rules for prompting. "
                    "Combine these rules into a single, semantically deduplicated yet comprehensive set of rules. "
                    "The new rules include new learnings. "
                    "These rules will be injected into a prompt. "
                    "These rules should be direct and actionable for an LLM. "
                    "Rules should only come from the old and new rules."
                ),
            },
            {
                "role": "user",
                "content": f"<old-rules>{before}</old-rules>\n<new-rules>{after}</new-rules>",
            },
        ],
    )
    return rules
