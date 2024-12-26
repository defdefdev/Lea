import requests
import anthropic
import tweepy
from requests_oauthlib import OAuth1
import time
import os
from datetime import datetime, timedelta, timezone
import random
import json
import re
import base64
import cloudinary
import cloudinary.uploader
from anthropic import Anthropic

class TwitterImageAnalyzer:
    def __init__(self, bearer_token, claude_api_key):
        self.twitter_client = tweepy.Client(bearer_token=bearer_token)
        self.claude_client = anthropic.Anthropic(api_key=claude_api_key)

    def check_tweet_media(self, tweet_url):
        try:
            tweet_id = tweet_url.split('/')[-1]
            tweet = self.twitter_client.get_tweet(
                id=tweet_id,
                expansions=['attachments.media_keys'],
                media_fields=['url', 'type']
            )
            if tweet.includes and 'media' in tweet.includes:
                image_urls = [
                    media.url for media in tweet.includes['media']
                    if media.type == 'photo'
                ]
                return image_urls if image_urls else None
        except Exception as e:
            print(f"Error checking media: {e}")
        return None

    def download_image(self, image_url):
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading the image: {e}")
            return None

    def encode_image_base64(self, image_content):
        return base64.b64encode(image_content).decode('utf-8')

    def analyze_images_with_claude(self, image_base64_list):
        analyses = []
        for image_base64 in image_base64_list:
            try:
                response = self.claude_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_base64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": "Describe precisely what you see in this image. Be detailed and objective. And give your opinion. If there are numbers associated to some token or nft, regroup them together and describe everything. If it's a chart, check if there is a big red candle at the end, means it's a rug or scam but if there is a big green candle, it's pumping so it's bullish so always say if it's a bullish chart, bearish or neutral. If it's not a chart, don't talk about chart. Always describe everything with precision"
                                }
                            ]
                        }
                    ]
                )
                analyses.append(response.content[0].text)
            except Exception as e:
                print(f"Error analyzing an image: {e}")
                analyses.append("Unable to analyze this image")
        return analyses

    def process_tweet_image(self, tweet_url):
        image_urls = self.check_tweet_media(tweet_url)
        if not image_urls:
            return None
        image_base64_list = []
        for image_url in image_urls:
            image_content = self.download_image(image_url)
            if image_content:
                image_base64_list.append(self.encode_image_base64(image_content))
        if not image_base64_list:
            return None
        analyses = self.analyze_images_with_claude(image_base64_list)
        if len(analyses) == 1:
            return analyses[0]
        else:
            return "\n\n".join([f"Image {i+1} :\n{analyse}" for i, analyse in enumerate(analyses)])

api_key = os.environ["TWITTER_API_KEY"]
api_secret = os.environ["TWITTER_API_SECRET"]
bearer_token = os.environ["TWITTER_BEARER_TOKEN"]
access_token = os.environ["TWITTER_ACCESS_TOKEN"]
access_token_secret = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
api = tweepy.API(auth)

movement_api_key = os.environ["MOVEMENT_API_KEY"]
photo_url = "https://s11.gifyu.com/images/SyFer.png"
box_coordinates = [444, 131, 733, 478]
ass_text_effect = "FadeIn"
ass_text_color_primary = "#FF5733"
outline_colour = "&H00da77da"

def create_auth():
    return OAuth1(api_key, api_secret, access_token, access_token_secret)

claude_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
image_analyzer = TwitterImageAnalyzer(bearer_token=bearer_token, claude_api_key=os.environ["ANTHROPIC_API_KEY"])

def generate_text_with_claude(prompt, image_description=None):
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
        os.environ["CHARACTER_CONTEXT_LINE_42"]
    )
    if image_description:
        full_prompt = (
            f"{character_context}\n\n{prompt}\n\n"
            f"Note: A detailed analysis of the image is available. Use this analysis if relevant and when asked or to support your answer, provide image elements. If someone asks you to explain or describe the picture, do it with some precision. Only if needed use the image analysis else don't use it.\n\n"
            f"Image analysis:\n{image_description}"
        )
    else:
        full_prompt = f"{character_context}\n{prompt}"
    response = claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=800,
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )
    generated_text = response.content[0].text
    print(generated_text)
    return generated_text.strip()

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"]
)

def upload_audio_to_cloudinary(file_path):
    try:
        upload_result = cloudinary.uploader.upload(file_path, resource_type="auto")
        print("Audio file uploaded successfully!")
        return upload_result['secure_url']
    except Exception as e:
        print(f"Error during upload to Cloudinary: {e}")
        return None

elevenlabs_api_key = os.environ["ELEVEN_LABS_API_KEY"]
voice_id = os.environ["ELEVEN_LABS_VOICE_ID"]

def generate_audio_with_eleven_labs(text, voice_id, elevenlabs_api_key):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": elevenlabs_api_key
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
            print("The audio has been saved under the name 'audio_output.mp3'.")
            uploaded_audio_url = upload_audio_to_cloudinary(audio_file_path)
            if uploaded_audio_url:
                print("Audio uploaded successfully!")
                return uploaded_audio_url
            else:
                print("Audio upload failed.")
                return None
        except Exception as e:
            print(f"Error saving audio file: {e}")
            return None
    else:
        print(f"Failed to generate audio. Status code: {response.status_code}, Response: {response.text}")
        return None

class AIAvatarCreator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "movement_token": f"{self.api_key}",
            "Content-Type": "application/json"
        }

    def create_avatar(self, photo_url, audio_url, box_coordinates):
        print("Creating avatar with audio overlay and dynamic subtitles...")
        url = os.getenv("MOVEMENT_CREATE_URL")
        data = {
            "photoUrl": photo_url,
            "info": [{"audioUrl": audio_url, "box": box_coordinates}],
            "watermark": 0,
            "useSr": False
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

def upload_and_post_video_v2(local_video_path, tweet_id, summary_text):
    print("Uploading video response to Twitter...")
    try:
        media = api.media_upload(local_video_path, media_category='tweet_video')
        print(f"Media uploaded with ID: {media.media_id}")
        response = client.create_tweet(
            in_reply_to_tweet_id=tweet_id,
            media_ids=[media.media_id],
            text=summary_text
        )
        print("Tweet posted successfully with video and text!")
        tweet_video_id = response.data['id']
        return tweet_video_id
    except Exception as e:
        print(f"Exception occurred during media upload: {e}")
        return None

def save_tweet_data_to_json(data, filename="reply.json"):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                print("JSON file is empty or invalid. Starting fresh.")
                existing_data = []
    else:
        existing_data = []
    data["tweet_id_tagging_bot"] = data.get("tweet_id_tagging_bot", "unknown")
    data["username"] = data.get("username", "unknown")
    data["timestamp"] = data.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    existing_data.append(data)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, indent=4)

def load_existing_tweet_data(filename="reply.json"):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print("JSON file is empty or invalid. Starting fresh.")
                return []
    else:
        return []

def is_tweet_responded(tweet_id, existing_data):
    if not existing_data:
        return False
    for tweet in existing_data:
        if tweet.get("tweet_id_tagging_bot") == tweet_id:
            return True
    return False

def get_tweet_url(tweet_id, client):
    tweet_data = client.get_tweet(tweet_id, tweet_fields="author_id")
    author_id = tweet_data.data["author_id"]
    user_data = client.get_user(id=author_id, user_fields="username")
    username = user_data.data["username"]
    return f"https://x.com/{username}/status/{tweet_id}"

claude_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def generate_summary(response_text, tweet_text=None):
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    if tweet_text:
        prompt = f"Tweet context: {tweet_text}\nLea's response: {response_text}"
    else:
        prompt = f"You are Lea and you just create a punchy and provocative tweet based on this text you made or a fun tweet based on this text you made: {response_text}"
    prompt += """
Rules:
1. Maximum 10 words
2. Must be provocative, funny, or intriguing, it depends of the answer
3. Use @mentions if text talks about a specific person
4. DO NOT use phrases like "Here's", "Discover", "Watch"
5. Don't summarize content, create suspense instead
6. DO NOT use emoji
7. Return ONLY the tweet text, with no explanations or comments
8. Write AS Lea, not ABOUT Lea

Desired formats:
- For clashes/criticism: "@person better watch your back "
- For advice/info: "Your boss is lying "
- For predictions: "Bitcoin 100k tomorrow "
"""
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=60,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        tweet = response.content[0].text.strip()
        return tweet
    except Exception as e:
        print(f"Error generating tweet: {e}")
        return ""

user_list = [
    "elonmusk", "TheCryptoDog", "rajgokal",
    "sunyuchentron", "brian_armstrong", "jessepollak",
    "saylor", "MustStopMurad", "Flowslikeosmo",
    "notthreadguy", "himgajria", "Defi0xJeff",
    "0xngmi", "Darrenlautf", "frankdegods",
    "KookCapitalLLC", "beaniemaxi", "farokh",
    "rektmando", "osf_rekt", "gospelofgoatse",
    "truth_terminal", "dolos_diary", "aixbt_agent",
    "shawmakesmagic", "0xzerebro", "luna_virtuals",
    "cookiedotfun", "realDonaldTrump", "seedphrase",
    "CozomoMedici", "sama", "Polymarket",
    "beeple", "Cointelegraph", "rihanna",
    "ParisHilton", "IGGYAZALEA", "Cobratate",
    "DanBilzerian", "HalieyWelchX", "a1lon9",
    "zhusu", "blknoiz06", "moonshot", "mellometrics",
    "cryptolyxe", "Davincij15", "orangie", "_RichardTeng",
    "Defi0xJeff", "cb_doge", "dxrnelljcl", "mrpunkdoteth",
    "1solinfeb", "CrashiusClay69", "Shawred0", "Yourpop8",
    "BillyM2k", "Bluntz_Capital", "pmarca", "Ashcryptoreal"
]

def fetch_recent_tweets_from_users(usernames, max_tweets=10, minutes=5):
    relevant_tweets = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    for username in usernames:
        try:
            user = client.get_user(username=username)
            if user and user.data:
                user_id = user.data.id
                tweets = client.get_users_tweets(
                    id=user_id,
                    max_results=max_tweets,
                    tweet_fields=["created_at","author_id","text"],
                    exclude=["retweets","replies"]
                )
                if tweets and tweets.data:
                    for tw in tweets.data:
                        tweet_time = tw.created_at
                        if tweet_time and tweet_time > cutoff_time:
                            relevant_tweets.append({'tweet': tw, 'username': username})
        except Exception as e:
            print(f"Error fetching tweets for {username}: {e}")
    print("Relevant tweets retrieved:")
    for t in relevant_tweets:
        print(f"- {t['tweet'].text} (by @{t['username']})")
    return relevant_tweets

def is_relevant_tweet(tweet_text):
    check_prompt = (
        "Please carefully analyze the following tweet and determine whether it is related to any of the following domains: (1) cryptocurrency or blockchain technology (including memecoins, tokens like DOGE, BTC, ..., shitcoins, solana, bitcoin, any blockchain or any type of crypto token), (2) political figures or issues specifically involving well-known leaders such as Trump, Putin, Zelensky, or Macron, or (3) artificial intelligence, including AI agents, machine learning models, or other AI-related topics.\n\n"
        f"Tweet: {tweet_text}"
    )
    response = claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=10,
        messages=[
            {"role": "user", "content": check_prompt}
        ]
    )
    answer = response.content[0].text.strip().lower()
    return "yes" in answer

def pick_tweet_to_respond(tweets):
    if not tweets:
        return None
    return random.choice(tweets)

def can_respond_to_user(username, existing_data, max_per_hour=2):
    current_time = datetime.now(timezone.utc)
    cutoff_time = current_time - timedelta(hours=1)
    count = 0
    for entry in existing_data:
        if entry.get('username') == username:
            timestamp_str = entry.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                    if timestamp > cutoff_time:
                        count += 1
                        if count >= max_per_hour:
                            return False
                except ValueError:
                    print(f"Invalid timestamp format: {timestamp_str}")
    return count < max_per_hour

API_KEY_SUBTITLES = os.environ["SUBTITLES_API_KEY"]
TEMPLATE_ID = os.environ["SUBTITLES_TEMPLATE_ID"]
LANGUAGE = "en"

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
4. Each word must be separated by a space

Expected format example:
Word1 Word2 Word3 Word4"""
            }
        ],
        "max_tokens": 4096
    }
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        if response.status_code != 200:
            print("Claude API error:", response.text)
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
        print(f"Error during correction with Claude: {e}")
        return None

def upload_video(file_path, api_key):
    url = "https://api.zapcap.ai/videos"
    headers = {"X-Api-Key": api_key}
    with open(file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, headers=headers, files=files)
    if response.status_code != 201:
        print("Error uploading:", response.text)
        return None
    video_id = response.json().get('id')
    print(f"Video uploaded. ID: {video_id}")
    return video_id

def create_transcription_task(video_id, template_id, language='en'):
    url = f"https://api.zapcap.ai/videos/{video_id}/task"
    headers = {"Content-Type": "application/json", "X-Api-Key": API_KEY_SUBTITLES}
    payload = {"templateId": template_id, "language": language, "autoApprove": True}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 201:
        print("Error creating task:", response.text)
        return None
    task_id = response.json().get('taskId')
    print(f"Transcription task created. ID: {task_id}")
    return task_id

def check_task_status(video_id, task_id):
    url = f"https://api.zapcap.ai/videos/{video_id}/task/{task_id}"
    headers = {"X-Api-Key": API_KEY_SUBTITLES}
    retry_count = 0
    max_retries = 30
    while retry_count < max_retries:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error checking status:", response.text)
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
    url = f"https://api.zapcap.ai/videos/{video_id}/task/{task_id}/transcript"
    headers = {"X-Api-Key": API_KEY_SUBTITLES}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error getting transcript:", response.text)
        return None
    return response.json()

def create_subtitle_task(video_id, transcript):
    url = f"https://api.zapcap.ai/videos/{video_id}/task"
    headers = {"Content-Type": "application/json", "X-Api-Key": API_KEY_SUBTITLES}
    payload = {
        "templateId": TEMPLATE_ID,
        "transcript": transcript,
        "autoApprove": True,
        "language": LANGUAGE
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 201:
        print("Error creating subtitle task:", response.text)
        return None
    task_id = response.json().get('taskId')
    print(f"Subtitle task created. ID: {task_id}")
    return task_id

def process_chosen_tweet(chosen_tweet_dict):
    tweet = chosen_tweet_dict['tweet']
    username = chosen_tweet_dict['username']
    tweet_id = tweet.id
    tweet_text = tweet.text
    existing_data = load_existing_tweet_data()
    if not can_respond_to_user(username, existing_data):
        print(f"User @{username} has reached the response limit in the past hour. Skipping tweet {tweet_id}.")
        return
    if is_tweet_responded(str(tweet_id), existing_data):
        print(f"Already answered tweet {tweet_id}. Skipping")
        return
    current_tweet_url = get_tweet_url(tweet_id, client)
    image_analysis = image_analyzer.process_tweet_image(current_tweet_url)
    if not image_analysis:
        tweet_details = client.get_tweet(tweet_id, expansions='referenced_tweets.id', tweet_fields=['author_id','created_at','referenced_tweets'])
        if tweet_details and tweet_details.includes and 'tweets' in tweet_details.includes:
            main_referenced = tweet_details.data.get('referenced_tweets', [])
            quoted_id = None
            for ref in main_referenced:
                if ref['type'] == 'quoted':
                    quoted_id = ref['id']
                    break
            if quoted_id:
                quoted_tweet_url = get_tweet_url(quoted_id, client)
                image_analysis = image_analyzer.process_tweet_image(quoted_tweet_url)
    context = tweet_text
    if image_analysis:
        context += "\nImage context: " + image_analysis
    response_text = generate_text_with_claude(context, image_analysis if image_analysis else None)
    summary_text = generate_summary(response_text, tweet_text)
    print(summary_text)
    audio_url = generate_audio_with_eleven_labs(response_text, voice_id, elevenlabs_api_key)
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
                    video_id = upload_video(local_video_path, API_KEY_SUBTITLES)
                    if not video_id:
                        raise Exception("Failed to upload to subtitles")
                    transcription_task_id = create_transcription_task(video_id, TEMPLATE_ID)
                    if not transcription_task_id:
                        raise Exception("Failed to create transcription task")
                    status, _ = check_task_status(video_id, transcription_task_id)
                    if not status:
                        raise Exception("Transcription task failed")
                    original_transcript = get_transcript(video_id, transcription_task_id)
                    if not original_transcript:
                        raise Exception("Failed to get transcript")
                    corrected_transcript = correct_transcript_with_claude(original_transcript, response_text)
                    if not corrected_transcript:
                        raise Exception("Failed to correct transcript")
                    subtitle_task_id = create_subtitle_task(video_id, corrected_transcript)
                    if not subtitle_task_id:
                        raise Exception("Failed to create subtitle task")
                    status, final_video_url = check_task_status(video_id, subtitle_task_id)
                    if not status or not final_video_url:
                        raise Exception("Failed to get final video URL")
                    subtitled_video_path = "video_response_subtitled.mp4"
                    with requests.get(final_video_url, stream=True) as r:
                        r.raise_for_status()
                        with open(subtitled_video_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    tweet_id_video = upload_and_post_video_v2(subtitled_video_path, tweet_id, summary_text)
                    tweet_data = {
                        "username": username,
                        "tweet_text_received": tweet_text,
                        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                        "bot_response": response_text,
                        "tweet_id_video_posted": tweet_id_video,
                        "tweet_id_tagging_bot": str(tweet_id)
                    }
                    save_tweet_data_to_json(tweet_data)
                    os.remove(local_video_path)
                    os.remove(subtitled_video_path)
                except Exception as e:
                    print(f"Error in subtitle process: {e}")
            else:
                print("Failed to retrieve video URL.")
        else:
            print("Failed to create avatar.")
    else:
        print("Failed to synthesize audio.")

from tweepy.errors import TooManyRequests, TweepyException

MAX_RESPONSES_PER_CYCLE = 5
DELAY_BETWEEN_RESPONSES = 2

while True:
    try:
        print("Checking recent tweets from predefined user list...")
        tweets = fetch_recent_tweets_from_users(user_list, max_tweets=10, minutes=10)
        relevant_tweets = [tw for tw in tweets if is_relevant_tweet(tw['tweet'].text)]
        if relevant_tweets:
            print(f"Found {len(relevant_tweets)} relevant tweet(s).")
            for i, tweet_dict in enumerate(relevant_tweets):
                if i >= MAX_RESPONSES_PER_CYCLE:
                    print("Reached maximum number of responses for this cycle.")
                    break
                tweet = tweet_dict['tweet']
                username = tweet_dict['username']
                print(f"Processing tweet {i+1} from @{username}: {tweet.text}")
                process_chosen_tweet(tweet_dict)
                time.sleep(DELAY_BETWEEN_RESPONSES)
        else:
            print("No relevant tweets found.")
        print("Waiting 300 seconds (5 minutes) before checking again...")
        time.sleep(300)
    except TooManyRequests as e:
        print("Rate limit exceeded. Waiting for reset...")
        if hasattr(e, 'retry_after'):
            wait_time = e.retry_after
        else:
            wait_time = 900
        print(f"Sleeping for {wait_time} seconds.")
        time.sleep(wait_time)
    except TweepyException as e:
        print(f"Tweepy error: {e}")
        print("Waiting 60 seconds before retrying...")
        time.sleep(60)
    except Exception as e:
        print(f"Unexpected error: {e}. Retrying in 5-8 minutes...")
        delay = random.randint(300, 480)
        time.sleep(delay)
