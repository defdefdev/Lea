import asyncio
from anthropic import AsyncAnthropic
import requests
from datetime import datetime, timedelta
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
import cloudinary
import cloudinary.uploader
import time
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

ALLOWED_GROUP_IDS = {
    -1002484970203,
    -1002409743841,
    -1001577098510,
    -1001326188873,
    -1001518809875,
    -1001837825278
}

user_last_response_time = {}
MAX_CONCURRENT_REQUESTS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

async def generate_text_with_claude(prompt):
    try:
        print("Generating response using Claude API...")
        character_context = (
        os.environ["CHARACTER_CONTEXT_LINE_1"] +
        os.environ["CHARACTER_CONTEXT_LINE_2"] +
        os.environ["CHARACTER_CONTEXT_LINE_3"] +
        os.environ["CHARACTER_CONTEXT_LINE_4"] +
        os.environ["CHARACTER_CONTEXT_LINE_5"] +
        os.environ["CHARACTER_CONTEXT_LINE_6"] +
        os.environ["CHARACTER_CONTEXT_LINE_7"] +
        os.environ["CHARACTER_CONTEXT_LINE_8"] +
        os.environ["CHARACTER_CONTEXT_LINE_9"] +
        os.environ["CHARACTER_CONTEXT_LINE_10"] +
        os.environ["CHARACTER_CONTEXT_LINE_11"] +
        os.environ["CHARACTER_CONTEXT_LINE_12"] +
        os.environ["CHARACTER_CONTEXT_LINE_13"] +
        os.environ["CHARACTER_CONTEXT_LINE_14"] +
        os.environ["CHARACTER_CONTEXT_LINE_15"] +
        os.environ["CHARACTER_CONTEXT_LINE_16"] +
        os.environ["CHARACTER_CONTEXT_LINE_17"] +
        os.environ["CHARACTER_CONTEXT_LINE_18"] +
        os.environ["CHARACTER_CONTEXT_LINE_19"] +
        os.environ["CHARACTER_CONTEXT_LINE_20"] +
        os.environ["CHARACTER_CONTEXT_LINE_21"] +
        os.environ["CHARACTER_CONTEXT_LINE_22"] +
        os.environ["CHARACTER_CONTEXT_LINE_23"] +
        os.environ["CHARACTER_CONTEXT_LINE_24"] +
        os.environ["CHARACTER_CONTEXT_LINE_25"] +
        os.environ["CHARACTER_CONTEXT_LINE_26"] +
        os.environ["CHARACTER_CONTEXT_LINE_27"] +
        os.environ["CHARACTER_CONTEXT_LINE_28"] +
        os.environ["CHARACTER_CONTEXT_LINE_29"] +
        os.environ["CHARACTER_CONTEXT_LINE_30"] +
        os.environ["CHARACTER_CONTEXT_LINE_31"] +
        os.environ["CHARACTER_CONTEXT_LINE_32"] +
        os.environ["CHARACTER_CONTEXT_LINE_33"] +
        os.environ["CHARACTER_CONTEXT_LINE_34"] +
        os.environ["CHARACTER_CONTEXT_LINE_35"] +
        os.environ["CHARACTER_CONTEXT_LINE_36"] +
        os.environ["CHARACTER_CONTEXT_LINE_37"] +
        os.environ["CHARACTER_CONTEXT_LINE_38"] +
        os.environ["CHARACTER_CONTEXT_LINE_39"] +
        os.environ["CHARACTER_CONTEXT_LINE_40"] +
        os.environ["CHARACTER_CONTEXT_LINE_41"] +
        os.environ["CHARACTER_CONTEXT_LINE_42"] +
        os.environ["CHARACTER_CONTEXT_LINE_43"] +
        os.environ["CHARACTER_CONTEXT_LINE_44"] +
        os.environ["CHARACTER_CONTEXT_LINE_45"] +
        os.environ["CHARACTER_CONTEXT_LINE_46"] +
        os.environ["CHARACTER_CONTEXT_LINE_47"] +
        os.environ["CHARACTER_CONTEXT_LINE_48"]
    )
        response = await anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=80,
            temperature=0.8,
            system=character_context,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        generated_text = response.content[0].text
        print("Response generated:", generated_text)
        return generated_text.strip()
    except Exception as e:
        print(f"Error in Claude API: {e}")
        return "I'm sorry, but I'm tired for now. Need a reboot."

async def generate_audio_with_eleven_labs(text, voice_id, api_key):
    loop = asyncio.get_event_loop()
    try:
        def make_request():
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
            return requests.post(url, json=data, headers=headers)

        response = await loop.run_in_executor(None, make_request)
        if response.status_code == 200:
            audio_file_path = f"audio_output_{int(time.time())}.mp3"
            with open(audio_file_path, "wb") as audio_file:
                audio_file.write(response.content)
            upload_result = await loop.run_in_executor(
                None,
                lambda: cloudinary.uploader.upload(audio_file_path, resource_type="auto")
            )
            os.remove(audio_file_path)
            return upload_result['secure_url']
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error in audio generation: {e}")
        raise

class AIAvatarCreator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "movement_token": f"{self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_avatar(self, photo_url, audio_url, box_coordinates):
        loop = asyncio.get_event_loop()
        try:
            def make_request():
                url = os.getenv("MOVEMENT_CREATE_URL")
                data = {
                    "photoUrl": photo_url,
                    "info": [{"audioUrl": audio_url, "box": box_coordinates}],
                    "watermark": 0,
                    "useSr": False
                }
                return requests.post(url, json=data, headers=self.headers)

            response = await loop.run_in_executor(None, make_request)
            if response.status_code == 200:
                result = response.json()
                return result["data"]["id"]
            else:
                raise Exception("Error in avatar creation")
        except Exception as e:
            print(f"Error in avatar creation: {e}")
            raise

    async def get_video_url(self, project_id, wait_time=5, max_retries=100):
        loop = asyncio.get_event_loop()
        url = f"{os.getenv('MOVEMENT_PROJECT_URL')}/{project_id}"
        for i in range(max_retries):
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(url, headers=self.headers)
                )
                if response.status_code == 200:
                    result = response.json()
                    if video_url := result["data"]["videoUrl"]:
                        return video_url
            except Exception as e:
                print(f"Error checking video status: {e}")
            await asyncio.sleep(wait_time)
        raise Exception("Video generation timed out")

async def process_message(update: Update, message_text: str):
    async with semaphore:
        try:
            response_text = await generate_text_with_claude(
                message_text.replace('/video/', '').replace('/audio/', '').strip()
            )
            audio_url = await generate_audio_with_eleven_labs(
                response_text,
                os.getenv("ELEVEN_LABS_VOICE_ID"),
                os.getenv("ELEVEN_LABS_API_KEY")
            )
            if "/video/" in message_text:
                avatar_creator = AIAvatarCreator(os.getenv("MOVEMENT_API_KEY"))
                project_id = await avatar_creator.create_avatar(
                    "https://s11.gifyu.com/images/SyFer.png",
                    audio_url,
                    [444, 131, 733, 478]
                )
                if project_id:
                    video_url = await avatar_creator.get_video_url(project_id)
                    if video_url:
                        video_path = f"response_video_{int(time.time())}.mp4"
                        response = requests.get(video_url)
                        with open(video_path, 'wb') as f:
                            f.write(response.content)
                        await update.message.reply_video(open(video_path, 'rb'))
                        os.remove(video_path)
                    else:
                        await update.message.reply_text("Failed to generate video.")
            else:
                audio_path = f"response_audio_{int(time.time())}.mp3"
                response = requests.get(audio_url)
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                await update.message.reply_audio(
                    open(audio_path, 'rb'),
                    filename="Lea_response.mp3"
                )
                os.remove(audio_path)
        except Exception as e:
            print(f"Error processing message: {e}")
            await update.message.reply_text("An error occurred while processing your request.")

async def handle_message(update: Update, context: CallbackContext):
    if update.message.chat.id not in ALLOWED_GROUP_IDS:
        return
    user_id = update.message.from_user.id
    current_time = datetime.now()
    if user_id in user_last_response_time:
        last_response_time = user_last_response_time[user_id]
        if (current_time - last_response_time < timedelta(minutes=5)):
            if "/video/" in update.message.text or "/audio/" in update.message.text:
                await update.message.reply_text("Please wait 5 min before mentioning me again.")
                return
    user_message = update.message.text
    if "/video/" in user_message or "/audio/" in user_message:
        asyncio.create_task(process_message(update, user_message))
        user_last_response_time[user_id] = current_time
    else:
        await update.message.reply_text("Specify '/video/' or '/audio/' to choose the response type.")

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Hello! I am Lea. Mention me and choose /video/ or /audio/.')

def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex('@Leagpt_bot'),
        handle_message
    ))
    application.run_polling()

if __name__ == '__main__':
    main()
