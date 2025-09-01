from flask import Flask, render_template, request, jsonify, url_for
import google.generativeai as genai
import os
from dotenv import load_dotenv
from gtts import gTTS
import time
import re
import sqlite3
import json




'''
Some of the station name erro to be fixed


User:
Arignar Anna Alandur (Alandur) to guindy

Mithra:
Error generating response: 400

User:
from Meenambakkam to Pachaiyappas

Mithra:
Error generating response: 400

User:
OTA - Nanganallur Road to Ashok Nagar

Mithra:
Error generating response: 400

User:
Tollgate Metro to tondiarpet metro

Mithra:
Error generating response: 400

User:
from airport to egmore

Mithra:
Error generating response: 400

Ekkattuthangal ---- Major error!

User:
Thousand Lights to kilpauk

Mithra:
Failed to fetch




User:
New Washermenpet to koyambedu

Mithra:
Error generating response: 400

User:
Koyambedu to New Washermanpet

Mithra:
Error generating response: 400

User:
Ekkatuthangal to Anna nagar east

Mithra:
Error generating response: 400

User:
ekkatuthangal to central

Mithra:
Error generating response: 400

User:
central to ekkatuthangal

Mithra:
Error generating response: 400

User:
airport to egmore

Mithra:
Error generating response: 400


Bug for swtiching line scenario or central, airport
'''



DATABASE_NAME = 'chennai_metro.db'  # Define your db name

# Ensure the static/audio folder exists
audio_folder = 'static/audio'
if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)

# Temporary audio file path
TEMP_AUDIO_PATH = os.path.join(audio_folder, 'temp_audio.mp3')

load_dotenv()  # Load environment variables from .env file

api_key = "AIzaSyBP5uV1TfyN5Mh3SPAegcqhDp4QAOFOFg8"  # Get API key from env variables

genai.configure(api_key=api_key)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash",
  generation_config=generation_config,
  system_instruction="""
Objective:

You are MITHRA, a multilingual voice bot for Chennai Metro Railways. Your sole purpose is to provide users with accurate travel information (Tamil, Hindi, or English). Strictly limit responses to metro/railway queries.

Key Requirements:

1. Language:
    * Detect user language (Tamil, Hindi, English).
    * **Respond ONLY in the detected language.**

2. Core Functionalities:

    * Greeting: Greet the user ONLY at the beginning of the conversation or if greeted first.
        * Tamil: "வணக்கம்! நான் மித்ரா, உங்கள் சென்னை மெட்ரோ சேவைகள் குறித்த உங்கள் துணைவர். நான் உங்களுக்கு இன்று எவ்வாறு உதவ முடியும்?"
        * Hindi: "नमस्ते! मैं मिथ्रा हूं, आपकी चेन्नई मेट्रो सेवाओं के लिए आपकी सहायक हूं। मैं आज आपकी कैसे मदद कर सकता हूं?"
        * English: "Hello! I am MITHRA, your Chennai Metro assistant. How can I help you today?"

    * Metro/Railway Information:
        * Provide directions, train timings, ticket prices, station facilities.
        * Give step-by-step route guidance (Station A to Station B): platform info, transfers, onward travel.

    * Out-of-Scope:
        * Non-travel: "I'm designed for Chennai Metro/Railway travel only."
        * Non-metro location: "[Location] is not a metro station. Nearest station to [Location]?"

3. Route Calculation (Station A to Station B):

    * Station List: Use provided Blue/Green Line stations (name: distance km).
        * Invalid station: "I am sorry, there is no station called [station] in the Chennai Metro network.".
        * No route: "I am sorry, there is no direct route available between those stations.".

    * Train Direction (Blue/Green Line): Based on destination proximity to line endpoints.
        * Blue Line: Airport or Wimco Nagar Depot
        * Green Line: St. Thomas Mount or Chennai Central

    * Step-by-Step Guidance:
        * Start: Clear starting point AND platform details.
        * Line/Direction: Line (Green/Blue), train direction, final destination.
        * Intermediate Stations: ALL stations between start/end: 🔵[Blue Station] → 🟢[Green Station]. Use →.
        * Transfer: Instructions on transfer, line switch, platform. Mention Lifts/Escalators ONLY if asked. Re-evaluate direction for next line.
        * Destination: Alight at destination station AND platform details.

    * Concluding Information:
        * Total Distance, Estimated Time, Transfer Time Disclaimer.

    * Crucially, only respond with what user wants:
           * If the user asks directly about platform numbers, lifts, or escalators, then you MUST include the corresponding details from the provided data.
           * If the user does NOT explicitly ask about those details, DO NOT include them in your initial response.

    * **Example Output:** (ADHERE CLOSELY!)

            "Okay, to get from Anna Nagar East to Nandanam:
            1. Start at Anna Nagar East and board Green Line Platform 2 Towards MGR Central.\n
            2. Travel through 🟢Shenoy Nagar → 🟢Pachaiyappa's College → 🟢Kilpauk → 🟢Nehru Park → 🟢Egmore.\n
            3. Alight at MGR Central.\n
            4. Transfer to Blue Line Platform 5 Towards Chennai Airport.\n
            5. Travel through 🔵Government Estate → 🔵LIC → 🔵Thousand Lights → 🔵AG-DMS → 🔵Teynampet.\n
            6. Finally, alight at Nandanam.\n
            Total: 12.6km, ~26 mins + transfer."

            "Okay, to get from Anna Nagar East to Nandanam. Platform for Anna Nagar East?:
            1. Start at Anna Nagar East, Green Line Platform 2. This station features : Escalator No 05 (Street to Unpaid Concourse, A2 Entrance), etc. Lifts: Lift No 01 (Concourse to Street, A1 Entrance), etc. Board train to MGR Central.\n
            2. Travel through 🟢Shenoy Nagar → 🟢Pachaiyappa's College → 🟢Kilpauk → 🟢Nehru Park → 🟢Egmore.\n
            3. Alight at MGR Central.\n
            4. Transfer to Blue Line Platform 5 Towards Chennai Airport.\n
            5. Travel through 🔵Government Estate → 🔵LIC → 🔵Thousand Lights → 🔵AG-DMS → 🔵Teynampet.\n
            6. Finally, alight at Nandanam.\n
            Total: 12.6km, ~26 mins + transfer."

    If no valid route, respond: "I am sorry, there is no direct route available between those stations."

4.  Examples (English only):

    * User: "Chennai Airport to Vadapalani?"
        * MITHRA: "Shortest Path: Chennai Airport -> Meenambakkam -> Alandur -> Ekkattuthangal -> Ashok Nagar -> Vadapalani. Total: 12.5 km. ~25 mins."

    * User: "Lift at Chennai Airport?"
        * MITHRA: "Chennai Airport: Lift 03, Concourse to Platform 1."

    * User: "Start from Guindy?"
        * MITHRA: "Guindy: Elevator to Level 2 for ticketing, Platform 1 to Airport. Can I assist?"

    * User: "Bicycles on metro?"
        * MITHRA: "Yes, bicycles allowed during non-peak hours."

    * User: "Restaurants near Guindy?"
        * MITHRA: "I’m here for Chennai Metro/Railways only."

    * User: "Chennai Airport to Meenambakkam?"
        * MITHRA: "Chennai Airport Platform 1 towards Wimco Nagar Depot. Meenambakkam is next station."

    * User: "நான் விமான நிலையத்துக்கு செல்ல எந்த ரெயில் எடுக்க வேண்டும்?" (Tamil)
        * MITHRA: "விமான நிலையத்தை அடைய, விமான நிலையத்தை நோக்கி ப்ளூ லைன் ரயிலில் செல்லவும்."

    * User: "मुझे हवाई अड्डे जाने के लिए कौन सी ट्रेन लेनी चाहिए?" (Hindi)
        * MITHRA: "हवाई अड्डे के लिए, कृपया एयरपोर्ट की ओर जाने वाली ब्लू लाइन ट्रेन लें।"
""",
)

history = []

app = Flask(__name__)


def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        print(f"Connected to {DATABASE_NAME}")
    except sqlite3.Error as e:
        print(e)
    return conn


def create_tables():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()

            # Create blue_line_stations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blue_line_stations (
                    id INTEGER PRIMARY KEY,
                    station_name TEXT NOT NULL,
                    distance REAL
                )
            """)

            # Create green_line_stations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS green_line_stations (
                    id INTEGER PRIMARY KEY,
                    station_name TEXT NOT NULL,
                    distance REAL
                )
            """)

            # Create station_details table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS station_details (
                    station_name TEXT PRIMARY KEY,
                    platform_details TEXT
                )
            """)

            conn.commit()
            print("Tables created successfully")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()
    else:
        print("Error! cannot create database connection.")


def populate_database():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()

            # Blue Line Stations Data (Extract from your prompt)
            blue_line_data = [
                (1, 'Wimco Nagar Depot', 0.0),
                (2, 'Wimco Nagar', 0.8),
                (3, 'Thiruvotriyur', 1.8),
                (4, 'Thiruvottriyur Theradi', 2.8),
                (5, 'Kaladipet', 4.2),
                (6, 'Tollgate', 5.7),
                (7, 'New Washermenpet', 6.9),
                (8, 'Tondiarpet', 7.9),
                (9, 'Thiyagaraya College', 8.9),
                (10, 'Washermenpet', 9.9),
                (11, 'Mannadi', 11.2),
                (12, 'High Court', 12.4),
                (13, 'Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)', 13.5),
                (14, 'Government Estate', 14.3),
                (15, 'LIC', 15.1),
                (16, 'Thousand Lights', 15.7),
                (17, 'AG-DMS', 16.8),
                (18, 'Teynampet', 17.9),
                (19, 'Nandanam', 19.0),
                (20, 'Saidapet', 20.1),
                (21, 'Little Mount', 21.2),
                (22, 'Guindy', 22.3),
                (23, 'Arignar Anna Alandur (Alandur)', 23.4),
                (24, 'OTA - Nanganallur Road', 24.8),
                (25, 'Meenambakkam', 26.2),
                (26, 'Chennai International Airport', 27.5)
            ]

            # Green Line Stations Data (Extract from your prompt)
            green_line_data = [
                (1, 'Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)', 0.0),
                (2, 'Egmore', 1.3),
                (3, 'Nehru Park', 2.4),
                (4, 'Kilpauk', 3.5),
                (5, "Pachaiyappa's College", 4.8),
                (6, 'Shenoy Nagar', 5.6),
                (7, 'Anna Nagar East', 6.7),
                (8, 'Anna Nagar Tower', 7.8),
                (9, 'Thirumangalam', 9.0),
                (10, 'Koyambedu', 10.1),
                (11, 'CMBT', 12.3),
                (12, 'Arumbakkam', 13.4),
                (13, 'Vadapalani', 14.5),
                (14, 'Ashok Nagar', 15.6),
                (15, 'Ekkattuthangal', 16.7),
                (16, 'Arignar Anna Alandur (Alandur)', 18.0),
                (17, 'St. Thomas Mount', 19.3)
            ]

            # Station Details (Extract from your prompt)
            station_details_data = [
                ('Chennai International Airport', "Chennai International Airport Metro Station, also known as 'Airport' has two platforms: Platform 1 (towards Wimco Nagar Depot Metro) and Platform 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station has multiple escalators: Escalator 1 (Street to Concourse Unpaid, A Entrance), Escalator 2 (Concourse to Street, A Entrance), Escalator 3 (Concourse to Platform 1), Escalator 4 (Platform 1 to Concourse), Escalator 5 (Concourse to Platform 2), Escalator 6 (Platform 2 to Concourse), Escalator 9 (Intermediate to Concourse, B Entrance), Escalator 10 (Concourse to Intermediate, B Entrance). The lifts include Lift 03 (Concourse to Platform 1), Lift 04 (Concourse to Platform 2), Lift 05 (Parking, Street to Unpaid Concourse, A Entrance), Lift 06 (Parking to Unpaid Concourse, near EFO 2), and Lift 07 (Street, Intermediate to Unpaid Concourse, B Entrance)."),
                ('Meenambakkam', "Meenambakkam Metro Station, also known as 'Meenambakkam' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro and Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station is equipped with multiple lifts: Lift 1 (Street to Unpaid Concourse, A2 Entrance), Lift 2 (Street to Unpaid Concourse, B2 Entrance), Lift 3 (Concourse to Platform 1), and Lift 4 (Concourse to Platform 2)."),
                ('OTA - Nanganallur Road', "OTA-Nanganallur Road Metro Station, also known as 'Nanganallur Road' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station has three lifts: Lift 01 (Street to Concourse), Lift 02 (Concourse to Platform 1), and Lift 03 (Concourse to Platform 2)."),
                ('Arignar Anna Alandur (Alandur)', "Arignar Anna Alandur Metro Station, also known as 'Alandur' has four platforms: Platform 1 (towards Chennai Airport), Platform 2 (towards Wimco Nagar Depot Metro), Platform 3 (towards St. Thomas Mount Metro and Chennai Airport), and Platform 4 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features escalators: Escalator 8 (Street to Platform 1), Escalator 10 (Platform 1 to Street), Escalator 18 (Platform 1 to Platform 3), Escalator 24 (Platform 3 to Platform 1), Escalator 6 (Street to Platform 2), Escalator 12 (Platform 2 to Street), Escalator 20 (Platform 2 to Platform 4), and Escalator 22 (Platform 4 to Platform 2). The lifts include Lift 1 and Lift 2 (Street to Platforms 1 and 3) and Lift 3 and Lift 4 (Street to Platforms 2 and 4)."),
                ('Guindy', "Guindy Metro Station, also known as 'Guindy' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station features multiple escalators: Escalator 1 (Street to Unpaid Concourse), Escalator 5 (Paid Concourse to Mechanical), Escalator 7 (Mechanical to Platform 1), and Escalator 8 (Mechanical to Platform 2). The lifts include Lift 2 (Street to Unpaid Concourse), Lift 3 (Concourse to Platform 1), and Lift 4 (Concourse to Platform 2)."),
                ('Little Mount', "Little Mount Metro Station, also known as 'Little Mount' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station is equipped with escalators: Escalator 6 (Platform 1 to Link Bridge), Escalator 7 (Link Bridge to Platform 1, A Entrance), and Escalator 4 (Street to Link Bridge, B Entrance). The lifts include Lift 01 (Concourse to Street, A Entrance) and Lift 02 (Concourse to Street, B Entrance)."),
                ('Saidapet', "Saidapet Metro Station, also known as 'Saidapet' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station is equipped with several escalators: Escalator 1 (Unpaid Concourse to Street, A1 Entrance), Escalator 2 (Street to Unpaid Concourse, A1 Entrance), Escalator 3 (Unpaid Concourse to Street, B2 Entrance), Escalator 4 (Street to Unpaid Concourse, B2 Entrance), Escalator 5 (Unpaid Concourse to Street, A2 Entrance), Escalator 6 (Platform to Concourse, EFO 02), and Escalator 7 (Concourse to Platform, EFO 01). The lifts include Lift 1 (Street to Unpaid Concourse, A3 Entrance), Lift 2 (Street to Unpaid Concourse, B1 Entrance), and Lift 3 (Platform to Concourse)."),
                ('Nandanam', "Nandanam Metro Station, also known as 'Nandanam' consists of two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station is equipped with multiple escalators, including Escalator 1 (Street to Unpaid Concourse, A1 Entrance), Escalator 3 (Street to Unpaid Concourse, B1 Entrance), Escalator 5 (Street to Intermediate, B4 Entrance), Escalator 6 (Street to Unpaid Concourse, A2 Entrance), Escalator 5 (Intermediate to Street, B4 Entrance), Escalator 8 (Concourse to Platform, EFO 01), and Escalator 11 (Concourse to Platform, EFO 02). The lifts available at Nandanam Metro are Lift 1 (Concourse to Street, B2 Entrance), Lift 2 (Street to Unpaid Concourse, A3 Entrance), Lift 3 (Concourse to Platform), Lift 4 (Concourse to Street, B3 Entrance), and Lift 5 (Concourse to Street, B3 Entrance)."),
                ('Teynampet', "Teynampet Metro Station, also known as 'Teynampet' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station has multiple escalators and lifts: Escalator 2 (Street to Unpaid Concourse, A2 Entrance), Escalator 3 (Street to Unpaid Concourse, B1 Entrance), Escalator 4 (Street to Intermediate, B1 Entrance), Escalator 5 (Street to Unpaid Concourse, B3 Entrance), Escalator 6 (Street to Unpaid Concourse, A3 Entrance), Escalator 8 (Concourse to Platform, EFO 02), and Escalator 11 (Concourse to Platform, EFO 01). The lifts include Lift 1 (Concourse to Street, A1 Entrance), Lift 2 (Concourse to Street, B2 Entrance), and Lift 3 (Near station control room)."),
                ('AG-DMS', "AG - DMS Metro Station, also known as 'AG - DMS' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station is equipped with multiple escalators and lifts: Escalator 1 (Street to Concourse, A1 Entrance), Escalator 2 (Concourse to Street, A1 Entrance), Escalator 3 (Concourse to Street, B1 Entrance), Escalator 5 (Intermediate to Street, A3 Entrance), Escalator 7 (Platform to Concourse, EFO 01), and Escalator 9 (Platform to Concourse, EFO 02). Additionally, Lift 1 (Concourse to Street, A1 Entrance), Lift 2 (Concourse to Street, B3 Entrance), and Lift 3 (Concourse to Platform) are available."),
                ('Thousand Lights', "Thousand Lights Metro Station, also known as 'Thousand Lights' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station is equipped with multiple escalators and lifts: Escalator 1 (Concourse to Street, A1 Entrance), Escalator 5 (Concourse to Street, A4 Entrance), Escalator 6 (Concourse to Street, A4 Entrance), Escalator 7 (Platform to Concourse), and Escalator 10 (Platform to Concourse). Additionally, Lift 1 (Concourse to Street, A3 Entrance), Lift 2 (Concourse to Street, B3 Entrance), and Lift 3 (Concourse to Platform near to SCR) are available."),
                ('LIC', "LIC Metro Station, also known as 'LIC' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station is equipped with multiple escalators and lifts: Escalator 3 (Intermediate to Street, B2 Entrance), Escalator 4 (Concourse to Intermediate, B2 Entrance), Escalator 7 (Concourse to Street, A3 Entrance), Escalator 8 (Street to Concourse, A3 Entrance), Escalator 9 (Platform to Concourse), and Escalator 12 (Platform to Concourse). Additionally, Lift 1 (Concourse to Street, B1 Entrance), Lift 2 (Concourse to Street, B4 Entrance), Lift 3 (Concourse to Platform), Lift 4 (Concourse to Street, A1 Entrance), and Lift 5 (Concourse to Street, A1 Entrance) are available."),
                ('Government Estate', "Government Estate Metro Station, also known as 'Government Estate' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station is equipped with multiple escalators and lifts: Escalator 2 (Concourse to Street, B1 Entrance), Escalator 4 (Concourse to Street, B2 Entrance), Escalator 6 (Concourse to Street, A4 Entrance), Escalator 7 (Platform to Concourse), and Escalator 10 (Platform to Concourse). Additionally, Lift 1 (Concourse to Street, A1 Entrance), Lift 2 (Concourse to Street, A3 Entrance), and Lift 3 (Concourse to Platform) are available."),
                ('Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)', "Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro Station, also known as 'Chennai Central' has four platforms: Platform 1 and Platform 2 (both towards St. Thomas Mount Metro and Chennai Airport), Platform 5 (towards Chennai Airport), and Platform 6 (towards Wimco Nagar Depot Metro). The station is equipped with several escalators and lifts: Escalator 1 (Street to Unpaid Concourse, B1 Entrance), Escalator 2 (Unpaid Concourse to Street, B1 Entrance), Escalator 3 (Subway 1 to Street, Towards Park Station), Escalator 39 (Street to Subway 1, Towards Park Station), Escalator 16 (Unpaid Concourse to Street, B5 Entrance), Escalator 38 (Unpaid Concourse to Subway 1, B3 & B4 Entrances), Escalator 37 (Subway 1 to Unpaid Concourse, B3 & B4 Entrances), Escalator 33 (Subway 1 to Street, B3 & B4 Entrances), Escalator 36 (Street to Subway 1, B3 & B4 Entrances), Escalator 41 (Unpaid Concourse to Subway 2, A1 & A2 Entrances), Escalator 42 (Subway 2 to Unpaid Concourse, A1 & A2 Entrances), Escalator 34 (Subway 2 to Street, A1 & A2 Entrances), Escalator 40 (Street to Subway 2, A1 & A2 Entrances), Escalator 45 (Unpaid Concourse to Subway 2, A3 Entrance), Escalator 46 (Subway 2 to Unpaid Concourse, A3 Entrance), Escalator 43 (Subway 2 to Street, A3 Entrance), Escalator 44 (Street to Subway 2, A3 Entrance), Escalator 35 (Subway 2 to Street, Central Bus Stop), Escalator 47 (Street to Subway 2, Central Bus Stop), Escalator 6 (Street to Subway 3, Towards Central), Escalator 7 (Subway 3 to Street, Towards Central), Escalator 40 (Subway 3 to Street, Towards GH), Escalator 29 (Paid Concourse to Platform 1 & 2, EFO 01), Escalator 48 (Platform 1 & 2 to Paid Concourse, EFO 01), Escalator 30 (Platform 1 & 2 to Platform 5 & 6, EFO 01), Escalator 49 (Platform 5 & 6 to Platform 1 & 2, EFO 01), Escalator 21 (Paid Concourse to Platform 1 & 2, EFO 02), Escalator 22 (Platform 1 & 2 to Paid Concourse, EFO 02), Escalator 25 (Platform 1 & 2 to Platform 5 & 6, EFO 02), and Escalator 26 (Platform 5 & 6 to Platform 1 & 2, EFO 02). Additionally, Lift 1 (Concourse to Street, B2 Entrance), Lift 2 (Concourse to Street, A1 & A2 Entrances), Lift 15 (Concourse to Subway 2, A1 & A2 Entrances), Lift 16 (Subway 2 to Street, A1 & A2 Entrances), Lift 3 (Concourse to Subway 2, A3 Entrance), Lift 17 (Subway 2 to Street, A3 Entrance), Lift 5 (Concourse to Subway 1, B3 & B4 Entrances), Lift 13 (Subway 1 to Street, B3 & B4 Entrances), Lift 8 (Concourse to Platform 1 & 2), Lift 18 (Platform 1 & 2 to Platform 5 & 6), Lift 19 (Subway 3 to Street), Lift 20 (Subway 3 to Street), Lift 14 (Subway 1 to Street), Lift 11 (Subway 2 to Street), and Lift 12 (Subway 2 to Street)."),
                ('High Court', "High Court Metro Station, also known as 'Highcourt' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station has multiple escalators: Escalator 1 (Street to Unpaid Concourse, B1 Entrance), Escalator 3 (Street to Unpaid Concourse, A1 Entrance), Escalator 5 (Street to Unpaid Concourse, A2 Entrance), Escalator 6 (Concourse to Platform), and Escalator 9 (Concourse to Platform). The lifts include Lift 1 (Concourse to Street, A1 Entrance), Lift 2 (Concourse to Street, A4 Entrance), Lift 3 (Concourse to Street, A2 Entrance), Lift 4 (Concourse to Street, B2 Entrance), and Lift 5 (Concourse to Platform)."),
                ('Mannadi', "Mannadi Metro Station, also known as 'Mannadi' has two platforms: Platform 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station has multiple escalators: Escalator 2 (Street to Unpaid Concourse, B1 Entrance), Escalator 3 (Street to Unpaid Concourse, A1 Entrance), Escalator 4 (Concourse to Platform, EFO 02), and Escalator 7 (Concourse to Platform, EFO 01). The lifts include Lift 1 (Concourse to Street, B1 Entrance), Lift 2 (Street to Unpaid Concourse, A1 Entrance), Lift 3 (Concourse to Platform), and Lift 4 (Concourse to Platform)."),
                ('Wimco Nagar Depot', "Wimco Nagar Depot Station, also known as 'Wimco Nagar Depot Metro' or 'Wimco Nagar Depot' has one platform: Platform No 1 or SBL 1 (towards Chennai Airport). The station includes Escalator 01, with no specified floor or location. The lifts include Lift 01 (Concourse to Street, Main Entrance), Lift 01 (Platform to Street, Main Entrance), Lift 02 (Concourse to Street, Main Entrance), and Lift 02 (Platform to Street, Main Entrance)."),
                ('Wimco Nagar', "Wimco Nagar Metro Station, also known as 'Wimco Nagar' has two platforms: Platform No 1 (towards Chennai Airport) and Platform 2 (towards Wimco Nagar Depot Metro). The station includes multiple escalators: Escalator 1 (Concourse to Platform 2, Upstairs), Escalator 2 (Concourse to Platform 2, Downstairs), Escalator 7 (Concourse to Platform 1, Downstairs), Escalator 8 (Concourse to Platform 1, Upstairs), and Escalator 9 (Street to Concourse, E1 Entrance). The lifts include Lift 1 (Concourse to Platform 2), Lift 2 (Concourse to Platform 1), Lift 3 (Street to Concourse, E1 Entrance), and Lift 4 (Street to Concourse, E3 Entrance)."),
                ('Thiruvotriyur', "Thiruvotriyur Metro Station, also known as 'Thiruvotriyur' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Wimco Nagar Depot Metro). The station includes multiple escalators: Escalator 3 (Paid Concourse to Platform 2), Escalator 4 (Platform 2 to Paid Concourse), Escalator 5 (Paid Concourse to Platform 1), Escalator 6 (Platform 1 to Paid Concourse), and Escalator 9 (Street to Concourse, E2 Entrance). The lifts include Lift 1 (Concourse to Platform 2), Lift 2 (Concourse to Platform 1), Lift 3 (Concourse to Street, E2 Entrance), and Lift 4 (Concourse to Street, E3 Entrance)."),
                ('Thiruvottriyur Theradi', "Thiruvottriyur Theradi Metro Station, also known as 'Thiruvottriyur Theradi' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Wimco Nagar Depot Metro). The station includes multiple lifts: Lift 1 (Street to Platform Unpaid Area, E1 Entrance), Lift 2 (Street to Platform Unpaid Area, E1 Entrance), Lift 3 (Street to Platform Unpaid Area, E2 Entrance), Lift 4 (Street to Platform Unpaid Area, E2 Entrance), Lift 5 (Street to Platform Unpaid Area, E1 Entrance), and Lift 7 (Street to Platform Unpaid Area, E2 Entrance)."),
                ('Kaladipet', "Kaladipet Metro Station, also known as 'Kaladipet' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Wimco Nagar Depot Metro). The station features several escalators: Escalator 10 (Street to Concourse, E1 Entrance), Escalator 9 (Street to Concourse, E2 Entrance), Escalator 3 (Concourse to Platform 2), Escalator 4 (Concourse to Platform 2), Escalator 5 (Concourse to Platform 1), and Escalator 6 (Concourse to Platform 1). The lifts include Lift 1 (Concourse to Platform 1), Lift 2 (Concourse to Platform 2), Lift 3 (Concourse to Street, E1 Entrance), Lift 4 (Concourse to Street, E3 Entrance), and Lift 5 (Concourse to Street, E3 Entrance)."),
                ('Tollgate', "Tollgate Metro Station, also referred to as 'Tollgate' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Wimco Nagar Depot Metro). The station is equipped with multiple escalators: Escalator No 3 (Platform 01 to Concourse), Escalator No 4 (Platform 02 to Concourse), Escalator No 5 (Concourse to Platform 01), Escalator No 6 (Concourse to Platform 02), and Escalator No 9 (Street Level to Concourse). Additionally, there are four lifts: Lift No 1 (Concourse to Platform 02), Lift No 2 (Concourse to Platform 01), Lift No 3 (Street Level to Concourse, E1 Entrance), and Lift No 4 (Street Level to Concourse)."),
                ('New Washermenpet', "New Washermenpet Metro Station, also known as 'New Washermenpet' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Wimco Nagar Depot Metro). The station features several escalators: Escalator No 5 (Street to Unpaid Concourse, E3 Entrance), Escalator No 2 (Paid Concourse to Platform 1), and Escalator No 3 (Paid Concourse to Platform 2). The lifts include Lift 3 & 4 (Street to Unpaid Concourse, E1 Entrance), Lift 5 (Street to Unpaid Concourse, E2 Entrance), Lift 7 (Street to Unpaid Concourse, E4 Entrance), Lift 2 (Paid Concourse to Platform 1), Lift 1 (Paid Concourse to Platform 2), and Lift 6 (Pd Area)."),
                ('Tondiarpet', "Tondiarpet Metro Station, also known as 'Tondiarpet' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Wimco Nagar Depot Metro). The station features several escalators: Escalator No 3 (Platform to Concourse, Near EFO-02), Escalator No 4 (Concourse to Platform, Near EFO-02), Escalator No 8 (Concourse to Street, E1 Entrance), Escalator No 10 (Concourse to Street, E2 Entrance), Escalator No 11 (Concourse to Street, E3 Entrance), and Escalator No 12 (Street level to Concourse, E3 Entrance). The lifts include Lift No 1 (Street level to Concourse, E4 Entrance), Lift No 2 (Street level to Concourse, E3 Entrance), and Lift No 3 (Platform to Concourse, Concourse Middle)."),
                ('Thiyagaraya College', "Thiyagaraya College Metro Station, also known as 'Thiyagaraya College' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Wimco Nagar Depot Metro). The station features several escalators: Escalator No 3 (Platform to Concourse), Escalator No 4 (Concourse to Platform), Escalator No 7 (Unpaid Concourse to Street, E2 Entrance), and Escalator No 9 (Unpaid Concourse to Street, E2 Entrance). The lifts include Lift No 1 (Concourse to Street, E4 Entrance), Lift No 2 (Street to Unpaid Concourse, E3 Entrance), and Lift No 3 (Concourse to Platform)."),
                ('Washermenpet', "Washermenpet Metro Station, also known as 'Washermenpet' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Wimco Nagar Depot Metro). The station features several escalators: Escalator No 3 (Concourse to Street, A1 Entrance), Escalator No 1 (Concourse to Street, B2 Entrance), Escalator No 12 (Concourse to Street, B3 Entrance), Escalator No 05 (Concourse to Platform), and Escalator No 08 (Concourse to Platform). The lifts include Lift No 1 (Concourse to Street, A2 Entrance), Lift No 2 (Concourse to Street, B1 Entrance), and Lift No 3 (Concourse to Platform)."),
                ('Egmore', "Egmore Metro Station, also known as 'Egmore' has two platforms: Platform No 1 (towards St. Thomas Mount Metro Station) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features several escalators: Escalator No 1 (Street to Unpaid Concourse, A3 Entrance), Escalator No 3 (Street to Unpaid Concourse, A1 Entrance), Escalator No 4 (Street to Unpaid Concourse, B2 Entrance), Escalator No 5 (Street to Unpaid Concourse, B2 Entrance), Escalator No 8 (Concourse to Platform, EFO 01), Escalator No 9 (Concourse to Platform, EFO 02), and Escalator No 10 (Street to Unpaid Concourse, A1 Entrance). The lifts include Lift No 01 (Concourse to Street, A2 Entrance), Lift No 03 (Concourse to Street, B1 Entrance), Lift No 05 (Concourse to Platform), Lift No 06 (Concourse to Platform), Lift No 08 (Street to FOB, A3 Entrance), and Lift No 09 (Street to FOB, A3 Entrance)."),
                ('Nehru Park', "Nehru Park Metro Station, also known as 'Nehru Park' has two platforms: Platform No 1 (towards St. Thomas Mount Metro) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features several escalators: Escalator No 1 (Street to Concourse Unpaid Area, A3 Entrance), Escalator No 3 (Street to Concourse Unpaid Area, B2 Entrance), Escalator No 5 (Street to Concourse Unpaid Area, A2 Entrance), Escalator No 11 (Concourse to Platform Paid Area, towards Chennai Central), and Escalator No 14 (Concourse to Platform Paid Area, towards St. Thomas Mount). The lifts include Lift No 1 (Street to Concourse Unpaid Area, A1 Entrance), Lift No 2 (Street to Concourse Unpaid Area, B1 Entrance), and Lift No 3 (Platform to Concourse Paid Area)."),
                ('Kilpauk', "Kilpauk Metro Station, also known as 'Kilpauk' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features several escalators: Escalator No 1 (Unpaid Concourse to Street, A2 Entrance), Escalator No 2 (Street to Unpaid Concourse, A2 Entrance), Escalator No 5 (Unpaid Concourse to Street, B3 Entrance), Escalator No 7 (Platform to Concourse, EFO 02), and Escalator No 10 (Platform to Concourse, EFO 01). The lifts include Lift No 1 (Street to Concourse, A2 Entrance), Lift No 2 (Street to Concourse, B2 Entrance), Lift No 3 (Concourse to Platform), Lift No 4 (Street to Subway, B3 Entrance), and Lift No 5 (Street to Subway, A3 Entrance)."),
                ("Pachaiyappa's College", "Pachaiyappa's College Metro Station, also known as 'Pachaiyappa's College,' 'Pachaiyappa's Metro' or simply 'Pachaiyappa's' has two platforms: Platform No 1 (towards Chennai Airport & St. Thomas Mount) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features several escalators: Escalator No 3 (Street to Unpaid Concourse, B3 Entrance), Escalator No 5 (Street to Unpaid Concourse, A1 Entrance), Escalator No 7 (Concourse to Platform, EFO 01), and Escalator No 10 (Concourse to Platform, EFO 02). The lifts include Lift No 1 (Concourse to Street, A1 Entrance), Lift No 2 (Concourse to Street, B1 Entrance), and Lift No 3 (Concourse to Platform)."),
                ('Shenoy Nagar', "Shenoy Nagar Metro Station, also known as 'Shenoy Nagar' has two platforms: Platform No 1 (towards Airport) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features several escalators: Escalator No 1 (Unpaid Concourse to Street, B2 Entrance), Escalator No 4 (Unpaid Concourse to Street, A3 Entrance), Escalator No 5 (Unpaid Concourse to Street, A2 Entrance), Escalator No 8 (Unpaid Concourse to Street, B3 Entrance), Escalator No 9 (Platform to Concourse, EFO 2), and Escalator No 12 (Platform to Concourse, EFO 1). The lifts include Lift No 1 (Unpaid Concourse to Street, B1 Entrance), Lift No 2 (Unpaid Concourse to Street, A1 Entrance), and Lift No 3 (Concourse to Platform)."),
                ('Anna Nagar East', "Anna Nagar East Metro Station, also known as 'Anna Nagar East' has two platforms: Platform No 1 (towards Chennai Airport & St. Thomas Mount) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features several escalators: Escalator No 05 (Street to Unpaid Concourse, A2 Entrance), Escalator No 04 (Street to Unpaid Concourse, A3 Entrance), Escalator No 07 (Street to Unpaid Concourse, B3 Entrance), Escalator No 12 (Platform to Concourse, EFO 01), and Escalator No 09 (Platform to Concourse, EFO 02). The lifts include Lift No 01 (Concourse to Street, A1 Entrance), Lift No 02 (Concourse to Street, B1 Entrance), Lift No 03 (Concourse to Platform), and Lift No 04 (Concourse to Street, B5 Entrance)."),
                ('Anna Nagar Tower', "Anna Nagar Tower Metro Station, also known as 'Anna Nagar Tower' has two platforms: Platform No 1 (towards St. Thomas Mount Metro) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features several escalators: Escalator No 1 (Unpaid Concourse to Street, B2 Entrance), Escalator No 3 (Unpaid Concourse to Street, A3 Entrance), Escalator No 4 (Unpaid Concourse to Street, A2 Entrance), Escalator No 9 (Platform to Concourse, EFO 02), and Escalator No 12 (Platform to Concourse, EFO 01). The lifts include Lift No 01 (Unpaid Concourse to Street, B1 Entrance), Lift No 02 (Unpaid Concourse to Street, A1 Entrance), and Lift No 03 (Paid Concourse to Platform)."),
                ('Thirumangalam', "Thirumangalam Metro Station, also known as 'Thirumangalam' has two platforms: Platform No 1 (towards Chennai Airport & St. Thomas Mount) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features several escalators: Escalator No 3 (Street to Unpaid Concourse, A3 Entrance), Escalator No 4 (Street to Unpaid Concourse, A2 Entrance), Escalator No 6 (Street to Unpaid Concourse, B2 Entrance), Escalator No 8 (Concourse to Platform, EFO 02), and Escalator No 11 (Concourse to Platform, EFO 01). The lifts include Lift No 01 (Street to Unpaid Concourse, A4 Entrance), Lift No 02 (Street to Unpaid Concourse, A1 Entrance), and Lift No 03 (Concourse to Platform)."),
                ('Koyambedu', "Koyambedu Metro Station, also known as 'Koyambedu' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro). The station features several escalators: Escalator No 1 (Street to Unpaid Concourse, A Entrance), Escalator No 2 (Street to Unpaid Concourse, A Entrance), Escalator No 3 (Street to Unpaid Concourse, B Entrance), Escalator No 4 (Concourse to Platform 01), Escalator No 5 (Concourse to Platform 01), and Escalator No 6 (Concourse to Platform 01). The lifts include Lift No 01 (Street to Unpaid Concourse, A Entrance), Lift No 02 (Paid Concourse to Platform 01, FOB), Lift No 03 (FOB to Platform 02), and Lift No 04 (Street to Unpaid Concourse, D Entrance)."),
                ('CMBT', "Puratchi Thalaivi Dr.J.Jayalalithaa CMBT Metro Station, also known as 'CMBT' 'CMBT Metro' 'Dr.J.Jayalalithaa CMBT Metro' and 'Jayalalithaa CMBT Metro' has two platforms: Platform No 1 (towards St.Thomas Mount Metro) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G.Ramachandran Central Metro). The station features several escalators: Escalator No 1 (Street to Unpaid Concourse, C Entrance), Escalator No 2 (Street to Unpaid Concourse, C Entrance), Escalator No 3 (Street to Unpaid Concourse, B Entrance), Escalator No 4 (Street to Unpaid Concourse, B Entrance), Escalator No 5 (Concourse to Platform 2), Escalator No 6 (Concourse to Platform 2), Escalator No 7 (Concourse to Platform 1), and Escalator No 8 (Concourse to Platform 1). The lifts include Lift No 1 (Street to Unpaid Concourse, C Entrance), Lift No 2 (Concourse to Platform 1), and Lift No 3 (Concourse to Platform 2)."),
                ('Arumbakkam', "Arumbakkam Metro Station, also known as 'Arumbakkam' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Puratchi Thalaivar Dr. M.G.Ramachandran Central Metro). The station features several escalators: Escalator No 1 (Street to Unpaid Concourse, A Entrance), Escalator No 2 (Street to Unpaid Concourse, A Entrance), Escalator No 3 (Street to Unpaid Concourse, B Entrance), Escalator No 4 (Concourse to Platform 1), Escalator No 5 (Concourse to Platform 1), and Escalator No 6 (Concourse to Platform 2). The lifts include Lift No 1 (Street to Unpaid Concourse, C Entrance), Lift No 2 (Street to Unpaid Concourse, D Entrance), Lift No 3 (Concourse to Platform 1), and Lift No 4 (Concourse to Platform 2)."),
                ('Vadapalani', "Vadapalani Metro Station, also known as 'Vadapalani' has two platforms: Platform No 1 (towards Chennai Airport & St.Thomas Mount) and Platform No 2 (towards Puratchi Thalaivar Dr.M.G.Ramachandran Central Metro). The station features several escalators: Escalator No E 01 (Street to Unpaid Concourse, A & B Entrances), Escalator No E 04 (Concourse to Unpaid Link Bridge), Escalator No E 05 (Link Bridge to Paid Platform 2), and Escalator No E 06 (Link Bridge to Paid Platform 1). The lifts include Lift No L 01 (Street to Unpaid Link Bridge, A & B Entrances), Lift No L 06 (Link Bridge to Paid Platform 2), Lift No L 07 (Link Bridge to Paid Platform 1), and Lift No L 08 (Street to Unpaid Link Bridge, C & D Entrances)."),
                ('Ashok Nagar', "Ashok Nagar Metro Station, also known as 'Ashok Nagar' has two platforms: Platform No 1 (towards St.Thomas Mount Metro & Chennai Airport) and Platform No 2 (towards Puratchi Thalaivar Dr.M.G.Ramachandran Central Metro). The station features several escalators: Escalator No 3 (Street to Unpaid Concourse, C Entrance), Escalator No 8 (Paid Concourse to PF 1), and Escalator No 9 (Paid Concourse to PF 2). The lifts include Lift No 01 (Paid Concourse to PF 1), Lift No 02 (Paid Concourse to PF 2), and Lift No 03 (Street to Unpaid Concourse, D Entrance)."),
                ('Ekkattuthangal', "Ekkattuthangal Metro Station, also known as 'Ekkattuthangal' has two platforms: Platform No 1 (towards Chennai Airport) and Platform No 2 (towards Puratchi Thalaivar Dr.M.G.Ramachandran Central Metro). The station features several escalators: Escalator No 1 (Street to Unpaid Concourse, A1 Entrance), Escalator No 2 (Concourse to Platform 2, EFO 02), and Escalator No 3 (Concourse to Platform 1, EFO 01). The lifts include Lift No 01 (Concourse to Street, A2 Entrance), Lift No 02 (Concourse to Platform), Lift No 03 (Concourse to Platform), and Lift No 04 (Concourse to Street, B1 Entrance)."),
                ('St. Thomas Mount', "St. Thomas Mount Metro Station, also known as 'St. Thomas Mount' has one platform: Platform No 1 (towards Puratchi Thalaivar Dr.M.G.Ramachandran Central Metro). The station features several escalators: Escalator No 3 (Street to Unpaid Concourse), Escalator No 4 (MRTS to Concourse), Escalator No 13 (Platform 1 to MRTS), Escalator No 9 (Concourse to MRTS), Escalator No 17 (MRTS to Platform 1), Escalator No 6 (Concourse to MRTS), Escalator No 14 (MRTS to Platform 2), Escalator No 10 (MRTS to Concourse), and Escalator No 18 (Platform 2 to MRTS). The lifts include Lift No 01 (Street to Concourse), Lift No 02 (Street to Concourse), Lift No 03 (Concourse to Platform 1), and Lift No 04 (Concourse to Platform 2).")
            ]

            # Insert Blue Line Stations
            cursor.executemany("INSERT INTO blue_line_stations (id, station_name, distance) VALUES (?, ?, ?)",
                           blue_line_data)

            # Insert Green Line Stations
            cursor.executemany("INSERT INTO green_line_stations (id, station_name, distance) VALUES (?, ?, ?)",
                           green_line_data)

            # Insert Station Details
            cursor.executemany("INSERT INTO station_details (station_name, platform_details) VALUES (?, ?)",
                           station_details_data)

            conn.commit()
            print("Data populated successfully")

        except sqlite3.Error as e:
            print(f"Error populating data: {e}")
        finally:
            conn.close()
    else:
        print("Error! cannot create database connection.")


def get_blue_line_stations():
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT station_name, distance FROM blue_line_stations")
        stations = [(row[0], row[1]) for row in cursor.fetchall()]  # (name, distance)
        return stations
    except sqlite3.Error as e:
        print(f"Error fetching blue line stations: {e}")
        return []
    finally:
        conn.close()


def get_green_line_stations():
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT station_name, distance FROM green_line_stations")
        stations = [(row[0], row[1]) for row in cursor.fetchall()]  # (name, distance)
        return stations
    except sqlite3.Error as e:
        print(f"Error fetching green line stations: {e}")
        return []
    finally:
        conn.close()

def get_station_details(station_name):
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT platform_details FROM station_details WHERE station_name = ?", (station_name,))
        result = cursor.fetchone()
        if result:
            return result[0] # Return the platform details
        else:
            return None # Station not found
    except sqlite3.Error as e:
        print(f"Error fetching station details: {e}")
        return None
    finally:
        conn.close()


@app.route('/')
def home():
    # Passing direct static path to the template
    user_logo_path = '/static/images/user_logo.png'
    gemini_logo_path = '/static/images/gemini_logo.svg'
    return render_template('index.html', user_logo=user_logo_path, gemini_logo=gemini_logo_path)


@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Retrieve the user's message and selected language from the request
        user_input = request.json.get('message')
        selected_lang = request.json.get('language', 'en-US')  # Default to English if not provided

        if not user_input:
            return jsonify({'error': 'No message provided'}), 400

        # ✅ Extract stations using Gemini
        print("For testingggggggggggggg the flow of user input!!!!!!!!!!",user_input)
        extraction_response = station_extraction(user_input)
        print("For testingggggggggggggg the flow of Station Extractionssss!!!!!!!!!!",extraction_response)
        source = extraction_response.get("src")
        destination = extraction_response.get("dest")
        single_station = extraction_response.get("station")

        print("🚉 Extracted Stations:", extraction_response)  # Debugging
        print("1111111111111111111111111111111111111111111111111111111111111111111111111111")
        # ✅ If only a single station is found, return that info
        if single_station and not source and not destination:
            return jsonify({'message': f"Detected station: {single_station}"})

        # ✅ If both source & destination are extracted, proceed with fetching route data
        print("2222222222222222222222222222222222222222222222222222222222222222222222222222")
        route_data = None
        if source and destination:
            conn = sqlite3.connect("route_data.db")
            cursor = conn.cursor()

            # ✅ Fetch route data from the database
            print("3333333333333333333333333333333333333333333333333333333333333333333333333333333")
            cursor.execute("SELECT * FROM route_data WHERE LOWER(source) = LOWER(?) AND LOWER(destination) = LOWER(?)",
                           (source.lower(), destination.lower()))
            row = cursor.fetchone()
            conn.close()

            if not row:
                print("333333333333333222222222222222233333333333333333222222222222222222222222222")
                return jsonify({'error': f'No route found for {source} to {destination}. Try another route.'}), 400

             # ✅ Fetch station data from the database
            print("444444444444444444444444444444444444444444444444444444444444444444444444444")
            source_station_details = get_station_details(source)
            print("55555555555555555555555555555555555555555555555555555555555555555555")
            destination_station_details = get_station_details(destination)
            print("66666666666666666666666666666666666666666666666666666666666666666666666")

            # ✅ Format the route data
            route_data = {
                "Source": row[1],
                "Destination": row[2],
                "Path": " → ".join(row[3].split(",")),
                "Interchange": row[4],
                "Source Platform Details": source_station_details, #use source data
                "Destination Platform Details": destination_station_details, #use des data
                "Line Color": row[7],
                "Line Symbol": row[8],
                "Source Platform Number": row[9],
                "Source Towards": row[10],
                "Destination Platform Number": row[11],
                "Destination Towards": row[12]
            }
            print("Debugging the route data's flowwwwwwwwwwwwwwwwwwwwwwwwwwww",route_data)  # Debugging

        # ✅ Fetch station data from the database
        blue_line_stations = get_blue_line_stations()
        green_line_stations = get_green_line_stations()

        # ✅ Format the Data
        blue_line_stations_str = "\n".join([f"{name}: {distance} km" for name, distance in blue_line_stations])
        green_line_stations_str = "\n".join([f"{name}: {distance} km" for name, distance in green_line_stations])

        # ✅ Ensure `route_data` exists before using it in `augmented_prompt`
        # ✅ Ensure `route_data` exists before using it in `augmented_prompt`
        if route_data:

            augmented_prompt = f"""
    **CRITICAL INFORMATION:** The following route details are **ABSOLUTELY CERTAIN and MUST BE USED EXACTLY AS PROVIDED**. Disregard any conflicting information(Do not say any values which are).

    Source Station: **{route_data["Source"]}**
    Source Platform Number: **{route_data["Source Platform Number"]}**
    Destination Station: **{route_data["Destination"]}**
    Destination Platform Number: **{route_data["Destination Platform Number"]}**
    Route Path (Stations in order): **{route_data["Path"]}**
    Interchange Required: **{route_data["Interchange"]}**

    **TASK: Based on the user's question, choose to include or not include the station details, platform details and also if needed to provide lift and escalator info (only when the user explicitly asks for it by mentioning "platform", "lift", "escalator", or similar keywords). Only show details relevant to what was asked and nothing more. Do not show the station details unless asked.**

    Source Platform Details: {route_data["Source Platform Details"]}
    Destination Platform Details: {route_data["Destination Platform Details"]}

    **UNDERSTAND AND UTILIZE THESE VALUES ABOVE ALL ELSE.**

    User Query: {user_input}

    Blue Line Stations: {blue_line_stations_str}
    Green Line Stations: {green_line_stations_str}

            """
        else:
            print("This is the else section for testing in ask() flow!!!!!!!!!!!!!!!!!!!!")
            augmented_prompt = f"""
            User Query: {user_input}
            Blue Line Stations: {blue_line_stations_str}
            Green Line Stations: {green_line_stations_str}
            """

        # ✅ Start a new chat session and process the user's message
        chat_session = model.start_chat(history=history)
        response = chat_session.send_message(augmented_prompt)
        model_response = response.text

        # ✅ Strip unnecessary punctuation marks before applying TTS
        response_text = re.sub(r'[*_#]', '', model_response)  # Remove *, _, #

        # ✅ Generate speech audio using the selected language and overwrite the temp file
        tts = gTTS(text=response_text, lang=selected_lang)
        tts.save(TEMP_AUDIO_PATH)

        # ✅ Update the history with user input and model response
        history.append({"role": "user", "parts": [user_input]})
        history.append({"role": "model", "parts": [model_response]})

        # ✅ Add a timestamp to the audio URL to force reload
        timestamp = int(time.time())  # Unique value based on current time
        audio_url = f'/{TEMP_AUDIO_PATH}?t={timestamp}'  # Add query parameter to force refresh

        # ✅ Return the response text and the updated audio URL
        return jsonify({'response': model_response, 'audio_url': audio_url})

    except Exception as e:
        # Handle exceptions and log them
        print(f"❌ Error in /ask: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/extract_stations', methods=['POST'])
def extract_stations_gemini():
    data = request.json
    user_message = data.get("message", "")

    prompt = f"Extract the source and destination metro stations from this text: '{user_message}'. Return only the station names separated by ' to '. Example: 'Egmore to Teynampet'."

    response = model.generate_content(prompt)
    
    if response and response.text:
        station_text = response.text.strip().replace("\n", " ")  # Remove newlines

        # Ensure correct format with ' to ' separator
        if " to " in station_text:
            stations = station_text.split(" to ")
            if len(stations) == 2:
                return jsonify({"src": stations[0].strip(), "dest": stations[1].strip()})

        # If response format is incorrect, return an error message
        print("❌ Unexpected station format:", station_text)  # Debugging
        return jsonify({"error": f"Could not extract stations from: '{station_text}'"}), 400

    print("❌ Failed to get response from Gemini API.")
    return jsonify({"error": "Failed to process request"}), 400








































def station_extraction(user_input):
    """
    Uses Gemini AI to extract station names (source & destination) from user input.
    Returns JSON with `src` and `dest` if both are found, or `station` if only one is detected.
    Now using simple string extraction instead of JSON.
    """
    try:
        # ✅ Gemini Model Configuration
        genai.configure(api_key="AIzaSyBP5uV1TfyN5Mh3SPAegcqhDp4QAOFOFg8")  # Replace with your API key
        model = genai.GenerativeModel("gemini-2.0-flash")

        # ✅ Define the prompt for Gemini (Simpler)
        prompt = f"""
You are a station name extraction tool for the Chennai Metro.
Your SOLE TASK is to extract metro station names from the user query.
Respond with the station names separated by " to ".

However, for these particular stations, pay close attention to:

* Arignar Anna Alandur (Alandur): Ensure "Arignar Anna Alandur (Alandur)" or "Alandur" is extracted.
* Meenambakkam:  Ensure "Meenambakkam" or "Meenambakkam Metro" is extracted.
* OTA - Nanganallur Road: Ensure "OTA - Nanganallur Road" or "Nanganallur Road" is extracted.
* Tollgate Metro: Ensure "Tollgate Metro" or "Tollgate" is extracted.
* Tondiarpet Metro: Ensure "Tondiarpet Metro" or "Tondiarpet" is extracted.
* Ekkattuthangal: Ensure "Ekkattuthangal" or "Ekkattuthangal Metro" is extracted
* Thousand Lights: Ensure "Thousand Lights" or "Thousand Lights Metro" is extracted
* Pachaiyappa's College: "Pachaiyappa's College", "Pachaiyappa's College Metro" or "Pachaiyappa's"
* Guindy: "Guindy" or "Guindy Metro"
* airport: Ensure "airport" or "Chennai International Airport" is extracted.
* New Washermenpet: Ensure "New Washermenpet" or "New Washermenpet Metro" is extracted.
* Koyambedu: Ensure "Koyambedu" or "Koyambedu Metro" is extracted.
* Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central):  Ensure "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)", "Chennai Central", or "Central" is extracted.

- If two station names are found: "Source Station to Destination Station"
- If only one station is detected: "Station: Detected Station"
- If no station is found: "Error: No station detected."

User Query: "{user_input}"

RESPONSE:
"""

        # ✅ Send the request to Gemini
        response = model.generate_content(prompt)
        result = response.text.strip()

        # ✅ Simple String Parsing
        if " to " in result:
            parts = result.split(" to ")
            if len(parts) == 2:
                return {"src": parts[0].strip(), "dest": parts[1].strip()}
        elif "Station:" in result:
            station_name = result.replace("Station:", "").strip()
            return {"station": station_name}
        elif "Error:" in result:
            return {"error": "No station detected."}
        else:
            print(f"❌ Unexpected response format: {result}")  # Debugging
            return {"error": "Failed to extract station names."}

    except Exception as e:
        print(f"❌ Error in station_extraction: {e}")
        return {"error": "Failed to extract station names due to API error."}

def fetch_stations():
    """Fetches station names and distances from the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect("chennai_metro.db")  # Replace with actual DB
        cursor = conn.cursor()

        # Fetch Blue Line stations
        cursor.execute("SELECT station_name, distance FROM blue_line_stations")
        blue_line_data = cursor.fetchall()

        # Fetch Green Line stations
        cursor.execute("SELECT station_name, distance FROM green_line_stations")
        green_line_data = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"🚨 Database Error: {e}")
        return [], [], [], []  # Return empty lists on failure

    finally:
        conn.close()  # Ensure the connection is always closed

    # Convert data into lists
    blue_line_stations = [station[0] for station in blue_line_data]
    blue_line_distances = [station[1] for station in blue_line_data]

    green_line_stations = [station[0] for station in green_line_data]
    green_line_distances = [station[1] for station in green_line_data]

    return blue_line_stations, blue_line_distances, green_line_stations, green_line_distances

# ✅ Fetch station data once
blue_stations, blue_distances, green_stations, green_distances = fetch_stations()



@app.route('/receive_route_data', methods=['POST'])
def receive_route_data():
    print("🚀 Receiving new route data...")

    try:
        data = request.get_json()
        source = data.get("source")
        destination = data.get("destination")
        line_color = data.get("line_color")

        source_details = data.get("source_platform_details", {})
        destination_details = data.get("destination_platform_details", {})

        source_platform_num, source_towards = get_platform_and_direction(
            source, destination, source_details.get("platform_details", ""), line_color
        )

        destination_platform_num, destination_towards = get_platform_and_direction(
            destination, source, destination_details.get("platform_details", ""), line_color
        )

        route_data = {
            "source": source,
            "destination": destination,
            "path": ",".join(data.get("path", [])),  # Store list as comma-separated values
            "interchange": data.get("interchange", "None"),
            "source_platform_details": str(source_details),
            "destination_platform_details": str(destination_details),
            "line_color": line_color,
            "line_symbol": data.get("line_symbol", ""),
            "source_platform_num": source_platform_num,
            "source_towards": source_towards,
            "destination_platform_num": destination_platform_num,
            "destination_towards": destination_towards
        }

        conn = sqlite3.connect("route_data.db", timeout=10)  
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")  
        conn.commit()

        # ✅ Delete old entry before inserting new data
        cursor.execute("DELETE FROM route_data WHERE source = ? AND destination = ?", (source, destination))
        conn.commit()

        # ✅ Insert new route data
        cursor.execute('''INSERT INTO route_data 
            (source, destination, path, interchange, source_platform_details, destination_platform_details, 
            line_color, line_symbol, source_platform_num, source_towards, destination_platform_num, destination_towards) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
            (source, destination, route_data["path"], route_data["interchange"],
             route_data["source_platform_details"], route_data["destination_platform_details"],
             route_data["line_color"], route_data["line_symbol"],
             route_data["source_platform_num"], route_data["source_towards"],
             route_data["destination_platform_num"], route_data["destination_towards"])
        )

        conn.commit()  # ✅ Ensure data is saved
        time.sleep(1)  # ✅ Allow DB to register update before `/ask` queries it
        conn.close()  

        print(f"✅ Updated Route Data: {route_data}") 
        global route2data 
        route2data = route_data
        print("The copied value of route_data in route2dataaaaaaaaaaaa :",route2data) 
        return jsonify(route_data), 200

    except Exception as e:
        print(f"❌ Error in receive_route_data: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@app.route('/check_booking_intent', methods=['POST'])
def check_booking_intent():
    """Determine if user wants to book a ticket using Gemini Flash model."""
    try:
        data = request.json
        user_input = data.get("message", "").strip()

        print(f"📝 User Message: {user_input}")  # Debugging Log

        user_message_lower = user_input.lower()

        # 🔹 **Regex for Booking Intent Detection**
        booking_regex = re.compile(
            r"\b(book|buy|purchase|reserve|get|obtain|need|wanna|want)\s*"
            r"(a\s*)?(ticket|metro\s*ticket|train\s*ticket|railway\s*ticket|pass|ride)\b",
            re.IGNORECASE
        )

        is_booking_regex_match = bool(booking_regex.search(user_message_lower))

        # 🔹 **Strict Gemini Prompt for YES/NO Classification**
        prompt = f"""
        User Message: "{user_input}"

        **Task:** Return ONLY "YES" or "NO" (nothing else).

        **Return "YES" if:**
        - The message expresses a direct or indirect intent to *book, buy, purchase, reserve, or obtain* a metro/train ticket.
        - It contains words like "book a ticket", "buy metro ticket", "need railway pass", "wanna get a train ticket".
        - Informal requests like "I wanna book a ticket" must still be classified as "YES".

        **Return "NO" if:**
        - The user is asking for schedules, prices, routes, or general info.
        - The message does NOT clearly mention ticket booking.

        **STRICT RULES:**
        - **DO NOT** explain the response.
        - **DO NOT** add extra words.
        - **RESPOND ONLY WITH "YES" OR "NO".**
        """

        # 🔹 **Call Gemini API**
        response = model.generate_content(prompt)

        print(f"🔍 Raw Gemini Response: {response}")  # Debugging Log

        # Extract and sanitize Gemini’s response
        intent_text = response.text.strip().upper() if response and response.text else "NO"
        print(f"🔍 Gemini Intent Response: {intent_text}")  # Debugging Log

        # 🔹 **Final Decision (Override Gemini If Regex Matches)**
        if intent_text == "YES" or is_booking_regex_match:
            result = {
                "isBookingIntent": True,
                "response": "You can book tickets using our ticketing bot. Click below to proceed."
            }
        else:
            result = {
                "isBookingIntent": False,
                "response": "I'm designed to assist with Chennai Metro and Railway travel only. Please use a different service for booking tickets."
            }

        print(f"📩 Final API Response: {result}")  # Debugging Log
        return jsonify(result)
    except Exception as e:
        print(f"🚨 Exception in Booking Intent API: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500



def get_platform_and_direction(station, destination, platform_details, line_color):
    """
    Determines the platform number and direction based on station order.
    """
    print("For testing get_platform_and_direction function starting point !!!!!!!!!!!!!!!!!! ")
    try:
        print("For testing get_platform_and_direction function Middle point after assigning index 1 !!!!!!!!!!!!!!!!!! ")
        # ✅ Select correct station list
        stations = (
    green_stations + blue_stations if line_color == "Blue to Green"  # BOTH lines
    else blue_stations + green_stations if line_color == "Green to Blue"  # BOTH lines
    else blue_stations if line_color == "Blue Line"                  # Blue line only
    else green_stations if line_color == "Green Line"                # Green line only
    else []                                                          # No valid line
)

        if not stations or station not in stations or destination not in stations:
            return "Unknown", "Unknown"

        # ✅ Determine travel direction
        station = station.replace("Metro", "").strip()
        destination = destination.replace("Metro", "").strip()
        station_index = stations.index(station)
        destination_index = stations.index(destination)

        print("For testing get_platform_and_direction function Middle point after assigning index 2 !!!!!!!!!!!!!!!!!! ")

        travel_direction = (
            f"Towards {stations[-1]}" if station_index < destination_index
            else f"Towards {stations[0]}"
        )

        print(f"🔄 Travel direction from {station} to {destination}: {travel_direction}")  # DEBUG LOG

        # ✅ Fetch platform details from DB
        details = get_station_details_from_db(station)
        platforms = details.get("platforms", [])

        if not platforms:
            return "Unknown", "Unknown"

        # ✅ Choose correct platform with flexible matching
        for platform in platforms:
            db_direction = platform["direction"].lower().replace("towards ", "").strip()
            expected_direction = travel_direction.lower().replace("towards ", "").strip()

            if expected_direction in db_direction or db_direction in expected_direction:
                return platform["platform_no"], platform["direction"]

        # ✅ Fallback if no exact match
        return platforms[0]["platform_no"], platforms[0]["direction"]

    except Exception as e:
        print(f"❌ Error in get_platform_and_direction: {e}")
        return "Unknown", "Unknown"


def get_latest_route_data():
    """Returns the latest route data dynamically."""
    global latest_route_data
    return latest_route_data  # Always returns the most updated data


def get_station_details_from_db(station_name):
    print("For testinggggggggggggggggg", station_name)
    """Fetch platform, lift, and escalator details from SQLite DB with flexible name matching."""
    conn = sqlite3.connect("NewMetroDetails.db")
    cursor = conn.cursor()

    # ✅ Normalize station name (remove special characters, spaces, dots)
    formatted_name = station_name.replace(".", "").replace("(", "").replace(")", "").replace(" ", "").lower()
    print(f"Formatted station name after normalization-----------------------> {formatted_name}")

    # ✅ Try exact match first (checking both `station_name` and `alias`)
    cursor.execute("""
        SELECT id FROM stations 
        WHERE REPLACE(LOWER(station_name), '.', '') = ? 
        OR REPLACE(LOWER(alias), '.', '') = ?
    """, (formatted_name, formatted_name))
    station_id = cursor.fetchone()
    print("station id through station_name and alias----------------------->", station_id)

    # ✅ If no exact match, use LIKE-based lookup
    if not station_id:
        cursor.execute("""
            SELECT id FROM stations 
            WHERE LOWER(station_name) LIKE ? 
            OR LOWER(alias) LIKE ?
        """, (f"%{formatted_name}%", f"%{formatted_name}%"))
        station_id = cursor.fetchone()
        print("station id through LIKE-based lookup----------------------->", station_id)
    
    if not station_id:
        cursor.execute("""
            SELECT id FROM stations 
            WHERE REPLACE(REPLACE(LOWER(station_name), ' ', ''), '.', '') LIKE ? 
            OR REPLACE(REPLACE(LOWER(alias), ' ', ''), '.', '') LIKE ?
        """, (f"%{formatted_name}%", f"%{formatted_name}%"))
        station_id = cursor.fetchone()
        print("station id through AGGRESSIVE LIKE-based lookup----------------------->", station_id)

    # ✅ Check if alias has 'Central' to handle cases like '(Chennai Central)' and compare
    if not station_id:
        print("\nTrying alias-based check for 'Central' presence----------------------->")
        cursor.execute("""
            SELECT id, alias FROM stations
        """)
        all_stations = cursor.fetchall()

        # Debugging all station aliases
        print("\nChecking against alias for 'Central':")
        for row in all_stations:
            db_station_alias = row[1] if row[1] else ""
            print(f"DB Alias: {db_station_alias} (Normalized: {db_station_alias.replace('.', '').replace(' ', '').lower()})")
            
            # If 'Central' is in the alias, check it
            if 'central' in db_station_alias.replace('.', '').replace(' ', '').lower():
                cursor.execute("""
                    SELECT id FROM stations 
                    WHERE LOWER(alias) LIKE ? 
                """, (f"%central%",))
                station_id = cursor.fetchone()
                print(f"Station ID found based on 'Central' match: {station_id}")

    if not station_id:
        print(f"⚠️ Station not found in DB: {station_name}")
        return {"platforms": [], "lifts_escalators": []}

    station_id = station_id[0]
    print("station id changed the values????----------------------->", station_id)
    
    # ✅ Fetch platform details
    cursor.execute("SELECT platform_no, direction FROM platforms WHERE station_id = ?", (station_id,))
    platforms = [{"platform_no": p[0], "direction": p[1]} for p in cursor.fetchall()]

    # ✅ Fetch lifts/escalators details
    cursor.execute("SELECT name, floor, location FROM lifts_escalators WHERE station_id = ?", (station_id,))
    lifts_escalators = [{"name": le[0], "floor": le[1], "location": le[2]} for le in cursor.fetchall()]

    conn.close()

    return {"platforms": platforms, "lifts_escalators": lifts_escalators}



















































if __name__ == '__main__':
    create_tables()
    ## populate_database() # Call this ONLY ONCE to populate the DB
    app.run(debug=True)