def main():
    from graph import graph,State

    # Example state to invoke the graph
    initial_state = State(description=input("Enter the description for the viral video: "))
    
    # Invoke the graph with the initial state
    result = graph.invoke(initial_state)
    
    # Print the result
    print(result)


if __name__ == "__main__":
    main()
