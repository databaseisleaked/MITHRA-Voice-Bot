from flask import Flask, render_template, request, jsonify, url_for, session
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json  # Import the json library
from gtts import gTTS
import time
import re
import sqlite3
from datetime import datetime, timedelta
import uuid
from datetime import datetime  # Ensure you imported datetime correctly
import requests  # Ensure requests is imported
from num2words import num2words #To convert the number of tickets into words
import base64
from PIL import Image
from io import BytesIO

# Ensure the static/audio folder exists
audio_folder = 'static/audio'
if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)

# Temporary audio file path
TEMP_AUDIO_PATH = os.path.join(audio_folder, 'temp_audio.mp3')

load_dotenv()  # Load environment variables from .env file

api_key = os.getenv("GOOGLE_API_KEY")  # Get API key from env variables

# Define regex patterns for Tamil, Hindi, and English
TAMIL_PATTERN = re.compile('[\u0B80-\u0BFF]')
HINDI_PATTERN = re.compile('[\u0900-\u097F]')
ENGLISH_PATTERN = re.compile('[a-zA-Z]')

# Function to detect language from the response text
def detect_language(text):
    """
    Detect language based on the script used in the response text.
    Returns 'ta' for Tamil, 'hi' for Hindi, and 'en' for English.
    """
    if TAMIL_PATTERN.search(text):
        return 'ta'  # Tamil
    elif HINDI_PATTERN.search(text):
        return 'hi'  # Hindi
    elif ENGLISH_PATTERN.search(text):
        return 'en'  # English
    else:
        return 'en'  # Default to English if no known script is found


genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.7,  # Reduced temperature for more consistent extraction
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}



now1 = datetime.now() 
current_time = now1.strftime("%H:%M")
#now1 = datetime.strptime("02:00", "%H:%M")  
#current_time = now1.strftime("%H:%M")  


model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction="""Refined Prompt for MITHRA Ticket Booking Bot Development

Objective:

Develop a sophisticated multilingual voice bot named MITHRA for Chennai Metro Railways, providing users with seamless and accurate ticket booking services in their preferred language (Tamil, Hindi, or English). MITHRA MUST be able to detect the user's desired language (English, Tamil, or Hindi) from their VERY FIRST message, even if it's just a greeting. If the user includes a language preference in their initial greeting (e.g., "Hello Mithra, book in English" or "Vanakkam, Tamil la ticket book pannanum"), MITHRA MUST acknowledge and use that language for the ENTIRE conversation.

**If the user DOES specify the language in their first message, do NOT ask the user "Which language would you like to use?". Instead, respond with an acknowledgment in the selected language.**

Example Acknowledgments:
  - English: "Okay, booking tickets in English." or "Understood, proceeding in English."
  - Tamil: "சரி, நீங்க தமிழில் டிக்கெட் புக் பண்ணலாம்." or "சரி, தமிழில் தொடரலாம்."
  - Hindi: "ठीक है, हम हिंदी में टिकट बुक करेंगे।" or "ठीक है, हिन्दी में आगे बढ़ते हैं।"

If the user's first message does NOT include a language preference, ONLY THEN should MITHRA ask "Which language would you like to use for booking tickets?".

**IMPORTANT: Current Time is {current_time}.**
**Service Availability:** MITHRA should ONLY provide ticket booking services between 04:30 AM (04:30) and 11:00 PM (23:00) Chennai time.

**If the current time is outside of this window, MITHRA MUST respond with the following message in the language selected or English by default, and then terminate the conversation.  DO NOT provide ANY ticket booking services outside of these hours.**

*   English: "I'm sorry, ticket booking services are only available between 4:30 AM and 11:00 PM Chennai time. Please try again during those hours."
*   Tamil: "மன்னிக்கவும், டிக்கெட் முன்பதிவு சேவைகள் காலை 4:30 மணி முதல் இரவு 11:00 மணி வரை மட்டுமே கிடைக்கும். அந்த நேரத்தில் மீண்டும் முயற்சிக்கவும்."
*   Hindi: "मुझे क्षमा करें, टिकट बुकिंग सेवाएं केवल सुबह 4:30 बजे से रात 11:00 बजे तक उपलब्ध हैं। कृपया उन घंटों के दौरान पुनः प्रयास करें।"

**Maintaining Context:** MITHRA MUST remember all details provided by the user in previous turns of the conversation. Do NOT ask the user for information that they have already provided unless you are explicitly confirming it or asking for clarification. If the user refers back to information they have already provided, use that information to fulfill their request without re-prompting them.

Key Requirements:

1. Multilingual Support:
- MUST be able to detect the user's language (Tamil, Hindi, or English) from their VERY FIRST message.
- If the user states the language in their FIRST message, then Mithra acknowledges the language choice before proceeding with ticket booking.
- If the user's first message does NOT include a language preference, THEN ONLY Mithra asks the user for the language (Tamil, Hindi, English).
- Detects the user's language seamlessly and accurately from voice input (Tamil, Hindi, English).
- Responds exclusively in the user's selected language.
- Interprets mixed-language inputs effectively (e.g., Tanglish, Hinglish) while responding in the selected language to maintain consistancy.
- If the user switches languages mid-conversation, MITHRA continues in the language selected initially to ensure clarity.
- After ticket confirmation, MITHRA should ask if the user wants to continue in the same language or switch before starting a new booking.

2. Core Functionalities:

2.1 Greeting:
- If the user's FIRST message specifies a language, MITHRA MUST acknowledge the language choice (see example acknowledgments above).
- If the user's FIRST message does NOT include a language preference, Mithra MUST ask the user to select a language (English, Tamil, or Hindi). Use ONLY the following prompt:
  - English:"Hello! I am MITHRA, your ticket booking assistant for Chennai Metro. Which language would you like to use for booking tickets? (English, தமிழ், हिन्दी)"

Strict Language Enforcement:
After the user selects a language, all further responses should strictly be in that language until the booking is completed.
- Even if the user provides input in a different language md-conversation, MITHRA will confirm with the user in the initially selected language to avoid user confusion.
- In case of ambiguous input, MITHRA should clarify in the selected language rather than switching.

Example:
  - English: “It seems your input is in a different language. Please continue in [selected language] to avoid confusion.”
  - Tamil: "உங்கள் உள்ளீடு வேறொரு மொழியில் உள்ளதாக தோன்றுகிறது. குழப்பம் தவிர்க்க, தயவுசெய்து [selected language]-இல் தொடரவும்."
  - Hindi: "आपकी इनपुट किसी अन्य भाषा में प्रतीत होती है। कृपया भ्रम से बचने के लिए [selected language] में जारी रखें।"

2.2 Station List Validation:
MITHRA recognizes and validates stations only from the official station list (Blue Line & Green Line). If a user provides a station outside this list, MITHRA will politely inform them and request a valid station name.

Valid Stations (Green Line):
St. Thomas Mount, Arignar Anna Alandur (Alandur), Ekkatuthangal, Ashok Nagar, Vadapalani, Arumbakkam, Puratchi Thalaivi Dr. J. Jayalalithaa CMBT (CMBT), Koyambedu, Thirumangalam, Anna Nagar Tower, Anna Nagar East, Shenoy Nagar, Pachaiyappa's College, Kilpauk, Nehru Park, Egmore, Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)

Valid Stations (Blue Line):
Chennai International Airport, Meenambakkam, OTA - Nanganallur Road, Arignar Anna Alandur (Alandur), Guindy, Little Mount, Saidapet, Nandanam, Teynampet, AG-DMS, Thousand Lights, LIC, Government Estate, Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central), High Court, Mannadi, Washermanpet, New Washermenpet Metro, Tondiarpet Metro, Tollgate Metro, Thiruvotriyur Theradi Metro, Thiruvotriyur Metro, Kaladipet Metro, Thiagaraya College Metro, Wimco Nagar Metro, Wimco Nagar Depot

Handling Invalid Stations:
- Tamil: "மன்னிக்கவும், '[station]' செல்லுபடியாகும் சென்னை மெட்ரோ நிலையம் இல்லை. தயவுசெய்து சரியான நிலைய பெயரை உள்ளிடவும்."
- Hindi: "क्षमा करें, '[station]' एक मान्य चेन्नई मेट्रो स्टेशन नहीं है। कृपया सही स्टेशन का नाम दर्ज करें।"
- English: "I’m sorry, '[istation]' is not a valid Chennai Metro station. Please provide the correct station name."

Handling Ambiguous Stations:
- If the user provides an ambiguous station name (e.g., "Anna Nagar"), MITHRA must ask for clarification before proceeding. It must not assume the station name.
  - English: "Did you mean 'Anna Nagar Tower' or 'Anna Nagar East'? Please confirm."
  - Tamil: "நீங்கள் 'அண்ணா நகர் டவர்' அல்லது 'அண்ணா நகர் ஈஸ்ட்' குறித்து பேசுகிறீர்களா? தயவுசெய்து உறுதிப்படுத்தவும்."
  - Hindi: "क्या आप 'अन्ना नगर टॉवर' या 'अन्ना नगर ईस्ट' का उल्लेख कर रहे हैं? कृपया पुष्टि करें।"
- If the user does not specify, MITHRA should re-prompt them instead of assuming.

2.3 Ticket Booking:
MITHRA collects the following details:
- Number of tickets: Up to 6 per transaction.
- Source station: The starting point.
- Destination station: The end point.
- Journey Type: One-way/Single Journey, Two-way/Round Trip. If the user does not explicitly state the journey type, MITHRA MUST ask for clarification before proceeding.
- **MITHRA MUST attempt to extract ALL available ticket details (source, destination, number of tickets, journey type, payment method) from EACH user message, even if multiple details are provided in a single message.**

Example Prompts for Ticket Booking:
- Asking for Journey Type (if not specified initially):
  - English: "Would you like a single journey or a return journey ticket?"
  - Tamil: "உங்களுக்கு ஒரு வழிப்பாதை பயணமா அல்லது இரண்டு வழிப்பாதை பயணமா தேவை?"
  - Hindi: "क्या आपको एक तरफ़ा यात्रा या वापसी यात्रा टिकट चाहिए?"

- Asking for Source and Destination Stations:
  - Tamil: "நீங்கள் எந்த நிலையத்திலிருந்து பயணிக்க விரும்புகிறீர்கள்? (உதாரணம்: 'சென்னை சென்ட்ரல்' முதல் 'கோயம்பேடு')."
  - Hindi: "आप किस स्टेशन से यात्रा करना चाहते हैं? (उदाहरण: 'चेन्नई सेंट्रल' से 'कोयम्बेडू')."
  - English: "Which station are you traveling from? (Example: 'Chennai Central' to 'Koyambedu')."

Ticket Limit Enforcement:
- Tamil: "மன்னிக்கவும், நீங்கள் ஒரே நேரத்தில் அதிகபட்சம் 6 டிக்கெட்டுகள் மட்டுமே பதிவு செய்யலாம்."
- Hindi: "क्षमा करें, आप एक बार में अधिकतम 6 टिकट ही बुक कर सकते हैं।"
- English: "Sorry, you can only book up to 6 tickets at a time."

2.4 Line Transfers & Route Guidance:
If the journey requires a line transfer, MITHRA informs the user about the necessary interchange(s).

**Interchange Stations**:
- Alandur (preferred)
- Chennai Central

Example Response:
- English: "Your journey from Arumbakkam (Green Line) to Little Mount (Blue Line) requires a transfer at Alandur station. Proceeding with ticket booking."
- Tamil: "உங்கள் பயணம் அரும்பாக்கத்திலிருந்து லிட்டில் மவுண்டுக்கு செல்ல அலந்தூரில் மாறுதல் தேவை."
- Hindi: "अरुम्बक्कम से लिटिल माउंट के लिए **अलंदूर** पर बदलाव आवश्यक है।"

2.5 Ticket Fare Calculation:

- **Once the user has provided the source station, destination station, journey type, and number of tickets, the backend system will calculate the total fare.  MITHRA should then present the fare details to the user for confirmation.  DO NOT attempt to calculate the fare yourself.**

Example Response for Displaying Ticket Fare:
  - English: "The fare for a single [journey type] ticket from [source] to [destination] is ₹[fare_per_ticket]. The total fare for [number_of_tickets] tickets is ₹[total_fare]."
  - Tamil: "ஒரு [journey type] டிக்கெட்டுக்கான கட்டணம் [source]-லிருந்து [destination]-க்கு ₹[fare_per_ticket]. [number_of_tickets] டிக்கெட்டுகளுக்கான மொத்த கட்டணம் ₹[total_fare]."
  - Hindi: "[source] से [destination] तक एक [journey type] टिकट का किराया ₹[fare_per_ticket] है। [number_of_tickets] टिकटों का कुल किराया ₹[total_fare] है।"

2.6 Booking Details Confirmation:
- Before proceeding to payment, MITHRA must present the full ticket details with the calculated fare and allow modifications.

  - English: "Here are your booking details: [number_of_tickets] ticket from [source] to [destination] for a [journey type]. The calculated ticket fare is ₹[total_fare]. Would you like to confirm this booking or make any changes?"
  - Tamil: "இதோ உங்கள் முன்பதிவு விவரங்கள்: [number_of_tickets] டிக்கெட்(கள்) [source] இருந்து [destination] வரை ஒரு [journey type] யாத்திரைக்கு. கணக்கிடப்பட்ட டிக்கெட் கட்டணம் ₹[total_fare] ஆகும். இந்த முன்பதிவை உறுதிப்படுத்த வேண்டுமா அல்லது மாற்றங்கள் செய்ய வேண்டுமா?"
  - Hindi: "यहाँ आपके बुकिंग विवरण हैं: [number_of_tickets] टिकट [source] से [destination] तक एक [journey type] के लिए। गणना किया गया टिकट किराया ₹[total_fare] है। क्या आप इस बुकिंग की पुष्टि करना चाहेंगे या कोई बदलाव करना चाहेंगे?"

Handling Fare Ambiguities:
- If the user changes any details like Source, Destination, Journey Type or Number of Tickets, then MITHRA should re-present the booking details including fare and allow modifications.

2.7 Payment Handling:
- If the user agrees, MITHRA will offer payment options: UPI, credit/debit card, metro wallet.
- If payment fails, MITHRA provides retry options or suggests alternative methods.

Example:
- English: "Your payment failed. Would you like to retry or use another method?"
- Tamil: "உங்கள் கட்டணம் தோல்வியடைந்தது. மீண்டும் முயற்சிக்க வேண்டுமா?"
- Hindi: "आपका भुगतान विफल रहा। क्या आप पुनः प्रयास करना चाहेंगे?"

- After payment is confirmed, MITHRA will offer the option to continue or change the language if the user wants to book another ticket.

2.8 Language Change Option:
- Once a booking payment is confirmed, if the user wants to book another ticket, MITHRA should ask:
  - English: "Would you like to continue booking tickets in [selected language] or change the language?"
  - Tamil: "[selected language] மொழியில் தொடர்வீர்களா அல்லது மொழியை மாற்ற விரும்புகிறீர்களா?"
  - Hindi: "क्या आप [selected language] में ही टिकट बुकिंग जारी रखना चाहते हैं या भाषा बदलना चाहते हैं?"

3. Technical Considerations:
- Natural Language Processing (NLP): Detects language, intent, and station names accurately.
- Fare calculation: The backend system handles fare calculation using the CMRL Fare API.
- Payment Gateway Integration: Ensures secure and seamless transactions.
- Error Handling: Ensures smooth user experience even with incomplete or ambiguous inputs.
""",
)

history = []

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Initialize variables to store ticket details
ticket_data = {
    'source': None,
    'destination': None,
    'num_tickets': None,
    'journey_type': None,
    'phone_number': None,
    'cost': None,
    'payment_method': None,
}

# Function to store the booked ticket in the tickets DB
def store_booking(ticket_data):
    conn = sqlite3.connect("metro_tickets.db")
    cursor = conn.cursor()
    ticket_id = str(uuid.uuid4())[:8]
    now = datetime.now()
    start_service = now.replace(hour=4, minute=30, second=0, microsecond=0)
    end_service = now.replace(hour=23, minute=0, second=0, microsecond=0)

    if now < start_service or now >= end_service:
        print("❌ Booking not allowed. Metro services are closed (11:00 PM - 4:30 AM).")
        return None

    expiry_time = end_service.strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute("""
            INSERT INTO tickets (ticket_id, source, destination, num_tickets, journey_type, phone_number, cost, payment_method, booking_time, expiry_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            ticket_data.get('source'),
            ticket_data.get('destination'),
            ticket_data.get('num_tickets'),
            ticket_data.get('journey_type'),
            ticket_data.get('phone_number'),
            ticket_data.get('cost'),
            ticket_data.get('payment_method'),
            now.strftime("%Y-%m-%d %H:%M:%S"),
            expiry_time
        ))

        conn.commit()
        print(f"✅ Booking successful! Your Ticket ID: {ticket_id}, Expires at: {expiry_time}")
        return ticket_id

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def extract_ticket_data_gemini(user_input, model_response, current_ticket_data):
    """Extracts ticket data and selectively updates it.
    Handles Gemini's tendency to return incomplete information."""
    conn = sqlite3.connect("metro_tickets.db")
    cursor = conn.cursor()

    # Fetch all station names
    cursor.execute("SELECT name FROM stations")
    station_names = [row[0] for row in cursor.fetchall()]

    # Close the connection
    conn.close()


    # Store original values for comparison
    original_data = current_ticket_data.copy()

    prompt = f"""
    User Input: {user_input}
    Model Response: {model_response}

    Extract the following ticket details: source, destination, num_tickets, journey_type, phone_number, cost, payment_method.
    If the details are in Hindi or Tamil, convert them to English. Have this value as reference {station_names}
    If a detail is not explicitly mentioned or confirmed, use 'None'. Return a valid JSON object. Ensure 'cost' is captured if present in the Model Response.
    """

    try:
        gemini_response = model.start_chat(history=[]).send_message(prompt).text
        print("Gemini Response:", gemini_response)

        # Sanitize the response
        gemini_response = gemini_response.replace("```json", "").replace("```", "").strip()

        try:
            extracted_data = json.loads(gemini_response)
            print("Extracted Data (JSON):", extracted_data)

            # Selectively update current_ticket_data
            for key, value in extracted_data.items():
                if value and value != "None":
                    current_ticket_data[key] = value  # Only update if valid

            # Reset cost if any key details change
            if (current_ticket_data.get('source') != original_data.get('source') or
                current_ticket_data.get('destination') != original_data.get('destination') or
                current_ticket_data.get('num_tickets') != original_data.get('num_tickets') or
                current_ticket_data.get('journey_type') != original_data.get('journey_type')):
                current_ticket_data['cost'] = None
                print("Ticket details changed, resetting cost.")

            print("Updated Ticket Data:", current_ticket_data)
            return current_ticket_data

        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}. Gemini Response was: {gemini_response}")
            return None

    except Exception as e:
        print(f"Error using Gemini: {e}")
        return None
  
             
def is_confirmation_message(model_response):
    """Checks for a booking confirmation using Gemini with refined prompt."""

    gemini_confirmation_prompt = f"""
    Given this chatbot response: "{model_response}"

    Determine if this message represents a FINAL outcome of a ticket booking process.  This could be EITHER:
    1) A CONFIRMATION where payment has been processed (or simulated) AND the user is now ready to receive/access their ticket(s).
    2) A message indicating the booking CANNOT be completed through this chatbot (e.g., directing the user to another payment method or platform) and no further action is needed.

    Answer ONLY with 'True' or 'False'.  Be VERY strict! Do not provide any additional explanation.
    """


    try:
        print("Sending this prompt to Gemini:", gemini_confirmation_prompt)  # Debug: Show the exact prompt

        gemini_response = model.start_chat(history=[]).send_message(gemini_confirmation_prompt).text
        print("Gemini Confirmation Raw Response:", gemini_response) #Raw Gemini

        # Convert the response to lowercase and strip whitespace
        gemini_response = gemini_response.lower().strip()

        print("Gemini Confirmation Lower/Strip:", gemini_response) #After cleaning

        if "true" in gemini_response:
            print("Gemini-Based Confirmation Detected")
            return True
        else:
            print("Gemini-Based Confirmation NOT Detected")
            return False

    except Exception as e:
        print("Gemini-based confirmation check failed:", e)
        return False
    
def detect_language_preference(text):
    """Detects language preference from user input (English, Tamil, Hindi).
    Returns the language if found, otherwise None."""
    text = text.lower()
    if "english" in text:
        return "English"
    elif "tamil" in text or "தமிழ்" in text:
        return "Tamil"
    elif "hindi" in text or "हिंदी" in text:
        return "Hindi"
    return None

def get_language_acknowledgment(language):
    """Returns a language-specific acknowledgment message."""
    if language == "English":
        return "Okay, booking tickets in English."
    elif language == "Tamil":
        return "சரி, நீங்க தமிழில் டிக்கெட் புக் பண்ணலாம்."
    elif language == "Hindi":
        return "ठीक है, हिंदी में टिकट बुक करेंगे।"
    else:
        return "Okay, proceeding in English."  # Default


def normalize_station_name(name):
    """Lowercases and strips whitespace from a station name."""
    return name.lower().strip()

def get_station_code(conn, station_name):
    """Retrieves the station code from the database given the station name,
    using aliases if necessary."""

    # List of station aliases
    station_aliases = {
        "alandur": "Arignar Anna Alandur",
        "chennai central": "Puratchi Thalaivar Dr. M.G. Ramachandran Central",
        "mgr central": "Puratchi Thalaivar Dr. M.G. Ramachandran Central",
        "central": "Puratchi Thalaivar Dr. M.G. Ramachandran Central",
        "cmbt": "Puratchi Thalaivi Dr. J. Jayalalithaa CMBT",
        "airport": "Chennai International Airport",
        "chennai airport": "Chennai International Airport",
        "ota": "OTA - Nanganallur Road",
        "nanganallur": "OTA - Nanganallur Road",
        "nanganallur road": "OTA - Nanganallur Road",
        "new washermenpet": "New Washermenpet Metro",
        "washermanpet metro": "Washermanpet",
        "tondiarpet": "Tondiarpet Metro",
        "tollgate": "Tollgate Metro",
        "thiruvotriyur theradi": "Thiruvotriyur Theradi Metro",
        "thiruvotriyur": "Thiruvotriyur Metro",
        "kaladipet": "Kaladipet Metro",
        "thiagaraya college": "Thiagaraya College Metro",
        "wimco nagar": "Wimco Nagar Metro",
        "wimco nagar depot metro": "Wimco Nagar Depot",
        "ekkattuthangal metro": "Ekkattuthangal",
        "ekkatuthangal": "Ekkattuthangal"
    }
    
    try:
        normalized_station_name = normalize_station_name(station_name)
        # Check if the normalized name is an alias
        if normalized_station_name in station_aliases:
            official_station_name = station_aliases[normalized_station_name]
            print(f"Alias found: '{station_name}' mapped to '{official_station_name}'")  # Debug print
        else:
            official_station_name = station_name # Use original station name if no alias is found
            print(f"No alias found for: '{station_name}'")  # Debug print
        cursor = conn.cursor()
        cursor.execute("SELECT code FROM stations WHERE LOWER(TRIM(name)) = ?", (normalize_station_name(official_station_name),))
        result = cursor.fetchone()
        if result:
            station_code = result[0]
            print(f"Station code found: {station_code}")
            return station_code
        else:
            print(f"Station code NOT found for station name: '{official_station_name}'")
            return None
    except sqlite3.Error as e:
        print(f"Error fetching station code: {e}")
        return None
    
def map_journey_type_to_code(journey_type):
    """Maps a textual journey type to its API code (SJT or RJT)."""
    journey_type = journey_type.lower()
    if "single" in journey_type or "one-way" in journey_type or "one way" in journey_type:
        return "SJT"
    elif "return" in journey_type or "two-way" in journey_type or "two way" in journey_type or "round trip" in journey_type or "double trip" in journey_type:
        return "RJT"
    else:
        return None

# Function to call the Fare API
def fetch_fare_from_api(origin_code, destination_code, ticket_type):
    """Fetches the fare from the CMRL Fare API."""
    api_url = f'https://quickticketapi.chennaimetrorail.org/api/airtel/farebyod?Origin={origin_code}&Destination={destination_code}&TicketType={ticket_type}'
    try:
        response = requests.get(api_url, headers={'accept': 'text/plain'})
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        if data['statusCode'] == 200:
            return data['result']['result']  # Access the fare value
        else:
            print(f"Fare API error: {data['statusCode']} - {data['message']}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching fare: {e}")
        return None
    except (KeyError, TypeError) as e:  # Handle potential issues with JSON structure
        print(f"Error parsing fare API response: {e}")
        return None


# Function to call the QR Ticket Code API
def generate_qr_ticket(ticket_data):
    """
    Calls the CMRL QR ticket API, converts the QR bytes to an image,
    and returns the base64 of the QR code image
    """

    api_url = 'https://quickticketapi.chennaimetrorail.org/api/airtel/generateqrticket'
    headers = {'accept': 'text/plain', 'Content-Type': 'application/json'}

    # Map ticket_data to API parameters.  This mapping is crucial.
    # Resolve Station Codes here before calling the API!
    conn = sqlite3.connect("metro_tickets.db")
    origin_code = get_station_code(conn, ticket_data.get('source'))
    destination_code = get_station_code(conn, ticket_data.get('destination'))
    journey_type_code = map_journey_type_to_code(ticket_data.get('journey_type'))

    if not origin_code or not destination_code or not journey_type_code:
        print("ERROR: Could not resolve station codes or journey type. QR ticket generation failed.")
        conn.close()  #Close the DB connection
        return None

    # Fetch the single ticket fare dynamically
    fare_per_ticket = fetch_fare_from_api(origin_code, destination_code, journey_type_code)
    conn.close() #Close the DB connection
    if fare_per_ticket is None:
        print("ERROR: Could not fetch fare. QR ticket generation failed.")
        return None

    try:
        no_of_tickets = int(ticket_data.get('num_tickets'))
    except (ValueError, TypeError) as e:
        print(f"Error parsing number of tickets: {e}")
        return None

    payload = {
        "ticketNumber": "",  # Generate this server-side using UUID, if necessary
        "origin": origin_code,  # Needs to be dynamically populated below with station codes
        "destination": destination_code,  # Needs to be dynamically populated below with station codes
        "ticketType": journey_type_code,  # Should be "SJT" or "RJT"
        "noOfTickets": no_of_tickets,  # Needs to be an integer
        "ticketFare": int(fare_per_ticket),  #The single ticket fare in INT
        "cancelReason": "",
        "cardNo": "",
        "rechargeAmount": 0,
        "customerMobileNo": ticket_data.get('phone_number'), #"9626450270",  #Should be mobile number that has been taken
        "uniqueTxnRefNo": str(uuid.uuid4()), #Unique ID for ticket booking
        "bankRefNo": str(uuid.uuid4()), #Unique Bank reference id
        "paymentMode": ticket_data.get('payment_method'), # "upi", # Should be UPI, card, wallet
        "mediaTypeId": "",
        "vendorId": "",
        "passengerTypeId": "",
        "paymentVendorId": "",
        "ipAddress": "",
        "appType": "CMRL_INTERNS_QR"    #set the App Id for appType
    }

    print("PAYLOAD to CMRL API:", json.dumps(payload, indent=4))

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        api_data = response.json() # Get the JSON Response

        if api_data['statusCode'] == 200 and api_data['result']:
            qr_base64 = api_data['result'][0]['qrBytes'] #Gets the base64 from response
            print("QR Code Generation API is successful with Status Code of 200")

            return qr_base64  # Return the base64

        else:
            print(f"ERROR: CMRL API returned an error: {api_data['statusCode']} - {api_data['message']}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return None
    except (KeyError, TypeError) as e:
        print(f"ERROR: Parsing JSON response failed: {e}")
        return None
    except Exception as e: #Catch all other exceptions
        print(f"ERROR: An unexpected error occurred: {e}")
        return None
    

@app.route('/')
def home():
    user_logo_path = '/static/images/user_logo.png'
    gemini_logo_path = '/static/images/gemini_logo.svg'
    return render_template('index.html', user_logo=user_logo_path, gemini_logo=gemini_logo_path)

def get_ticket_history():
    conn = sqlite3.connect("metro_tickets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT source, destination, num_tickets, journey_type, phone_number, cost, payment_method, booking_time, expiry_time FROM tickets")
    tickets = cursor.fetchall()
    conn.close()

    ticket_list = []
    for ticket in tickets:
        ticket_dict = {
            "source": ticket[0],
            "destination": ticket[1],
            "num_tickets": ticket[2],
            "journey_type": ticket[3],
            "phone_number": ticket[4],
            "cost": ticket[5],
            "payment_method": ticket[6],
            "booking_time": ticket[7],
            "expiry_time": ticket[8],
        }
        ticket_list.append(ticket_dict)

    return ticket_list



@app.route("/get_history")
def get_history():
    return jsonify(get_ticket_history())

@app.route('/ask', methods=['POST'])
def ask():
    # Initialize session variables
    if 'ticket_data' not in session:
        session['ticket_data'] = {
            'source': None,
            'destination': None,
            'num_tickets': None,
            'journey_type': None,
            'phone_number': None,
            'cost': None,
            'payment_method': None,
        }
    if 'language_selected' not in session:
        session['language_selected'] = False
    if 'selected_language' not in session:
        session['selected_language'] = 'English' # Default language
    if 'history' not in session:
        session['history'] = []

    try:
        user_input = request.json.get('message')
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400

        # Initial Language Detection
        if not session['language_selected']:
            language = detect_language_preference(user_input) # New function to detect language from the first message
            if language:
                session['selected_language'] = language
                session['language_selected'] = True
                session.modified = True
                acknowledgment = get_language_acknowledgment(language) #New function to get the acknowledgemnt message
                return jsonify({'response': acknowledgment, 'audio_url': None}) # Return acknowledgement message
            else:
                # Ask for language if not detected
                chat_session = model.start_chat(history=session['history'])
                response = chat_session.send_message(user_input)
                model_response = response.text
                if "Which language would you like to use for booking tickets?" in model_response:
                    session['history'].append({"role": "user", "parts": [user_input]})
                    session['history'].append({"role": "model", "parts": [model_response]})
                    session['language_selected'] = True
                    session.modified = True
                    return jsonify({'response': model_response, 'audio_url': None})  # Return the language prompt
                
        # Main booking flow
        else:
            chat_session = model.start_chat(history=session['history'])
            response = chat_session.send_message(user_input)
            model_response = response.text
            session['history'].append({"role": "user", "parts": [user_input]})
            session['history'].append({"role": "model", "parts": [model_response]})
            session.modified = True

            # Extract ticket data
            extracted_data = extract_ticket_data_gemini(user_input, model_response, session['ticket_data'])

            if extracted_data:
                session['ticket_data'] = extracted_data
                session.modified = True
            else:
                print("Data extraction failed.")

            # **FARE CALCULATION LOGIC**
            if session['ticket_data'].get('source') and session['ticket_data'].get('destination') and session['ticket_data'].get('journey_type') and session['ticket_data'].get('num_tickets') and session['ticket_data'].get('cost') is None:
                print ("Attempting to call Fare API")
                # Connect to DB
                conn = sqlite3.connect("metro_tickets.db")
                # Get station codes
                source_code = get_station_code(conn, session['ticket_data']['source'])
                destination_code = get_station_code(conn, session['ticket_data']['destination'])
                conn.close() #Close the DB connection
                journey_type_code = map_journey_type_to_code(session['ticket_data']['journey_type'])

                if source_code and destination_code and journey_type_code:
                    fare_per_ticket = fetch_fare_from_api(source_code, destination_code, journey_type_code)
                    if fare_per_ticket is not None:
                        try:
                            num_tickets = int(session['ticket_data']['num_tickets'])
                            num_tickets_words = num2words(num_tickets, to='cardinal') #Converting the number of tickets to words
                            total_fare = fare_per_ticket * num_tickets
                            session['ticket_data']['cost'] = str(total_fare)  # Store as string for consistency
                            session.modified = True
                            print(f"Calculated fare: Single ticket = ₹{fare_per_ticket}, Total = ₹{total_fare}")
                            # **CRITICAL: Include fare details in the model_response**                                                      
                            if (session['selected_language'] == 'English'):
                                model_response += f"\nThe fare for a {session['ticket_data']['journey_type']} ticket from {session['ticket_data']['source']} to {session['ticket_data']['destination']} is ₹{fare_per_ticket}. The total fare for {num_tickets_words} tickets is ₹{total_fare}. Would you like to confirm the booking?"  # Changed from num_tickets to num_tickets_words. 
                                session['history'].append({"role": "model", "parts": [model_response]})                        
                            elif (session['selected_language'] == 'Tamil'):
                                model_response += f"\n{session['ticket_data']['source']} இருந்து {session['ticket_data']['destination']} வரை ஒரு {session['ticket_data']['journey_type']} டிக்கெட்டுக்கான கட்டணம் ₹{fare_per_ticket} ஆகும். {num_tickets_words} டிக்கெட்களுக்கு மொத்த கட்டணம் ₹{total_fare} ஆகும். நீங்கள் முன்பதிவை உறுதிப்படுத்த விரும்புகிறீர்களா?"
                                session['history'].append({"role": "model", "parts": [model_response]})
                            elif (session['selected_language'] == 'Hindi'):
                                model_response += f"\n{session['ticket_data']['source']} से {session['ticket_data']['destination']} तक के एक {session['ticket_data']['journey_type']} टिकट का किराया ₹{fare_per_ticket} है। {num_tickets_words} टिकटों का कुल किराया ₹{total_fare} है। क्या आप बुकिंग की पुष्टि करना चाहेंगे?"
                                session['history'].append({"role": "model", "parts": [model_response]})
                            
                        except ValueError:
                            print("Invalid number of tickets provided.")
                            model_response += "\nThere was an error calculating the fare. Please check the number of tickets."  # Inform the user. 
                    else:
                        model_response += "\nSorry, I could not retrieve the fare for this journey."  # Inform the user.
                else:
                    model_response += "\nSorry, I could not find the station codes or journey type."  # Inform the user.

            #Sanitizing the response
            response_text = re.sub(r'[*_#]', '', model_response) # Sanitize
            detected_lang = detect_language(response_text)  # Use cleaned response text
            tts = gTTS(text=response_text, lang=detected_lang)
            tts.save(TEMP_AUDIO_PATH)
            timestamp = int(time.time())
            audio_url = f'/{TEMP_AUDIO_PATH}?t={timestamp}'

            # Before storing, print the full session data and the result of the confirmation check
            print("Session Ticket Data:", session['ticket_data'])
            print("Confirmation Check:", is_confirmation_message(model_response))

            # Store booking if all details are present and it is confirmation time
            required_fields = ["source", "destination", "num_tickets", "journey_type", "phone_number", "cost", "payment_method"]
            if is_confirmation_message(model_response) and all(session['ticket_data'].get(field) for field in required_fields):
                # Generate QR ticket data (base64)
                qr_base64 = generate_qr_ticket(session['ticket_data']) # Calling the QR Code function
                if qr_base64:
                    print(f"Successfully generated QR code.")
                    ticket_id = store_booking(session['ticket_data'])
                    if ticket_id:
                        print(f"Successfully stored ticket with ID: {ticket_id}")
                        session['ticket_data'] = { #Reset the ticket data
                            'source': None,
                            'destination': None,
                            'num_tickets': None,
                            'journey_type': None,
                            'phone_number': None,
                            'cost': None,
                            'payment_method': None,
                        }
                        session['history'] = [] #Clear history too.
                        session.modified = True
                        # Include the QR code data and the newly booked ticket's id in the JSON response to the client.
                        return jsonify({'response': model_response, 'audio_url': audio_url, 'qr_base64': qr_base64, 'ticket_id': ticket_id})
                    else:
                        print("Storing ticket failed") #Handle failure appropriately.
                        return jsonify({'response': "There was an error storing the ticket. Please try again.", 'audio_url': audio_url})
                else:
                    print("QR Code generation failed.")
                    return jsonify({'response': "There was an error generating the QR code. Please try again.", 'audio_url': audio_url})

            return jsonify({'response': model_response, 'audio_url': audio_url})

    except Exception as e:
        print(f"Error in /ask route: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    conn = sqlite3.connect('metro_tickets.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            source TEXT,
            destination TEXT,
            num_tickets INTEGER,
            journey_type TEXT,
            phone_number TEXT,
            cost REAL,
            payment_method TEXT,
            booking_time TEXT,
            expiry_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

    app.run(debug=True, host='127.0.0.1', port=8001)
