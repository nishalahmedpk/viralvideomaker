def main():
    from graph import graph,State

    # Example state to invoke the graph
    initial_state = State(description=input("Enter the description for the viral video: "), generate_video=input("Do you want to generate a video? (y/n): ").strip().lower() == 'yes')
    
    # Invoke the graph with the initial state
    result = graph.invoke(initial_state)
    
    # Print the result
    print(result)


if __name__ == "__main__":
    main()
