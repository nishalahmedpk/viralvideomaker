client = ElevenLabs()

# Convert text to speech using a specific voice and model
audio = client.text_to_speech.convert(
    text="Chicken is a great source of protein and can be prepared in many delicious ways.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # You can use voice name or voice ID
    model_id="eleven_multilingual_v2",  # Optional, defaults to best available
    output_format="mp3_44100_128"  # Audio file format
)

# Play the audio
with open("test.mp3", "wb") as f:
    f.write(audio)