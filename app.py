import os
import yt_dlp
from moviepy import VideoFileClip
import whisper
import streamlit as st

# ----------------------------------------
# Function to download YouTube video
# ----------------------------------------
def download_video(url, out_file="downloaded_video.mp4"):
    """
    Downloads a YouTube video using yt_dlp and saves it as an MP4 file.
    
    Args:
        url (str): The YouTube video URL.
        out_file (str): The desired output filename.
    
    Returns:
        str: Path to the downloaded video file.
    """
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download best available video and audio
        'outtmpl': out_file,                   # Output filename template
        'quiet': True,                         # Suppress verbose output
        'merge_output_format': 'mp4',          # Ensure output format is MP4
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return out_file

# ----------------------------------------
# Function to extract audio from video
# ----------------------------------------
def extract_audio(video_file, audio_file="audio.wav"):
    """
    Extracts audio from a video file and saves it as a WAV file.
    
    Args:
        video_file (str): Path to the input video file.
        audio_file (str): Path to save the extracted audio.
    
    Returns:
        str: Path to the extracted audio file.
    
    Raises:
        RuntimeError: If no audio stream is found in the video.
    """
    clip = VideoFileClip(video_file)
    if clip.audio is None:
        clip.close()
        raise RuntimeError(f"No audio stream found in {video_file}")
    
    clip.audio.write_audiofile(audio_file)
    clip.close()
    return audio_file

# ----------------------------------------
# Function to transcribe audio using Whisper
# ----------------------------------------
def transcribe_audio(audio_file):
    """
    Transcribes spoken content from an audio file using OpenAI's Whisper model.
    
    Args:
        audio_file (str): Path to the audio file.
    
    Returns:
        str: Transcribed text.
    """
    model = whisper.load_model("base")  # Load base Whisper model
    result = model.transcribe(audio_file)
    return result['text']

# ----------------------------------------
# Simple rule-based accent classifier
# ----------------------------------------
def simple_accent_classifier(text):
    """
    Performs simple rule-based accent detection based on keyword occurrences.
    
    Args:
        text (str): Transcribed text to analyze.
    
    Returns:
        tuple: Detected accent, confidence score (0–100), and explanation.
    """
    text = text.lower()
    
    # Accent-specific keyword lists
    british_keywords = ['colour', 'favourite', 'realise', 'aluminium', 'lorry', 'biscuit']
    american_keywords = ['color', 'favorite', 'realize', 'aluminum', 'truck', 'cookie']
    australian_keywords = ['mate', 'arvo', 'barbie', 'brekkie']

    # Count keyword occurrences
    british_score = sum(word in text for word in british_keywords)
    american_score = sum(word in text for word in american_keywords)
    australian_score = sum(word in text for word in australian_keywords)

    scores = {
        'British': british_score,
        'American': american_score,
        'Australian': australian_score
    }

    total = sum(scores.values())

    if total == 0:
        # No keywords found
        return "No accent detected", 0, "No accent keywords detected in the transcription."

    # Determine accent with the highest score
    accent = max(scores, key=scores.get)
    confidence = int(scores[accent] / total * 100)
    explanation = f"Detected keywords suggest {accent} accent with confidence {confidence}%."
    
    return accent, confidence, explanation

# ----------------------------------------
# Complete video-to-accent pipeline
# ----------------------------------------
def process_video(url):
    """
    Orchestrates the full pipeline: download → extract audio → transcribe → classify accent.
    
    Args:
        url (str): YouTube video URL.
    
    Returns:
        tuple: Transcription, accent label, confidence %, explanation.
    """
    video_file = None
    audio_file = None
    
    try:
        video_file = download_video(url)
        audio_file = extract_audio(video_file)
        transcription = transcribe_audio(audio_file)
        accent, confidence, explanation = simple_accent_classifier(transcription)
        return transcription, accent, confidence, explanation
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None, None, None
    finally:
        # Clean up temporary files
        if video_file and os.path.exists(video_file):
            os.remove(video_file)
        if audio_file and os.path.exists(audio_file):
            os.remove(audio_file)

# ----------------------------------------
# Streamlit User Interface
# ----------------------------------------
st.title("Accent Detector from YouTube Video")

# Input field for video URL
video_url = st.text_input("Enter YouTube video URL:")

# Button to start analysis
if st.button("Analyze Accent"):
    if not video_url.strip():
        st.warning("Please enter a valid YouTube video URL.")
    else:
        with st.spinner("Processing... This may take a few minutes depending on video length and model speed."):
            transcription, accent, confidence, explanation = process_video(video_url)

        if transcription is not None:
            st.subheader("Transcription:")
            st.write(transcription)

            st.subheader("Accent Detection Result:")
            st.write(f"**Accent:** {accent}")
            st.write(f"**Confidence:** {confidence}%")
            st.write(f"**Explanation:** {explanation}")
