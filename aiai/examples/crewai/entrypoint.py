try:
    from aiai.examples.crewai.crew import LeadEmailCrew
except ImportError:
    print("Error: crewAI is not installed. Please install it using:")
    print("  rye sync --features crewai")
    print("  or")
    print("  pip install -e '.[crewai]'")
    import sys

    sys.exit(1)

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv


def main():
    """Run the lead email generation crew"""
    # Load environment variables from .env file
    load_dotenv()  # By default looks in current working directory

    # Check for OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("Error: OpenAI API key not found.")
        print(
            "Please set your OPENAI_API_KEY environment variable or add it to a .env file."
        )
        print(
            "Place your .env file in the project root or in src/aiai/examples/crewai/"
        )
        sys.exit(1)

    # Ensure we're working with paths relative to this script
    script_dir = Path(__file__).resolve().parent

    # Create sample data file if it doesn't exist
    people_data_path = script_dir / "people_data.json"
    if not people_data_path.exists():
        sample_data = {
            "leads_text": "Amir Mehr is the CTO of Zenbase AI with a focus on optimizing LLM workflows. "
            "Sarah Johnson is a Lead Developer at Tech Solutions Inc. interested in prompt engineering and model selection."
        }
        with open(people_data_path, "w") as f:
            json.dump(sample_data, f)

    # Change working directory to the script directory for relative paths in the crew
    os.chdir(script_dir)

    # Run the crew
    crew_instance = LeadEmailCrew()
    result = crew_instance.crew().kickoff()
    return result


if __name__ == "__main__":
    main()
