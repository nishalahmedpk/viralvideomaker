from typing import Union

from fastapi import FastAPI

from graph import graph, State

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Viral Video Maker API"}

@app.get("/generate_video")
def generate_video(project_name: str,description: str, generate_video: bool):
    """
    Endpoint to generate a viral video based on the provided description.
    
    :param project_name: Name of the project for video generation.
    :param description: Description for the viral video.
    :param generate_video: Flag to indicate whether to generate a video.
    :return: Result of the video generation process.
    """

    import os
    import shutil

    if os.path.exists(project_name):
        shutil.rmtree(project_name)
    os.makedirs(project_name, exist_ok=True)

    initial_state = State(description=description, generate_video=generate_video, project_name=project_name)
    
    # Invoke the graph with the initial state
    result = graph.invoke(initial_state)
    
    return {"graph_state": result,"path":os.path.abspath(project_name)}

