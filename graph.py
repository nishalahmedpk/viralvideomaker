from typing import Annotated, NotRequired, List

from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class State(TypedDict):
    # messages: Annotated[list, add_messages]
    # prompts: List[str] = []
    # generated_video_files: List[str] = []
    description: str = ""
    prompts: NotRequired[List[str]] = []
    generated_video_files: NotRequired[List[str]] = []
    hashtags: NotRequired[List[str]] = []
    script: NotRequired[str] = ""
    voiceover: NotRequired[str] = ""
    cuts: NotRequired[List[int]] = []
    audio_file: NotRequired[str] = ""
    video_files: NotRequired[List[str]] = []


graph_builder = StateGraph(State)



from dotenv import load_dotenv
import os
load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("google_genai:gemini-2.0-flash")


import requests
import json
import time

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") 
deployment = os.getenv("DEPLOYMENT_NAME", "sora")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY", "<AZURE_OPENAI_API_KEY>")

api_version = "preview"
path = f'openai/v1/video/generations/jobs'
params = f'?api-version={api_version}'
constructed_url = endpoint + path + params

headers = {
  'Api-Key': subscription_key,
  'Content-Type': 'application/json',
}


def generate_and_download_video(prompt: str,i:int):
    print(f"Generating video for prompt {i+1}: {prompt}")
    body = {
        "prompt": prompt,
        "n_variants": 1,
        "n_seconds": 5,
        "height": 1920,
        "width": 1080,
        "model": deployment,
    }
    job_response = requests.post(constructed_url, headers=headers, json=body)
    if not job_response.ok:
        print(f"❌ Video {i} generation failed.")
        print(json.dumps(job_response.json(), sort_keys=True, indent=4, separators=(',', ': ')))
    else:
        print(json.dumps(job_response.json(), sort_keys=True, indent=4, separators=(',', ': ')))
        job_response = job_response.json()
        job_id = job_response.get("id")
        status = job_response.get("status")
        status_url = f"{endpoint}openai/v1/video/generations/jobs/{job_id}?api-version={api_version}"

        print(f"⏳ Polling job status for Video {i} with ID: {job_id}")
        while status not in ["succeeded", "failed"]:
            time.sleep(5)
            job_response = requests.get(status_url, headers=headers).json()
            status = job_response.get("status")
            print(f"Status: {status}")

        if status == "succeeded":
            generations = job_response.get("generations", [])
            if generations:
                print(f"✅ Video {i} generation succeeded.")

                generation_id = generations[0].get("id")
                video_url = f'{endpoint}openai/v1/video/generations/{generation_id}/content/video{params}'
                print(f"Video URL: {video_url}")
                video_response = requests.get(video_url, headers=headers)
                if video_response.ok:
                    output_filename = f"output{i}.mp4"
                    with open(output_filename, "wb") as file:
                        file.write(video_response.content)
                    print(f'Generated video saved as "{output_filename}"')
            else:
                print("⚠️ Status is succeeded, but no generations were returned.")
        elif status == "failed":
            print("❌ Video {i} generation failed.")
            print(json.dumps(job_response, sort_keys=True, indent=4, separators=(',', ': ')))

def VideoGenerator(state: State):
    if "prompts" in state:
        print(state["prompts"])
        # return state
    video_files = []
    for i, prompt in enumerate(state["prompts"]):
        print(f"Generating video for prompt {i+1}: {prompt}")
        video_files.append(f"output{i}.mp4")
        generate_and_download_video(prompt, i)


from langgraph.types import Command
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate


prompt1 = ChatPromptTemplate.from_messages([
    ("system","""Generate viral hashtags related to the given user description. Return them as a JSON list.""" ),
    ("human", "{input}"),
])
class HashtagOutput(BaseModel):
    hashtags: List[str]
def HashtagGenerator(state: State):
    llm_structured = llm.with_structured_output(HashtagOutput)
    result = (prompt1 | llm_structured).invoke({"input": state["description"]})
    return Command(update={"hashtags": result.hashtags})

class ScriptOutput(BaseModel):
    script: str
    voiceover: str
prompt2 = ChatPromptTemplate.from_messages([
    ("system", 
     """You are a skilled voiceover artist and scriptwriter specializing in creating captivating viral short videos.  
Given a user’s description, generate a **15-second voiceover script** that is expressive, engaging, and drives emotional connection.  

The voiceover should:  
- Be written exactly as it would be spoken — no stage directions, tone markers, or parenthetical notes.  
- Use natural, conversational language that flows smoothly.  
- Be the centerpiece, with the accompanying video script serving as visual support to enhance the narration.  

Return the output as JSON with keys:  
- 'voiceover': the spoken script as plain text only (no parentheses or tone labels).  
- 'script': a short description of the video visuals that would match the voiceover."""
),
    ("human", "{input}"),
])

def ScriptGenerator(state: State):
    llm_structured = llm.with_structured_output(ScriptOutput)
    result = (prompt2 | llm_structured).invoke({"input": state["description"]})
    return Command(update={"script": result.script, "voiceover": result.voiceover})

class PromptOutput(BaseModel):
    prompts: List[str]
prompt3 = ChatPromptTemplate.from_messages([
    ("system",
     """You are an expert cinematic storyteller and prompt engineer specializing in creating detailed, scene-by-scene prompts for video generation.  
     Given the voiceover script provided, generate 3 to 5 vivid and richly detailed scene prompts that visually interpret and complement the voiceover.  
     Ensure that all scenes share a consistent thematic style in lighting, color palette, mood, and visual motifs, so the final video feels coherent and unified.  
     Do NOT include text overlays or voiceover lines in the prompts—focus entirely on visual descriptions, actions, settings, and atmosphere that can guide video creation.  
     Return the prompts as a JSON list under the key 'prompts'."""),
    ("human", "{input}"),
])
def SceneGenerator(state: State):
    llm_structured = llm.with_structured_output(PromptOutput)
    result = (prompt3 | llm_structured).invoke({"input": state["voiceover"]})
    return Command(update={"prompts": result.prompts})

def JSONPromptGenerator(state: State):
    # llm1 = prompt1 | llm
    # Create a list of prompts from planner.
    dummy_prompts = [
        "A cat playing piano in a jazz bar with lively music.",
        "A bustling street market with colorful stalls and ambient chatter.",
    ]
    return Command(update={"prompts": dummy_prompts})

from elevenlabs.client import ElevenLabs

def audio_generator(state: State):
    if "voiceover" not in state or not state["voiceover"]:
        print("No voiceover provided, skipping audio generation.")
        return state
    
    print(f"Generating audio for voiceover: {state['voiceover']}")
    audio_filename = "output_audio.mp3"

    # Initialize ElevenLabs client
    client = ElevenLabs()

    # Convert text to speech (returns a generator)
    audio_stream = client.text_to_speech.convert(
        text=state["voiceover"],
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128"
    )

    # Combine generator chunks into bytes
    audio_bytes = b"".join(audio_stream)

    # Save to file
    with open(audio_filename, "wb") as f:
        f.write(audio_bytes)

    print(f"Generated audio saved as '{audio_filename}'")
    return Command(update={"audio_file": audio_filename})


import numpy as np
from moviepy.editor import AudioFileClip, concatenate_audioclips

def combine_videos_with_audio(state: State):
    import os
    import numpy as np
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
    from moviepy.audio.AudioClip import AudioArrayClip
    from langgraph.types import Command

    video_files = state.get("video_files", [])
    video_files = ["output0.mp4", "output1.mp4", "output2.mp4", "output3.mp4", "output4.mp4"]

    if not video_files:
        print("No video files found in state — cannot combine.")
        return state

    audio_file = "output_audio.mp3"
    if not os.path.exists(audio_file):
        print("No audio file found — cannot combine.")
        return state

    clips = []
    try:
        for v in video_files:
            if not os.path.exists(v):
                print(f"File not found: {v}")
                continue
            clip = VideoFileClip(v)
            if clip.duration is None:
                print(f"Skipping {v}: duration is None")
                clip.close()
                continue
            clips.append(clip)

        if not clips:
            print("No valid video clips loaded.")
            return state

        final_clip = concatenate_videoclips(clips, method="compose")

        audio_clip = AudioFileClip(audio_file)

        # If audio is shorter, trim the video to audio duration (remove silence padding)
        if audio_clip.duration < final_clip.duration:
            print(f"Trimming video from {final_clip.duration} to audio duration {audio_clip.duration}")
            final_clip = final_clip.subclip(0, audio_clip.duration)

        # If audio longer, trim audio to video duration
        elif audio_clip.duration > final_clip.duration:
            audio_clip = audio_clip.subclip(0, final_clip.duration)

        final_clip = final_clip.set_audio(audio_clip)

        output_file = "final_video_with_audio.mp4"
        final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")

        print(f"Final video saved as {output_file}")
        return Command(update={"final_video": output_file})

    except Exception as e:
        print(f"Error combining videos: {e}")
        return state

    finally:
        for c in clips:
            c.close()


graph_builder = StateGraph(State)
graph_builder.add_node("HashtagGenerator", HashtagGenerator)
graph_builder.add_node("ScriptGenerator", ScriptGenerator)
graph_builder.add_node("SceneGenerator", SceneGenerator)
graph_builder.add_node("VideoGenerator", VideoGenerator)
graph_builder.add_node("audio_generator", audio_generator)
graph_builder.add_node("combine_videos_with_audio", combine_videos_with_audio)
graph_builder.add_edge(START, "HashtagGenerator")
graph_builder.add_edge("HashtagGenerator", "ScriptGenerator")
graph_builder.add_edge("ScriptGenerator", "SceneGenerator")
graph_builder.add_edge("SceneGenerator", "VideoGenerator")
graph_builder.add_edge("VideoGenerator", "audio_generator")
graph_builder.add_edge("audio_generator", "combine_videos_with_audio")
graph_builder.add_edge("combine_videos_with_audio", END)
graph = graph_builder.compile()

# graph.invoke(State(description=""" Create a viral video for promoting BTIS Pilani""")) #Wrap this in a function to invoke the graph
