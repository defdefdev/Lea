import requests
import anthropic
import time
import os
import random
import cloudinary
import cloudinary.uploader
from anthropic import Anthropic
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, ImageSequenceClip
from PIL import Image
import numpy as np

SUBTITLES_API_KEY = os.environ["SUBTITLES_API_KEY"]
SUBTITLES_TEMPLATE_ID = os.environ["SUBTITLES_TEMPLATE_ID"]
LANGUAGE = "en"
movement_api_key = os.environ["MOVEMENT_API_KEY"]
default_photo_url = "https://s7.gifyu.com/images/SJtSF.png"
box_coordinates = [261, 372, 798, 1005]

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"]
)

api_key_eleven_labs = os.environ["ELEVEN_LABS_API_KEY"]
voice_id = os.environ["ELEVEN_LABS_VOICE_ID"]

claude_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def upload_audio_to_cloudinary(file_path):
    try:
        upload_result = cloudinary.uploader.upload_large(file_path, resource_type="auto")
        print("Audio file uploaded successfully!")
        return upload_result['secure_url']
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None

def upload_video_to_cloudinary(file_path):
    try:
        upload_result = cloudinary.uploader.upload_large(file_path, resource_type="video")
        print("Video uploaded successfully to Cloudinary!")
        return upload_result['secure_url']
    except Exception as e:
        print(f"Error uploading video to Cloudinary: {e}")
        return None

def generate_audio_with_eleven_labs(text, voice_id, api_key):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "style": 1,
            "use_speaker_boost": False,
            "similarity_boost": 0,
            "stability": 0
        }
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        try:
            audio_file_path = "audio_output.mp3"
            with open(audio_file_path, "wb") as audio_file:
                audio_file.write(response.content)
            print("Audio saved as 'audio_output.mp3'.")
            audio_url = upload_audio_to_cloudinary(audio_file_path)
            return audio_url
        except Exception as e:
            print(f"Error saving audio: {e}")
            return None
    else:
        print(f"HTTP Error {response.status_code}: {response.text}")
        return None

class AIAvatarCreator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "movement_token": f"{self.api_key}",
            "Content-Type": "application/json"
        }

    def create_avatar(self, photo_url, audio_url, box_coordinates):
        print("Creating avatar with audio overlay...")
        url = os.getenv("MOVEMENT_CREATE_URL")
        data = {
            "photoUrl": photo_url,
            "info": [{"audioUrl": audio_url, "box": box_coordinates}],
            "watermark": 0,
            "useSr": False,
            "subtitles": 0
        }
        response = requests.post(url, json=data, headers=self.headers)
        if response.status_code == 200:
            result = response.json()
            project_id = result["data"]["id"]
            print("Avatar creation started, project ID:", project_id)
            return project_id
        else:
            print("Error in avatar creation.")
            return None

    def get_video_url(self, project_id, wait_time=5, max_retries=100):
        print("Waiting for avatar video to be ready...")
        url = f"{os.getenv('MOVEMENT_PROJECT_URL')}/{project_id}"
        for i in range(max_retries):
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                video_url = result["data"]["videoUrl"]
                if video_url:
                    print("Video ready at URL:", video_url)
                    return video_url
            print(f"Retry {i+1}/{max_retries} - video not ready yet, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        print("Video creation failed or timed out.")
        return None

def merge_video_and_audio(intro_video_path, video_response_path, background_audio_path, output_video_path):
    try:
        intro_clip = VideoFileClip(intro_video_path)
        video_clip = VideoFileClip(video_response_path)
        intro_width, intro_height = intro_clip.size
        video_clip = video_clip.resize((intro_width, intro_height))
        intro_audio = intro_clip.audio
        intro_audio = intro_audio.volumex(0.2)
        intro_with_audio = intro_clip.set_audio(intro_audio)
        response_audio = video_clip.audio
        response_audio = response_audio.volumex(1.05)
        background_audio = AudioFileClip(background_audio_path)
        response_duration = video_clip.duration
        if background_audio.duration < response_duration:
            n_loops = int(np.ceil(response_duration / background_audio.duration))
            background_audio = background_audio.loop(n=n_loops)
        background_audio = background_audio.subclip(0, response_duration)
        background_audio = background_audio.volumex(0.5)
        if response_audio:
            from moviepy.audio.AudioClip import CompositeAudioClip
            response_composite_audio = CompositeAudioClip([background_audio, response_audio])
            video_clip = video_clip.set_audio(response_composite_audio)
        final_video = concatenate_videoclips([intro_with_audio, video_clip], method="compose")
        final_video.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=25,
            threads=4,
            preset='ultrafast'
        )
        intro_clip.close()
        video_clip.close()
        background_audio.close()
        if response_audio:
            response_audio.close()
        final_video.close()
        print(f"Final video generated successfully: {output_video_path}")
        return True
    except Exception as e:
        print(f"Error merging video and audio: {e}")
        return None
    finally:
        try:
            if 'intro_clip' in locals():
                intro_clip.close()
            if 'video_clip' in locals():
                video_clip.close()
            if 'background_audio' in locals():
                background_audio.close()
            if 'response_audio' in locals():
                response_audio.close()
            if 'final_video' in locals():
                final_video.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")

def correct_transcript_with_claude(original_transcript, reference_text):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01"
    }
    original_text = " ".join([entry['text'] for entry in original_transcript])
    payload = {
        "model": "claude-3-opus-20240229",
        "messages": [
            {
                "role": "user",
                "content": f"""You are a program that corrects a transcription to match exactly the reference text.
You must return ONLY the corrected transcription, without any other text or introduction.

Original transcription: {original_text}
Reference text: {reference_text}

Rules:
1. Correct spelling, case and punctuation to match exactly the reference text
2. Keep EXACTLY the same time segmentation as the original transcription
3. Return ONLY the corrected words, without ANY introduction or conclusion text
4. Each word must be separated by a space"""
            }
        ],
        "max_tokens": 4096
    }
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload
        )
        if response.status_code != 200:
            print("Claude API Error:", response.text)
            return None
        correction = response.json()
        corrected_text = correction['content'][0]['text'].strip()
        corrected_transcript = []
        words = corrected_text.split()
        for i, (entry, corrected_word) in enumerate(zip(original_transcript, words)):
            corrected_transcript.append({
                "text": corrected_word,
                "type": "word",
                "start_time": entry['start_time'],
                "end_time": entry['end_time']
            })
        return corrected_transcript
    except Exception as e:
        print(f"Error during Claude correction: {e}")
        return None

def upload_video(file_path, api_key):
    url = "https://api.subtitles.ai/videos"
    headers = {"X-Api-Key": api_key}
    with open(file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, headers=headers, files=files)
    if response.status_code != 201:
        print("Upload error:", response.text)
        return None
    video_id = response.json().get('id')
    print(f"Video uploaded. ID: {video_id}")
    return video_id

def create_transcription_task(video_id, template_id, language='en'):
    url = f"https://api.subtitles.ai/videos/{video_id}/task"
    headers = {"Content-Type": "application/json", "X-Api-Key": SUBTITLES_API_KEY}
    payload = {"templateId": template_id, "language": language, "autoApprove": True}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 201:
        print("Task creation error:", response.text)
        return None
    task_id = response.json().get('taskId')
    print(f"Transcription task created. ID: {task_id}")
    return task_id

def check_task_status(video_id, task_id):
    url = f"https://api.subtitles.ai/videos/{video_id}/task/{task_id}"
    headers = {"X-Api-Key": SUBTITLES_API_KEY}
    retry_count = 0
    max_retries = 30
    while retry_count < max_retries:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Status check error:", response.text)
            return None, None
        data = response.json()
        status = data.get('status', '').lower()
        if status == "completed":
            return status, data.get('downloadUrl')
        elif status in ["failed", "error"]:
            print("Task failed.")
            return None, None
        retry_count += 1
        time.sleep(10)
    return None, None

def get_transcript(video_id, task_id):
    url = f"https://api.subtitles.ai/videos/{video_id}/task/{task_id}/transcript"
    headers = {"X-Api-Key": SUBTITLES_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Transcript retrieval error:", response.text)
        return None
    return response.json()

def create_subtitle_task(video_id, transcript):
    url = f"https://api.subtitles.ai/videos/{video_id}/task"
    headers = {"Content-Type": "application/json", "X-Api-Key": SUBTITLES_API_KEY}
    payload = {
        "templateId": SUBTITLES_TEMPLATE_ID,
        "transcript": transcript,
        "autoApprove": True,
        "language": LANGUAGE,
        "renderOptions": {
            "styleOptions": {
                "top": 55
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 201:
        print("Subtitle task creation error:", response.text)
        return None
    task_id = response.json().get('taskId')
    print(f"Subtitle task created. ID: {task_id}")
    return task_id

def add_snow_overlay(video_path, snow_gif_path, output_path):
    try:
        video = VideoFileClip(video_path)
        video_duration = video.duration
        width, height = video.size
        snow_frames = []
        gif = Image.open(snow_gif_path)
        n_frames = gif.n_frames
        try:
            for frame_idx in range(n_frames):
                gif.seek(frame_idx)
                frame = gif.convert('RGBA')
                frame = frame.resize((width, height), Image.Resampling.LANCZOS)
                snow_frames.append(np.array(frame))
        except EOFError:
            pass
        snow_clip = ImageSequenceClip(snow_frames, fps=25)
        single_loop_duration = len(snow_frames) / 25
        num_loops = int(np.ceil(video_duration / single_loop_duration))
        snow_clip = snow_clip.loop(n=num_loops)
        snow_clip = snow_clip.set_duration(video_duration)
        snow_clip = snow_clip.set_opacity(0.5)
        final_clip = CompositeVideoClip([video, snow_clip])
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=25,
            preset='ultrafast',
            threads=4
        )
        video.close()
        final_clip.close()
        snow_clip.close()
        return True
    except Exception as e:
        print(f"Snow overlay error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            if 'video' in locals():
                video.close()
            if 'final_clip' in locals():
                final_clip.close()
            if 'snow_clip' in locals():
                snow_clip.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")

def process_responses():
    try:
        with open("responses.txt", 'r', encoding='utf-8') as file:
            text = file.read().strip()
            if not text:
                print("responses.txt is empty. Exiting...")
                return
            photo_url = default_photo_url
            audio_url = generate_audio_with_eleven_labs(text, voice_id, api_key_eleven_labs)
            if audio_url:
                avatar_creator = AIAvatarCreator(movement_api_key)
                project_id = avatar_creator.create_avatar(photo_url, audio_url, box_coordinates)
                if project_id:
                    video_url = avatar_creator.get_video_url(project_id)
                    if video_url:
                        local_video_path = "video_response.mp4"
                        with requests.get(video_url, stream=True) as r:
                            r.raise_for_status()
                            with open(local_video_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        try:
                            video_id = upload_video(local_video_path, SUBTITLES_API_KEY)
                            if not video_id:
                                raise Exception("subtitles upload failed")
                            transcription_task_id = create_transcription_task(video_id, SUBTITLES_TEMPLATE_ID)
                            if not transcription_task_id:
                                raise Exception("Transcription task creation failed")
                            status, _ = check_task_status(video_id, transcription_task_id)
                            if not status:
                                raise Exception("Transcription task failed")
                            original_transcript = get_transcript(video_id, transcription_task_id)
                            if not original_transcript:
                                raise Exception("Transcript retrieval failed")
                            corrected_transcript = correct_transcript_with_claude(original_transcript, text)
                            if not corrected_transcript:
                                print("Using original transcript as fallback")
                                corrected_transcript = original_transcript
                            subtitle_task_id = create_subtitle_task(video_id, corrected_transcript)
                            if not subtitle_task_id:
                                raise Exception("Subtitle task creation failed")
                            status, final_video_url = check_task_status(video_id, subtitle_task_id)
                            if not status or not final_video_url:
                                raise Exception("Final video retrieval failed")
                            subtitled_video_path = "video_response_subtitled.mp4"
                            with requests.get(final_video_url, stream=True) as r:
                                r.raise_for_status()
                                with open(subtitled_video_path, 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
                            intro_video_path = 'LEA_INTRO.mp4'
                            background_audio_path = 'audiogame.mp3'
                            merged_video_path = 'merged_video.mp4'
                            if os.path.exists(intro_video_path) and os.path.exists(background_audio_path):
                                merged_url = merge_video_and_audio(
                                    intro_video_path,
                                    subtitled_video_path,
                                    background_audio_path,
                                    merged_video_path
                                )
                                if merged_url:
                                    print("Video merged with intro and background audio")
                                    subtitled_video_path = merged_video_path
                            snow_gif_path = "SNOW.gif"
                            final_video_path = "final_video_with_snow.mp4"
                            if os.path.exists(snow_gif_path):
                                if add_snow_overlay(subtitled_video_path, snow_gif_path, final_video_path):
                                    print("Snow overlay added successfully")
                                    final_url = upload_video_to_cloudinary(final_video_path)
                                else:
                                    print("Snow overlay failed, using video without snow effect")
                                    final_url = upload_video_to_cloudinary(subtitled_video_path)
                            else:
                                print("Snow gif not found, using video without snow effect")
                                final_url = upload_video_to_cloudinary(subtitled_video_path)
                            if os.path.exists(local_video_path):
                                os.remove(local_video_path)
                            if os.path.exists(subtitled_video_path):
                                os.remove(subtitled_video_path)
                            if os.path.exists(merged_video_path):
                                os.remove(merged_video_path)
                            if os.path.exists(final_video_path):
                                os.remove(final_video_path)
                            print("Final video URL:", final_url)
                            if final_url:
                                try:
                                    with open('link.txt', 'w', encoding='utf-8') as link_file:
                                        link_file.write(final_url)
                                    print("Link saved to link.txt")
                                except Exception as e:
                                    print(f"Error saving link to file: {e}")
                        except Exception as e:
                            print(f"Error in video processing: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print("Failed to get video URL from avatar creator")
                else:
                    print("Failed to create avatar project")
            else:
                print("Failed to generate audio")
    except FileNotFoundError:
        print("responses.txt not found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_responses()
