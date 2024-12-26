import requests
import anthropic
import tweepy
from requests_oauthlib import OAuth1
import time
import os
from datetime import datetime, timedelta
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
                                    "text": "Describe precisely what you see in this image. Be detailed and objective. And give your opinion. If there are numbers associated to some token or nft, regroup the together and describe everything. If it's a chart, check if there is a big red candle at the end, means it's a rug or scam but if there is a big green candle, it's pumping so it's bullish so always say if it's a bullish chart, bearish or neutral. If it's not a chart, don't talk about chart. Always describe everything with precision"
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

def search_tweets(query, since_id=None, include_replies=True):
    print("Searching for tweets containing:", query)
    url = "https://api.twitter.com/2/tweets/search/recent"
    tw_auth = create_auth()
    params = {
        'query': '@lea_gpt -is:retweet',
        'max_results': 100,
        'since_id': since_id,
        'tweet.fields': 'author_id,conversation_id,referenced_tweets,created_at,in_reply_to_user_id'
    }
    response = requests.get(url, auth=tw_auth, params=params)
    if response.status_code != 200:
        print(f"Request returned an error: {response.status_code} {response.text}")
        return None
    if not response.text:
        print("No content received from API.")
        return None
    try:
        tweets = response.json()
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return None
    if 'data' not in tweets:
        print("No tweets found or unexpected response format.")
        return None
    return tweets['data']

def filter_recent_engaging_tweets(tweets, time_window_minutes=10, fallback_time_window_minutes=60):
    current_time = datetime.utcnow()
    recent_tweets = []
    for tweet in tweets:
        tweet_time = datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if current_time - tweet_time <= timedelta(minutes=time_window_minutes):
            recent_tweets.append(tweet)
    if len(recent_tweets) == 0:
        print(f"No tweets found in the last {time_window_minutes} minutes, extending search to {fallback_time_window_minutes} minutes.")
        for tweet in tweets:
            tweet_time = datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if current_time - tweet_time <= timedelta(minutes=fallback_time_window_minutes):
                recent_tweets.append(tweet)
    return recent_tweets

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
        os.environ["CHARACTER_CONTEXT_LINE_42"] +
        os.environ["CHARACTER_CONTEXT_LINE_43"] +
        os.environ["CHARACTER_CONTEXT_LINE_44"] +
        os.environ["CHARACTER_CONTEXT_LINE_45"] +
        os.environ["CHARACTER_CONTEXT_LINE_46"] +
        os.environ["CHARACTER_CONTEXT_LINE_47"] +
        os.environ["CHARACTER_CONTEXT_LINE_48"]
    )
    if image_description:
        full_prompt = (
            f"{character_context}\n\n{prompt}\n\n"
            f"Note: A detailed analysis of the image is available. Use this analysis if relevant and when asked or to support your answer, provide image elements. If someone asks to explain or describe the picture, do it with some precision. Only if needed use the image analysis else don't use it.\n\n"
            f"Image analysis:\n{image_description}"
        )
    else:
        full_prompt = f"{character_context}\n{prompt}"
    response = claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
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
            existing_data = json.load(file)
    else:
        existing_data = []
    data["main_tweet_id"] = data.get("main_tweet_id", "unknown")
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

def is_tweet_responded(main_tweet_id, existing_data):
    if not existing_data:
        return False
    for tweet in existing_data:
        if tweet.get("main_tweet_id") == main_tweet_id:
            return True
    return False

def get_thread_tweets(tweet_id):
    tweet_data = client.get_tweet(tweet_id, tweet_fields="conversation_id,author_id,text,referenced_tweets")
    conversation_id = tweet_data.data["conversation_id"]
    main_tweet_data = client.get_tweet(conversation_id, tweet_fields="text,author_id,referenced_tweets")
    main_tweet = main_tweet_data.data
    all_tweets = client.search_recent_tweets(
        query=f"conversation_id:{conversation_id}",
        tweet_fields="text,author_id,referenced_tweets",
        max_results=100
    )
    tweet_list = [main_tweet]
    if all_tweets.data:
        for tw in all_tweets.data:
            if tw.id != main_tweet.id:
                tweet_list.append(tw)
    sorted_tweets = sorted(tweet_list, key=lambda x: int(x.id))
    return sorted_tweets

def get_thread_context(tweet_id):
    sorted_tweets = get_thread_tweets(tweet_id)
    context = []
    for t in sorted_tweets:
        context.append(t.text)
        if t.id == tweet_id:
            break
    return " ".join(context)

claude_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def generate_summary(response_text, thread_context=None):
    new_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    if thread_context:
        prompt = f"Tweet context: {thread_context}\nLea's response: {response_text}"
    else:
        prompt = f"You are Lea and you just create a punchy and provocative tweet based on this text you made or a fun tweet based on this text you made: {response_text}"
    prompt += """
    Requirements:
    1. Maximum 10 words
    2. Must be provocative, funny, or intriguing, it depends of the answer
    3. Use @mentions if text talks about a specific person else don't use it
    4. DO NOT use phrases like "Here's", "Discover", "Watch"
    5. Don't summarize content, create suspense instead
    6. DO NOT use emoji
    7. Return ONLY the tweet text, with no explanations or comments
    8. Write AS Lea, not ABOUT Lea
    
    Example formats:
    - For clashes/criticism: "@person better watch your back "
    - For advice/info: "Your boss is lying "
    - For predictions: "Bitcoin 100k tomorrow "
    """
    try:
        response = new_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=60,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        tweet = response.content[0].text.strip().split('\n')[0]
        return tweet
    except Exception as e:
        print(f"Error generating tweet: {e}")
        return ""

def is_main_tweet_by_lea(tweet):
    conversation_id = tweet.get('conversation_id')
    if not conversation_id:
        return False
    lea_user_id = "1850273360724348928"
    main_tweet = client.get_tweet(conversation_id, tweet_fields='author_id')
    if main_tweet and main_tweet.data and main_tweet.data.get('author_id') == lea_user_id:
        return True
    return False

def is_direct_mention(tweet):
    return '@lea_gpt' in tweet.get('text', '').lower()

def count_words_excluding_tags_and_emojis(text):
    text_without_tags = re.sub(r'@\w+', '', text)
    text_without_emojis = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text_without_tags)
    cleaned_text = re.sub(r'\s+', ' ', text_without_emojis).strip()
    return len(cleaned_text.split())

def get_tweet_url(tweet_id, client):
    tweet_data = client.get_tweet(tweet_id, tweet_fields="author_id")
    author_id = tweet_data.data["author_id"]
    user_data = client.get_user(id=author_id, user_fields="username")
    username = user_data.data["username"]
    return f"https://x.com/{username}/status/{tweet_id}"

SUBTITLES_API_KEY = os.environ["SUBTITLES_API_KEY"]
TEMPLATE_ID = os.environ["SUBTITLES_TEMPLATE_ID"]
LANGUAGE = "en"
CLAUDE_API_KEY = os.environ["ANTHROPIC_API_KEY"]

def correct_transcript_with_claude(original_transcript, reference_text):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": CLAUDE_API_KEY,
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
    url = "https://api.subtitles.ai/videos"
    headers = {"X-Api-Key": api_key}
    with open(file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, headers=headers, files=files)
    if response.status_code != 201:
        print("Error uploading video:", response.text)
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
        print("Error creating transcription task:", response.text)
        return None
    task_id = response.json().get('taskId')
    print(f"Transcription task created. ID: {task_id}")
    return task_id

def check_task_status(video_id, task_id):
    url = f"https://api.subtitles.ai/videos/{video_id}/task/{task_id}"
    headers = {"X-Api-Key": SUBTITLES_API_KEY}
    retry_count = 0
    max_retries = 30
    last_status = None
    while retry_count < max_retries:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error checking status:", response.text)
            return None, None
        data = response.json()
        status = data.get('status', '').lower()
        if status != last_status:
            print(f"Task status: {status}")
            last_status = status
        if status == "completed":
            return status, data.get('downloadUrl')
        elif status in ["failed", "error"]:
            print("Task failed.")
            return None, None
        retry_count += 1
        time.sleep(10)
    print("Max retries reached.")
    return None, None

def get_transcript(video_id, task_id):
    url = f"https://api.subtitles.ai/videos/{video_id}/task/{task_id}/transcript"
    headers = {"X-Api-Key": SUBTITLES_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error getting transcript:", response.text)
        return None
    transcript = response.json()
    print("Transcript retrieved successfully.")
    return transcript

def create_subtitle_task(video_id, transcript):
    url = f"https://api.subtitles.ai/videos/{video_id}/task"
    headers = {"Content-Type": "application/json", "X-Api-Key": SUBTITLES_API_KEY}
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

lea_user_id = "1850273360724348928"

def process_tweet(tweet):
    tweet_id = tweet['id']
    tweet_text = tweet.get('text')
    author_id = tweet.get('author_id')
    if '@lea_gpt' not in tweet.get('text', '').lower():
        print(f"Tweet {tweet['id']} does not mention @lea_gpt. Ignoring...")
        return
    if tweet.get('in_reply_to_user_id') == lea_user_id:
        print(f"Tweet {tweet_id} is a reply to a Lea tweet. Ignored.")
        return
    if author_id == lea_user_id:
        print("Ignore tweets from the bot itself.")
        return
    if count_words_excluding_tags_and_emojis(tweet_text) < 1:
        print(f"Tweet {tweet_id} ignored due to having less than 1 word (excluding tags).")
        return
    if is_main_tweet_by_lea(tweet):
        print(f"Tweet {tweet_id} is part of a thread where the main tweet is from Lea. Ignoring...")
        return
    if 'referenced_tweets' in tweet:
        referenced_tweet_id = tweet['referenced_tweets'][0]['id']
        original_tweet = client.get_tweet(referenced_tweet_id)
        if original_tweet.data['author_id'] != lea_user_id and '@lea_gpt' not in tweet_text:
            print(f"Tweet {tweet_id} is not a direct mention to Lea. Ignoring...")
            return
    sorted_tweets = get_thread_tweets(tweet_id)
    main_tweet = sorted_tweets[0]
    main_tweet_id = main_tweet.id
    existing_data = load_existing_tweet_data()
    if is_tweet_responded(main_tweet_id, existing_data):
        print(f"Lea already replied to the main tweet {main_tweet_id}. Skipping...")
        return
    print(f"Tweet received that mentioned the bot: {tweet_text}")
    print(f"Main tweet ID: {main_tweet_id}")
    context = get_thread_context(tweet_id)
    context += " " + tweet_text
    current_tweet_url = get_tweet_url(tweet_id, client)
    image_analysis = image_analyzer.process_tweet_image(current_tweet_url)
    if not image_analysis and 'referenced_tweets' in tweet:
        for ref in tweet['referenced_tweets']:
            if ref['type'] == 'replied_to':
                parent_tweet_id = ref['id']
                parent_tweet_url = get_tweet_url(parent_tweet_id, client)
                image_analysis = image_analyzer.process_tweet_image(parent_tweet_url)
                if image_analysis:
                    print("Image found in the parent tweet.")
                break
    if image_analysis:
        print("Result of image analysis :")
        print(image_analysis)
        context += "\nImage context: " + image_analysis
    thread_context = get_thread_context(tweet_id)
    response_text = generate_text_with_claude(context, image_analysis if image_analysis else None)
    summary_text = generate_summary(response_text, thread_context)
    print("summary:")
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
                    video_id = upload_video(local_video_path, SUBTITLES_API_KEY)
                    if not video_id:
                        raise Exception("Failed to upload video to subtitles")
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
                        "main_tweet_id": main_tweet_id,
                        "tweet_text_received": tweet_text,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                        "bot_response": response_text,
                        "tweet_id_video_posted": tweet_id_video,
                        "tweet_id_tagging_bot": tweet_id
                    }
                    save_tweet_data_to_json(tweet_data)
                    os.remove(local_video_path)
                    os.remove(subtitled_video_path)
                except Exception as e:
                    print(f"Error in subtitle process: {e}")
                    tweet_id_video = upload_and_post_video_v2(local_video_path, tweet_id, summary_text)
                    os.remove(local_video_path)
            else:
                print("Failed to retrieve video URL.")
        else:
            print("Failed to create avatar.")
    else:
        print("Failed to synthesize audio.")

processed_main_tweet_ids = set()
last_processed_id = None

while True:
    try:
        print("Checking for new tweets...")
        tweets = search_tweets("@lea_gpt", since_id=last_processed_id)
        if tweets:
            filtered_tweets = [tweet for tweet in tweets if is_direct_mention(tweet)]
            max_id_this_round = None
            for tweet in filtered_tweets:
                tweet_id = tweet['id']
                if max_id_this_round is None or int(tweet_id) > int(max_id_this_round):
                    max_id_this_round = tweet_id
                process_tweet(tweet)
            if max_id_this_round:
                last_processed_id = max_id_this_round
        else:
            print("No relevant tweets found.")
        delay = random.randint(15, 30)
        print(f"Waiting for {delay} seconds before checking again...")
        time.sleep(delay)
    except Exception as e:
        print(f"Error encountered: {e}. Retrying in 5-8 minutes...")
        delay = random.randint(300, 480)
        time.sleep(delay)
