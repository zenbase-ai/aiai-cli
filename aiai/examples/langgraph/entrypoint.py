from examples.langgraph.langgraph_agent import create_agent


def main(inputs=None):
    inputs = inputs or {"topic": "Benefits of regular exercise"}
    agent = create_agent()
    return agent.invoke(inputs)


if __name__ == "__main__":
    # If run directly, print the result
    print(main())
