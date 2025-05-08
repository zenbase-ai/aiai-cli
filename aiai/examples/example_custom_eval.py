"""
Example custom evaluation function.

This file demonstrates how to create a custom evaluation function for the aiai CLI.
The file should contain a function named 'main' that takes agent output as input
and returns a dictionary with a 'reward' key.
"""

import random


def main(agent_output):
    """
    Custom evaluation function that scores agent output.

    Args:
        agent_output: The output from the agent to evaluate

    Returns:
        A dictionary with a 'reward' key containing a float from 0 to 1
    """
    score = 0.0

    score += random.uniform(0, 1)

    return {"reward": score}
