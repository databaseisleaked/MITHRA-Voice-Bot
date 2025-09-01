from flask import Flask, render_template, request, jsonify, url_for
import google.generativeai as genai
import os
from dotenv import load_dotenv
from gtts import gTTS
import time
import re
from waitress import serve
import sqlite3
import json
import requests


DATABASE_NAME = 'chennai_metro.db'  # Define your db name

# Ensure the static/audio folder exists
audio_folder = 'static/audio'
if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)

# Temporary audio file path
TEMP_AUDIO_PATH = os.path.join(audio_folder, 'temp_audio.mp3')


genai.configure(api_key="AIzaSyBP5uV1TfyN5Mh3SPAegcqhDp4QAOFOFg8")

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}


app = Flask(__name__)

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

        # Start a new chat session and process the user's message
        chat_session = model.start_chat(history=history)

        data_dict = {
    "source": "Station A",
    "destination": "Station B",
    "line_color": "Blue",
    "source_platform_details": {"platform_details": "Platform 1"},
    "destination_platform_details": {"platform_details": "Platform 2"},
    "path": ["Station A", "Interchange 1", "Station B"],
    "interchange": "Interchange 1",
    "line_symbol": "B1"
}

        result = route_data_py(data_dict)

        print("📍 Final Route Dataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:", result)



        response = chat_session.send_message(user_input)
        model_response = response.text

        # Strip unnecessary punctuation marks before applying TTS
        response_text = re.sub(r'[*_#]', '', model_response)  # Remove *, _, #


        # Generate speech audio using the selected language and overwrite the temp file
        tts = gTTS(text=response_text, lang=selected_lang)
        tts.save(TEMP_AUDIO_PATH)  # Save the new response to the same file

        # Update the history with user input and model response
        history.append({"role": "user", "parts": [user_input]})
        history.append({"role": "model", "parts": [model_response]})

        # Add a timestamp to the audio URL to force reload
        timestamp = int(time.time())  # Unique value based on current time
        audio_url = f'/{TEMP_AUDIO_PATH}?t={timestamp}'  # Add query parameter to force refresh

        # Return the response text and the updated audio URL
        return jsonify({'response': model_response, 'audio_url': audio_url})

    except Exception as e:
        # Handle exceptions and log them
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

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


latest_route_data = {
    "source": "Unknown",
    "destination": "Unknown",
    "path": [],
    "interchange": "None",
    "source_platform_details": "Details not available",
    "destination_platform_details": "Details not available",
    "line_color": "Unknown",
    "line_symbol": "❓",
    "source_platform_num": None,  # Placeholder for source platform number
    "source_towards": "Unknown",  # Placeholder for source travel direction
    "destination_platform_num": None,  # Placeholder for destination platform number
    "destination_towards": "Unknown"  # Placeholder for destination travel direction
}

model = genai.GenerativeModel("gemini-2.0-flash", generation_config=generation_config, system_instruction=f"""
    You are MITHRA, a multilingual voice bot for Chennai Metro Railways. Your sole purpose is to provide users with accurate travel information exclusively in their preferred language. You should respond in the same language as the user without asking for clarification. You should only provide details related to the Chennai Metro Railways (no need to mention suburban rails, cabs, autos, walking, etc.).

    Languages: English (primary), Tamil, Hindi (respond in the same language as the user's prompt).

    These lists are for your own reference to know the stations, but you must strictly follow the provided data for routes (with or without interchange). Do not generate routes based on the list but based on the data provided in the prompt.

    Blue Line stations: {", ".join(blue_stations)}
    Green Line stations: {", ".join(green_stations)}

    Route Structure:
    - Start: {latest_route_data["source"]}
    - Destination: {latest_route_data["destination"]}
    - Path: {', '.join(latest_route_data["path"])}
    - Interchange: {latest_route_data["interchange"] if latest_route_data["interchange"] != "None" else "No interchange"}
    - Source Platform: {latest_route_data["source_platform_num"] if latest_route_data["source_platform_num"] else "Unknown"}
    - Destination Platform: {latest_route_data["destination_platform_num"] if latest_route_data["destination_platform_num"] else "Unknown"}
    - Travel Direction from Source: {latest_route_data["source_towards"] if latest_route_data["source_towards"] else "Unknown"}
    - Travel Direction to Destination: {latest_route_data["destination_towards"] if latest_route_data["destination_towards"] else "Unknown"}

    👉 **If the user asks about lifts and escalators, provide:**  
       - **Lifts and Escalator - Source:** {latest_route_data["source_platform_details"]}
       - **Lifts and Escalator - Destination:** {latest_route_data["destination_platform_details"]}

    Example Routing Template (use this only for structural guidance, not hardcoded content):
    Route from {latest_route_data["source"]} to {latest_route_data["destination"]}:
    1. **Go to Platform No {latest_route_data["source_platform_num"] if latest_route_data["source_platform_num"] else "X"} (towards {latest_route_data["source_towards"] if latest_route_data["source_towards"] else "<Direction>"}).**
    2. **Board the {latest_route_data["line_color"]} train and travel through:**  
       ◉ <Station1> → <Station2> → <Station3> → ...
    3. **(If interchange is necessary) Switch lines at {latest_route_data["interchange"]} and board the corresponding train.**
    4. **Alight at {latest_route_data["destination"]} Metro Station (Platform {latest_route_data["destination_platform_num"] if latest_route_data["destination_platform_num"] else "Y"}, towards {latest_route_data["destination_towards"] if latest_route_data["destination_towards"] else "<Direction>"}).**

    🟦 Blue Line - Platform {latest_route_data["source_platform_num"] if latest_route_data["source_platform_num"] else "X"} → Towards {latest_route_data["source_towards"] if latest_route_data["source_towards"] else "<Direction>"}
    🟩 Green Line - Platform {latest_route_data["destination_platform_num"] if latest_route_data["destination_platform_num"] else "Y"} → Towards {latest_route_data["destination_towards"] if latest_route_data["destination_towards"] else "<Direction>"}

    🚆 Total journey distance: Approximately <Distance> km  
    ⏳ Estimated travel time: <Time> minutes (excluding transfer time at interchange station)  
    ⏳ Transfer time: Allow an extra <Time> minutes (if interchange exists)  

    Example Output (With Lifts & Escalators if asked):  
    1. **Go to Platform No {latest_route_data["source_platform_num"] if latest_route_data["source_platform_num"] else "X"} (towards {latest_route_data["source_towards"] if latest_route_data["source_towards"] else "<Direction>"}).**  
       (The station has multiple lifts: Lift 1 (Street to Unpaid Concourse, A2 Entrance), Lift 2 (Street to Unpaid Concourse, B2 Entrance), etc.)  
    2. **Board the {latest_route_data["line_color"]} train and travel through:**  
       ◉ <Station1> → <Station2> → <Station3> → ...  
    3. **(If interchange is necessary) Switch lines at {latest_route_data["interchange"]} and board the corresponding train.**  
    4. **Alight at {latest_route_data["destination"]} Metro Station (Platform {latest_route_data["destination_platform_num"] if latest_route_data["destination_platform_num"] else "Y"}, towards {latest_route_data["destination_towards"] if latest_route_data["destination_towards"] else "<Direction>"}).**  
       (The station has multiple escalators: Escalator 1 (Street to Unpaid Concourse, A Entrance), etc.)  

    🟦 Blue Line - Platform {latest_route_data["source_platform_num"] if latest_route_data["source_platform_num"] else "X"} → Towards {latest_route_data["source_towards"] if latest_route_data["source_towards"] else "<Direction>"}  
    🟩 Green Line - Platform {latest_route_data["destination_platform_num"] if latest_route_data["destination_platform_num"] else "Y"} → Towards {latest_route_data["destination_towards"] if latest_route_data["destination_towards"] else "<Direction>"}  

    🚆 Total journey distance: Approximately <Distance> km  
    ⏳ Estimated travel time: <Time> minutes (excluding transfer time at interchange station)  
    ⏳ Transfer time: Allow an extra <Time> minutes  

    For specific station lift details, respond as follows:  
    **station_name Metro has the following lifts available:**  
    1. **Lift No 1:** Connects the Street to the Concourse (A2 Entrance).  
    2. **Lift No 2:** Connects the Street to the Concourse (B2 Entrance).  
    3. **Lift No 3:** Connects the Concourse to the Platforms.  
    ...  

    👉 **If the user asks about lifts and escalators, provide:**  
    1. **Lifts and Escalator - Source:** {latest_route_data["source_platform_details"]}  
    2. **Lifts and Escalator - Destination:** {latest_route_data["destination_platform_details"]}  

    The platform details can be taken from that too.
""")

history = []
print(latest_route_data["path"])




def get_latest_route_data():
    """Returns the latest route data dynamically."""
    global latest_route_data
    return latest_route_data  # Always returns the most updated data


def get_station_details_from_db(station_name):
    """Fetch platform, lift, and escalator details from SQLite DB with flexible name matching."""
    conn = sqlite3.connect("NewMetroDetails.db")
    cursor = conn.cursor()

    # ✅ Attempt exact match
    cursor.execute("SELECT id FROM stations WHERE station_name = ?", (station_name,))
    station_id = cursor.fetchone()

    # ✅ If no exact match, try LIKE-based lookup
    if not station_id:
        cursor.execute("SELECT id FROM stations WHERE station_name LIKE ?", (f"%{station_name}%",))
        station_id = cursor.fetchone()

    if not station_id:
        print(f"⚠️ Station not found in DB: {station_name}")
        return {"platforms": [], "lifts_escalators": []}

    station_id = station_id[0]

    # ✅ Fetch platform details
    cursor.execute("SELECT platform_no, direction FROM platforms WHERE station_id = ?", (station_id,))
    platforms = [{"platform_no": p[0], "direction": p[1]} for p in cursor.fetchall()]

    # ✅ Fetch lifts/escalators details
    cursor.execute("SELECT name, floor, location FROM lifts_escalators WHERE station_id = ?", (station_id,))
    lifts_escalators = [{"name": le[0], "floor": le[1], "location": le[2]} for le in cursor.fetchall()]

    conn.close()
    
    return {"platforms": platforms, "lifts_escalators": lifts_escalators}

def get_correct_platform(station_name, travel_direction):
    """
    Selects the correct platform based on the direction of travel.
    """
    platform_data = get_station_details_from_db(station_name).get("platforms", [])

    for platform in platform_data:
        db_direction = platform["direction"].lower().replace("towards ", "").strip()
        expected_direction = travel_direction.lower().replace("towards ", "").strip()

        if expected_direction in db_direction:
            return platform["platform_no"], platform["direction"]

    return "Unknown", "Unknown"  # Fallback if no match is found


def get_platform_and_direction(station, destination, platform_details, line_color):
    """
    Determines the platform number and direction based on station order.
    """
    try:
        # ✅ Select correct station list
        stations = (
            blue_stations if line_color == "Blue Line"
            else green_stations if line_color == "Green Line"
            else []
        )

        if not stations or station not in stations or destination not in stations:
            return "Unknown", "Unknown"

        # ✅ Determine travel direction
        station_index = stations.index(station)
        destination_index = stations.index(destination)

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





def route_data_py(data):
    try:
        url = "http://127.0.0.1:8000/receive_route_data"  # Adjust if Flask runs on a different host/port
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: Received {response.status_code} from Flask API")
            return {"error": "Failed to retrieve route data"}

    except Exception as e:
        print(f"❌ Exception in route_data_py: {e}")
        return {"error": "Something went wrong"}


@app.route('/receive_route_data', methods=['POST'])
def receive_route_data():
    try:
        data = request.get_json()
        source = data.get("source")
        destination = data.get("destination")
        line_color = data.get("line_color")

        # ✅ Extract platform details
        source_details = data.get("source_platform_details", {})
        destination_details = data.get("destination_platform_details", {})

        # ✅ Use function to determine platform & direction
        source_platform_num, source_towards = get_platform_and_direction(
            source, destination, source_details.get("platform_details", ""), line_color
        )

        destination_platform_num, destination_towards = get_platform_and_direction(
            destination, source, destination_details.get("platform_details", ""), line_color
        )

        # ✅ Construct response dictionary
        route_data = {
            "source": source,
            "destination": destination,
            "path": data.get("path", []),
            "interchange": data.get("interchange", "None"),
            "source_platform_details": source_details,
            "destination_platform_details": destination_details,
            "line_color": line_color,
            "line_symbol": data.get("line_symbol", ""),
            "source_platform_num": source_platform_num,
            "source_towards": source_towards,
            "destination_platform_num": destination_platform_num,
            "destination_towards": destination_towards
        }

        print(f"✅ Updated Route Data: {route_data}")  # Debugging Log
        return jsonify(route_data), 200

    except Exception as e:
        print(f"❌ Error in receive_route_data: {e}")
        return jsonify({"error": "Something went wrong"}), 500


def get_station_details(station_name):
    """
    Retrieves lift and escalator details for a specific metro station from the database.

    Args:
        station_name (str): The name of the metro station to query.

    Returns:
        dict: A dictionary containing the platform details or an error message.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT platform_details FROM station_details WHERE station_name = ?", (station_name,))
        result = cursor.fetchone()

        if result:
            platform_details = result[0]  # Extract platform details string
            return {"station_name": station_name, "platform_details": platform_details}
        else:
            return {"error": "Station not found"}

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {"error": "Database error"}
    
    finally:
        if conn:
            conn.close()



def extract_lift_details(platform_details):
    """
    Extracts lift details from the platform_details string.  This assumes a
    specific format for the string.  Adjust the logic if your data format is different.

    Args:
        platform_details (str): The platform details string from the database.

    Returns:
        list: A list of strings, where each string is a description of a lift.
              Returns an empty list if no lift details are found or if the format is unexpected.
    """
    lift_details = []
    if platform_details:  # Check if platform_details is not None
        lines = platform_details.splitlines()
        for line in lines:
            if "Lift No" in line:
                lift_details.append(line.strip()) # Strip to remove leading/trailing whitespace

    return lift_details


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
    



if __name__ == '__main__':
    serve(app, host='127.0.0.1', port=8000)






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

        # ✅ If only a single station is found, return that info
        if single_station and not source and not destination:
            return jsonify({'message': f"Detected station: {single_station}"})

        # ✅ If both source & destination are extracted, proceed with fetching route data
        route_data = None
        if source and destination:
            conn = sqlite3.connect("route_data.db")
            cursor = conn.cursor()

            # ✅ Fetch route data from the database
            cursor.execute("SELECT * FROM route_data WHERE LOWER(source) = LOWER(?) AND LOWER(destination) = LOWER(?)",
                           (source.lower(), destination.lower()))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return jsonify({'error': f'No route found for {source} to {destination}. Try another route.'}), 400

             # ✅ Fetch station data from the database
            source_station_details = get_station_details(source)
            destination_station_details = get_station_details(destination)

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
    **CRITICAL INFORMATION:** The following route details are **ABSOLUTELY CERTAIN and MUST BE USED EXACTLY AS PROVIDED**. Disregard any conflicting information.

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