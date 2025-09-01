import os
import pyaudio
import wave
import io
import requests
import base64
from google.cloud import texttospeech
import re
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Set your API Key for Google Cloud services
API_KEY = os.getenv("GOOGLE_API_KEY")  # Get API key from env variables

# List of Tamil station names
CHENNAI_METRO_STATIONS = {
    "ag-dms", "anna nagar east", "anna nagar tower", "arignar anna alandur", "alandur",
    "arumbakkam", "ashok nagar", "chennai international airport", "airport", "egmore",
    "ekkatuthangal", "government estate", "guindy", "high court", "kaladipet metro",
    "kilpauk", "koyambedu", "puratchi thalaivi dr. j. jayalalithaa cmbt", "cmbt",
    "lic", "little mount", "mannadi", "meenambakkam", "nandanam", "nehru park",
    "new washermenpet metro", "ota - nanganallur road", "pachaiyappas college",
    "puratchi thalaivar dr. m.g. ramachandran central", "central",
    "saidapet", "shenoy nagar", "st. thomas mount", "teynampet",
    "thiagaraya college metro", "thirumangalam", "thiruvotriyur metro",
    "thiruvotriyur theradi metro", "thousand lights", "tollgate metro",
    "tondiarpet metro", "vadapalani", "washermanpet", "wimco nagar depot",
    "wimco nagar metro"
}

# Google Cloud Speech-to-Text API
def record_audio(filename="input.wav", record_seconds=5):
    """Record audio from the microphone and save it to a file."""
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    sample_rate = 16000
    audio = pyaudio.PyAudio()

    print("Recording...")
    stream = audio.open(format=format, channels=channels,
                        rate=sample_rate, input=True,
                        frames_per_buffer=chunk)
    frames = []

    for _ in range(0, int(sample_rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    print("Recording complete.")
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the audio to a file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(format))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

def transcribe_speech(filename="input.wav"):
    """Transcribe the given audio file using Google Cloud Speech-to-Text."""
    try:
        with open(filename, "rb") as audio_file:
            content = audio_file.read()

        encoded_audio = base64.b64encode(content).decode('utf-8')
        url = f"https://speech.googleapis.com/v1p1beta1/speech:recognize?key={API_KEY}"

        headers = {"Content-Type": "application/json"}
        data = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": "en-GB",  # Switch from "en-IN" to "en-GB"
                "speechContexts": [
                    # Tamil Metro Station Names (Higher Priority)
                    {
                        "phrases": [
                            "AG-DMS",
                            "Anna Nagar East",
                            "Anna Nagar Tower",
                            "Arignar Anna Alandur",
                            "Arumbakkam",
                            "Ashok Nagar",
                            "Chennai International Airport",
                            "Egmore",
                            "Ekkatuthangal",
                            "Government Estate",
                            "Guindy",
                            "High Court",
                            "Kaladipet Metro",
                            "Kilpauk",
                            "Koyambedu",
                            "LIC",
                            "Little Mount",
                            "Mannadi",
                            "Meenambakkam",
                            "Nandanam",
                            "Nehru Park",
                            "New Washermenpet Metro",
                            "OTA - Nanganallur Road",
                            "Pachaiyappas College",
                            "Puratchi Thalaivar Dr. M.G. Ramachandran Central",
                            "Puratchi Thalaivi Dr. J. Jayalalithaa CMBT",
                            "Saidapet",
                            "Shenoy Nagar",
                            "St. Thomas Mount",
                            "Teynampet",
                            "Thiagaraya College Metro",
                            "Thirumangalam",
                            "Thiruvotriyur Metro",
                            "Thiruvotriyur Theradi Metro",
                            "Thousand Lights",
                            "Tollgate Metro",
                            "Tondiarpet Metro",
                            "Vadapalani",
                            "Washermanpet",
                            "Wimco Nagar Depot",
                            "Wimco Nagar Metro"
                        ],
                        "boost": 20  # Prioritize Tamil metro stations
                    },
                    # Common English Travel Modes (Lower Priority)
                    {
                        "phrases": [
                            "one way", "one-way", "1 way", "1-way", "two way", 
                            "two-way", "2 way", "2-way", "round trip", "roundtrip"
                            "single trip", "double trip", "single journey"
                        ],
                        "boost": 15  # Boost but lower than metro stations
                    },
                    # Explicitly handle number of tickets in phrases
                    {
                        "phrases": [
                            "a ticket", "one ticket", "two tickets", "three tickets", "four tickets",
                            "five tickets", "six tickets", "book ticket", "book tickets"
                        ],
                        "boost": 15  # Ensure numbers are correctly transcribed
                    },
                    {
                        "phrases": [
                            "yes", "no", "source", "origin", "destination"
                        ],
                        "boost": 15 # Lower priority for confirmations
                    }
                ]
            },
            "audio": {
                "content": encoded_audio
            }
        }

        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            transcript = result['results'][0]['alternatives'][0]['transcript']
            print(f"Transcribed text: {transcript}")
            return transcript
        else:
            print(f"Error transcribing audio: {response.text}")
            return ""

    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""


def extract_entities(text):
    """Use Google Cloud NLP API to analyze and extract entities with station correction."""
    try:
        url = f"https://language.googleapis.com/v1/documents:analyzeEntities?key={API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {
            "document": {
                "type": "PLAIN_TEXT",
                "content": text
            }
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            entities = {entity["name"]: entity["type"] for entity in result["entities"]}
            
            # 🔹 Manual Fix: Ensure Metro Station Names Are Correctly Classified as LOCATION
            for word in text.lower().split():
                for station in CHENNAI_METRO_STATIONS:
                    if word in station:
                        entities[station] = "LOCATION"

            print("Extracted Entities:", entities)
            return entities
        else:
            print(f"Error in NLP API: {response.text}")
            return {}

    except Exception as e:
        print(f"Error in NLP processing: {e}")
        return {}
        

def text_to_speech_live(text):
    """Convert the text response to speech using Google Text-to-Speech and play live."""
    if not text:
        print("No valid text for Text-to-Speech.")
        return
    
    try:
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={API_KEY}"

        headers = {"Content-Type": "application/json"}
        data = {
            "input": {
                "text": text
            },
            "voice": {
                "languageCode": "en-US",
                "ssmlGender": "NEUTRAL"
            },
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "speakingRate": 1.5  # Adjust speech rate here
            }
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            audio_content = response.json().get("audioContent")
            play_audio(audio_content)
        else:
            print(f"Error in Text-to-Speech: {response.text}")

    except Exception as e:
        print(f"Error in Text-to-Speech: {e}")

def play_audio(audio_content):
    """Play audio directly from raw data."""
    try:
        audio_stream = io.BytesIO(base64.b64decode(audio_content))
        p = pyaudio.PyAudio()

        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        output=True)

        stream.write(audio_stream.read())
    except Exception as e:
        print(f"Error in playing audio: {e}")

import re

def extract_ticket_and_mode(text):
    """Extract number of tickets and travel mode from the sentence."""
    ticket_count = None
    travel_mode = None

    # Mapping of number words to their numeric values
    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "a": 1, "an": 1  # Handling "a ticket" or "an ticket"
    }

    # Search for numeric ticket count (e.g., "2 tickets")
    match = re.search(r'\b(\d+)\s*tickets?\b', text, re.IGNORECASE)
    if match:
        ticket_count = int(match.group(1))
    else:
        # Search for standalone numbers (both numeric and word versions)
        match_single_number = re.search(r'\b(1|2|3|4|5|6|one|two|three|four|five|six|a|an)\b', text, re.IGNORECASE)
        if match_single_number:
            word_or_number = match_single_number.group(1).lower()
            ticket_count = number_words.get(word_or_number, int(word_or_number) if word_or_number.isdigit() else None)

    # Handling possible misinterpretation of "two" as "to"
    if ticket_count is None and re.search(r'\bto\b', text, re.IGNORECASE):
        ticket_count = 2  # Assign "to" as 2 if no valid number is found

    # Determine travel mode (One-way or Two-way)
    if re.search(r'(1\s*-?\s*way|one\s*-?\s*way|single\s*trip|single)', text, re.IGNORECASE):
        travel_mode = "one-way"
    elif re.search(r'(round\s*trip|two\s*-?\s*way|2\s*-?\s*way|double\s*trip|double)', text, re.IGNORECASE):
        travel_mode = "two-way"

    return ticket_count, travel_mode


import re

def prompt_for_changes():
    """Handles prompting the user to specify what they want to change."""
    while True:
        text_to_speech_live("What would you like to change?")
        print("What would you like to change?")
        record_audio()
        text = transcribe_speech().lower()

        if "number of tickets" in text:
            return "tickets"
        elif "travel mode" in text:
            return "travel mode"
        elif "origin" in text or "source" in text:
            return "origin"
        elif "destination" in text:
            return "destination"
        else:
            text_to_speech_live("I am sorry but I didn't understand.")
            print("I am sorry but I didn't understand.")

def handle_summary_and_changes(from_location, to_location, ticket_count, travel_mode):
    """Handles booking summary and allows user to make changes."""
    changes_made = False  

    while True:
        response = f"From: {from_location}, To: {to_location}, Number of tickets: {ticket_count}, Travel mode: {travel_mode}"
        text_to_speech_live(response)
        print("Response:", response)

        if not changes_made:  
            text_to_speech_live("Would you like to make any changes to the booking details?")
            print("Would you like to make any changes to the booking details?")
            record_audio()
            text = transcribe_speech().lower()

            if "no" in text:
                text_to_speech_live("Your booking is confirmed. Thank you!")
                print("Final Booking Confirmed:", response)
                break
            elif "yes" in text:
                changes_made = True  

        while changes_made:
            change_type = prompt_for_changes()

            if change_type == "tickets":
                while True:
                    text_to_speech_live("How many tickets would you like to book?")
                    print("How many tickets would you like to book?")
                    record_audio()
                    text = transcribe_speech()
                    ticket_count, _ = extract_ticket_and_mode(text)

                    if ticket_count and ticket_count <= 6:
                        break
                    else:
                        text_to_speech_live("You can only book up to six tickets. Please provide a valid number.")
                        print("You can only book up to six tickets. Please provide a valid number.")

            elif change_type == "travel mode":
                while travel_mode not in ["one-way", "two-way"]:
                    text_to_speech_live("Is this a one-way or round trip?")
                    print("Is this a one-way or round trip?")
                    record_audio()
                    text = transcribe_speech()
                    _, travel_mode = extract_ticket_and_mode(text)

            elif change_type == "origin":
                from_location = None
                while not from_location:
                    text_to_speech_live("Please provide the origin location.")
                    print("Please provide the origin location.")
                    record_audio()
                    text = transcribe_speech()
                    entities = extract_entities(text)
                    for entity, entity_type in entities.items():
                        if entity_type == 'LOCATION':
                            from_location = entity

            elif change_type == "destination":
                to_location = None
                while not to_location:
                    text_to_speech_live("Please provide the destination location.")
                    print("Please provide the destination location.")
                    record_audio()
                    text = transcribe_speech()
                    entities = extract_entities(text)
                    for entity, entity_type in entities.items():
                        if entity_type == 'LOCATION':
                            to_location = entity

            # Provide an updated summary
            response = f"From: {from_location}, To: {to_location}, Number of tickets: {ticket_count}, Travel mode: {travel_mode}"
            text_to_speech_live(response)
            print("Updated Response:", response)

            # Ask if further changes are needed
            text_to_speech_live("Would you like to make any further changes?")
            print("Would you like to make any further changes?")
            record_audio()
            text = transcribe_speech().lower()

            if "no" in text:
                text_to_speech_live("Your booking is confirmed. Thank you!")
                print("Final Booking Confirmed:", response)
                return  # Exit function after confirmation


# To fix the locations entity extraction error
def extract_locations_from_text(text):
    """Extract from_location and to_location directly from the transcribed text."""
    match = re.search(r"from\s+(.*?)\s+to\s+(.*?)(?:\s|$)", text, re.IGNORECASE)
    if match:
        from_location = match.group(1).strip()
        to_location = match.group(2).strip()
        return from_location, to_location
    return None, None


def validate_and_correct_locations(text, extracted_entities):
    """
    Validate and correct the from_location and to_location based on the transcribed text.
    
    Arguments:
    text: The original transcribed text.
    extracted_entities: Locations extracted by NLP as a dictionary.
    
    Returns:
    Corrected from_location and to_location.
    """
    # Extract locations from text
    text_from_location, text_to_location = extract_locations_from_text(text)
    
    # Extract locations from NLP entities
    nlp_locations = [entity for entity, entity_type in extracted_entities.items() if entity_type == "LOCATION"]
    
    # If NLP provides locations, validate against the text order
    if len(nlp_locations) >= 2:
        # Compare with the text-based extraction
        if nlp_locations[0] != text_from_location or nlp_locations[1] != text_to_location:
            print(f"Mismatch detected. Correcting locations based on text.")
            return text_from_location, text_to_location
    
    # Default to NLP if locations match or no issue is detected
    return nlp_locations[0] if len(nlp_locations) > 0 else None, nlp_locations[1] if len(nlp_locations) > 1 else None


def process_input():
    try:
        from_location = None
        to_location = None
        ticket_count = None
        travel_mode = None

        record_audio()
        text = transcribe_speech()

        if text == "":
            print("No text received from the speech.")
            return

        # NLP entity extraction
        entities = extract_entities(text)
        ticket_count, travel_mode = extract_ticket_and_mode(text)

        # Validate and correct locations
        from_location, to_location = validate_and_correct_locations(text, entities)
        
        # Prompt user for missing data if necessary
        while not from_location:
            text_to_speech_live("Can you tell me the origin location?")
            print("Can you tell me the origin location?")
            record_audio()
            text = transcribe_speech()
            entities = extract_entities(text)
            for entity, entity_type in entities.items():
                if entity_type == 'LOCATION':
                    from_location = entity

        while not to_location:
            text_to_speech_live("Can you tell me the destination location?")
            print("Can you tell me the destination location?")
            record_audio()
            text = transcribe_speech()
            entities = extract_entities(text)
            for entity, entity_type in entities.items():
                if entity_type == 'LOCATION':
                    to_location = entity

        while not ticket_count or ticket_count > 6:
            if ticket_count and ticket_count > 6:
                text_to_speech_live("You can only book up to six tickets. Please provide a valid number of tickets.")
                print("You can only book up to six tickets. Please provide a valid number of tickets.")
                
            else:
                text_to_speech_live("How many tickets would you like to book?")
                print("How many tickets would you like to book?")
            record_audio()
            text = transcribe_speech()
            ticket_count, _ = extract_ticket_and_mode(text)

        while travel_mode not in ["one-way", "two-way"]:
            text_to_speech_live("Is this a one-way or round trip?")
            print("Is this a one-way or round trip?")
            record_audio()
            text = transcribe_speech()
            _, travel_mode = extract_ticket_and_mode(text)

        handle_summary_and_changes(from_location, to_location, ticket_count, travel_mode)

    except Exception as e:
        print(f"Error in processing input: {e}")

if __name__ == "__main__":
    process_input()

