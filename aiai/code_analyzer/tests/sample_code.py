"""
Sample code for testing the code analyzer.
This file contains several functions that call each other to demonstrate
the function dependency analysis.
"""


def main():
    """
    Main entry point that calls other functions.
    """
    print("Starting program")
    data = get_data()
    processed_data = process_data(data)
    result = calculate_result(processed_data)
    display_result(result)
    print("Program completed")
    return result


def get_data():
    """
    Fetch some sample data.
    """
    data = [1, 2, 3, 4, 5]
    return data


def process_data(data):
    """
    Process the input data.
    """
    processed = []
    for item in data:
        processed.append(transform_item(item))

    return processed


def transform_item(item):
    """
    Transform a single data item.
    """
    return item * 2


def calculate_result(processed_data):
    """
    Calculate the final result from processed data.
    """
    result = sum(processed_data)
    if result > 20:
        result = apply_bonus(result)
    return result


def apply_bonus(value):
    """
    Apply a bonus to the value.
    """
    return value * 1.5


def display_result(result):
    """
    Display the final result.
    """
    print(f"The final result is: {result}")
    format_for_report(result)


def format_for_report(value):
    """
    Format the value for a report.
    """
    return f"Result: {value:.2f}"
