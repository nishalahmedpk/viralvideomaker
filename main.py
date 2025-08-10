from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from graph import graph, State  # Assuming you have a graph module that provides these

app = FastAPI()


class VideoRequest(BaseModel):
    description: str

class VideoResponse(BaseModel):
    result: dict

@app.post("/generate-video", response_model=VideoResponse)
async def generate_video(req: VideoRequest):
    try:
        # Wrap the description in a State and invoke your graph
        state = State(description=req.description)
        output = graph.invoke(state)
        
        # Depending on your graph output, adapt this:
        # Here assuming output is a dict or similar
        return VideoResponse(result=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
