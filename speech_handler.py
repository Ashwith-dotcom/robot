import speech_recognition as sr
import time
import os
import playsound
import requests
import boto3
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
from difflib import get_close_matches
from threading import Event

# Function to change animation state using file
def send_animation_state(state):
    try:
        with open("animation_state.txt", "w") as f:
            f.write(state)
    except Exception as e:
        print(f"Error writing animation state: {e}")

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize AWS Polly and Groq clients
polly = boto3.client('polly', region_name='ap-south-1')
client = Groq(api_key=GroqAPIKey)

# File paths
CHAT_LOG_PATH = "ChatLog.json"
UNANSWERED_QUERIES_PATH = "UnansweredQueries.json"

# Initialize messages
try:
    if os.path.exists(CHAT_LOG_PATH):
        with open(CHAT_LOG_PATH, "r") as f:
            content = f.read().strip()
            messages = load(f) if content else []
    else:
        messages = []
except Exception as e:
    print(f"Error loading chat history: {e}")
    messages = []

delivery_queries = {
    "who are you?": "I'm delivery robot, name Karna",
    "can i change my delivery location?": "Yes, but only before the robot reaches your vicinity. Please update your address in the app.",
    "can i schedule my delivery for a later time?": "Yes, you can select a preferred delivery time in the app before dispatch.",
    "can i track my order in real-time?": "Yes, use the tracking feature in our app to monitor the live location of your delivery.",
    "how do i open the delivery compartment?": "Enter the OTP sent to your registered phone or use Face Recognition if enabled.",
    "i didn't receive my otp. what should i do?": "Please check your phone/email. If the issue persists, request a new OTP in the app.",
    "can someone else collect my package?": "Yes, they will need to enter the OTP or verify using Face Recognition.",
    "what if someone tries to steal my package?": "The compartment is locked and only opens for authorized users. Security alerts are triggered for unauthorized access.",
    "can i pay on delivery?": "Currently, only pre-paid orders are supported for autonomous deliveries.",
    "can i cancel my order after dispatch?": "Cancellations after dispatch are not allowed. You can refuse delivery upon arrival.",
    "can i change the payment method?": "Payment methods cannot be changed once the order is dispatched.",
    "what happens if the robot breaks down?": "If the robot malfunctions, support will arrange for an alternative delivery or refund.",
    "what if the robot gets stuck?": "The robot will attempt to reroute or request assistance from a nearby operator.",
    "can i interact with the robot using voice?": "Yes, the robot supports basic voice commands for queries and assistance.",
    "how does the robot handle traffic and obstacles?": "It uses AI-powered sensors to navigate around obstacles and adjust routes dynamically.",
    "is the delivery compartment sanitized?": "Yes, our robots use UV-C sterilization to ensure hygiene before and after each delivery.",
    "can the robot handle multiple deliveries at once?": "Yes, the robot carries multiple packages in separate compartments and delivers them sequentially.",
}

def listen():
    print("🔊 Listening...")
    recognizer = sr.Recognizer()

    try:
        mic = sr.Microphone(device_index=0)
        
        with mic as source:
            print("🎤 Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎙️ Start speaking...")

            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)
                print("✅ Captured audio successfully!")

                text = recognizer.recognize_google(audio)
                print(f"🗣️ You said: {text}")
                return text.lower()

            except sr.WaitTimeoutError:
                print("⚠️ No speech detected (Timeout)")
                return None
            except sr.UnknownValueError:
                print("⚠️ Could not understand speech")
                return None
            except sr.RequestError as e:
                print(f"⚠️ Speech recognition error: {e}")
                return None

    except Exception as e:
        print(f"⚠️ Error initializing microphone: {e}")
        return None

def speak(text, voice="Joanna"):
    print(f"🗣️ Speaking: {text}...")

    try:
        print("🔄 Connecting to AWS Polly...")
        response = polly.synthesize_speech(
            Text=text,
            VoiceId=voice,
            OutputFormat='mp3',
            Engine='neural'
        )

        mp3_filename = "response.mp3"
        with open(mp3_filename, 'wb') as f:
            f.write(response['AudioStream'].read())

        os.system(f"mpg123 {mp3_filename}")

        os.remove(mp3_filename)
        print("✅ Finished speaking")

    except Exception as e:
        print(f"⚠️ Error in speak: {e}")

def get_delivery_response(query):
    query = query.lower().strip()
    matches = get_close_matches(query, delivery_queries.keys(), n=1, cutoff=0.7)
    return delivery_queries.get(matches[0], None) if matches else None

def save_chat_log():
    try:
        with open(CHAT_LOG_PATH, "w") as f:
            dump(messages, f, indent=4)
    except Exception as e:
        print(f"⚠️ Error saving chat log: {e}")

def save_unanswered_query(query):
    try:
        unanswered_queries = []
        if os.path.exists(UNANSWERED_QUERIES_PATH):
            with open(UNANSWERED_QUERIES_PATH, "r") as f:
                content = f.read().strip()
                unanswered_queries = load(f) if content else []

        unanswered_queries.append(query)

        with open(UNANSWERED_QUERIES_PATH, "w") as f:
            dump(unanswered_queries, f, indent=4)

        print(f"⚠️ Query saved for training: {query}")
    except Exception as e:
        print(f"⚠️ Error saving unanswered query: {e}")

def get_groq_response(query):
    messages.append({"role": "user", "content": query})

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
        top_p=1,
        stream=True,
        stop=None
    )

    answer = "".join(chunk.choices[0].delta.content for chunk in completion 
                    if chunk.choices[0].delta.content)    
    messages.append({"role": "assistant", "content": answer})
    save_chat_log()
    return answer

def process_query(query):
    query = query.lower()

    delivery_answer = get_delivery_response(query)
    if delivery_answer:
       response = delivery_answer
    else:
        response = get_groq_response(query)
        if "I don't know" in response or "I couldn't find" in response:
            save_unanswered_query(query)

    messages.append({"role": "user", "content": query})
    messages.append({"role": "assistant", "content": response})
    save_chat_log()

    return response

def main():
    should_exit = False
    try:
        print("🔄 Initializing speech handler...")
        
        # Initial greeting
        try:
            greeting = "Hello! How can I help you?"
            print(f"🗣️ Attempting to speak greeting: {greeting}")
            send_animation_state('answering')
            speak(greeting)
            send_animation_state('idle')
            print("✅ Greeting complete")
        except Exception as e:
            print(f"❌ Error speaking greeting: {e}")

        print("✅ Initialization complete. Entering main loop...")

        while not should_exit:
            try:
                print("🔊 Listening for user input...")
                send_animation_state('listening')
                user_input = listen()

                if user_input:
                    if user_input.lower() in ["exit", "quit", "stop", "bye"]:
                        print("👋 Exiting chatbot...")
                        send_animation_state('last')
                        should_exit = True
                        break

                    print(f"🎤 User said: {user_input}")
                    send_animation_state('thinking')
                    response = process_query(user_input)
                    print(f"🤖 Response: {response}")
                    send_animation_state('answering')
                    speak(response)
                    send_animation_state('idle')
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                send_animation_state('idle')

    except Exception as e:
        print(f"❌ Critical error in main function: {e}")
    finally:
        print("🔻 Shutting down speech handler...")

if __name__ == "__main__":
    main()