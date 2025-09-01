document.addEventListener("DOMContentLoaded", () => {
  // Selecting DOM elements
  const typingForm = document.querySelector(".typing-form");
  const chatContainer = document.querySelector(".chat-list");
  const suggestions = document.querySelectorAll(".suggestion");
  const toggleThemeButton = document.querySelector("#theme-toggle-button");
  const deleteChatButton = document.querySelector("#delete-chat-button");
  const micIcon = document.querySelector(".mic-icon");

  // Selecting the language-selector elements
  const languageSelector = document.getElementById("language-selector");
  const greetingText = document.getElementById("greeting-text");
  const subtitleText = document.getElementById("subtitle-text");
  const suggestionTexts = document.querySelectorAll(".suggestion .text");

  // Translation Data
  const translations = {
    "en-US": {
      "greeting": "Hello, there",
      "subtitle": "Please provide your Chennai Metro queries.",
      "q1": "How can I travel from Koyambedu to Washermanpet through metro?",
      "q2": "What is the nearest metro station to Nungambakkam?",
      "q3": "Tell me the quickest route from Thirumangalam to Guindy",
      "q4": "Give me the Metro details for Nungambakkam to Anna Nagar",
      "placeholder-query": "Enter your queries here",
      "instruction": "This is a Voice Bot that can only be used for Chennai Metro passenger assistance."
    },
    "ta": {
      "greeting": "வணக்கம்",
      "subtitle": "உங்கள் சென்னை மெட்ரோ கேள்விகளை வழங்கவும்.",
      "q1": "கோயம்பேடு முதல் வாஷ்மென்பேட் வரை மெட்ரோவில் பயணிக்க எப்படி?",
      "q2": "நுங்கம்பாக்கத்திற்கு அருகிலுள்ள மெட்ரோ நிலையம் எது?",
      "q3": "திருமங்கலம் முதல் கிண்டி வரை விரைவான பாதை எது?",
      "q4": "நுங்கம்பாக்கம் முதல் அண்ணா நகர் வரை மெட்ரோ விவரங்களை வழங்கவும்.",
      "placeholder-query": "உங்கள் கேள்விகளை இங்கே உள்ளிடவும்",
      "instruction": "இந்த வோய்ஸ் போட் சென்னை மெட்ரோ பயணிகளுக்கு மட்டுமே உதவ பயன்படுத்தப்படுகிறது."
    },
    "hi": {
      "greeting": "नमस्ते",
      "subtitle": "कृपया अपनी चेन्नई मेट्रो से संबंधित प्रश्न प्रदान करें।",
      "q1": "कोयंबेडु से वॉशरमैनपेट तक मेट्रो से कैसे यात्रा करें?",
      "q2": "नुंगमबक्कम के सबसे नज़दीकी मेट्रो स्टेशन कौन सा है?",
      "q3": "तिरुमंगलम से गुइंडी के लिए सबसे तेज़ मार्ग कौन सा है?",
      "q4": "नुंगमबक्कम से अन्ना नगर तक मेट्रो विवरण दें।",
      "placeholder-query": "अपनी क्वेरी यहाँ दर्ज करें",
      "instruction": "यह वॉयस बॉट केवल चेन्नई मेट्रो यात्रियों की सहायता के लिए है।"
    }
  };
// Function to type text with a typing effect
function typeText(element, text, speed) {
  let i = 0;
  element.textContent = ""; // Clear any existing content
  const intervalId = setInterval(() => {
      element.textContent += text.charAt(i); // Append one character at a time
      i++;
      if (i === text.length) {
          clearInterval(intervalId); // Stop typing once all text is displayed
      }
  }, speed); // Adjust speed to control typing speed (milliseconds per character)
}

// Function to update the text content based on selected language
const updateText = (lang) => {
  // Update greeting text (this doesn't need typing effect)
  greetingText.textContent = translations[lang].greeting;

  // Apply typing effect to subtitle
  const subtitleText = document.getElementById("subtitle-text");
  typeText(subtitleText, translations[lang].subtitle, 95); // Adjust speed as necessary

  // Update suggestions
  suggestionTexts.forEach((el) => {
      el.textContent = translations[lang][el.dataset.key];
  });

  // Update elements with the 'data-lang' attribute
  document.querySelectorAll("[data-lang]").forEach((element) => {
      const key = element.getAttribute("data-lang");

      // If it's an input field, update the placeholder
      if (element.tagName === "INPUT") {
          element.placeholder = translations[lang][key];
      } else {
          element.textContent = translations[lang][key];
      }
  });
};

// Change event listener for language selection
languageSelector.addEventListener("change", (event) => {
  const selectedLang = event.target.value;
  updateText(selectedLang);
});

// Set default language to English on page load
updateText("en-US");

  let userMessage = null;
  let isResponseGenerating = false;

  // Backend API configuration (Updated to `/ask` as per Flask setup)
  const BACKEND_API_URL = "/ask";





//changed ekkatuthangal to ekkattuthangal
// Define Metro Lines
const greenLine = [
  "St. Thomas Mount", "Arignar Anna Alandur (Alandur)", "Ekkatuthangal", "Ashok Nagar",
  "Vadapalani", "Arumbakkam", "Puratchi Thalaivi Dr. J. Jayalalithaa CMBT (CMBT)",
  "Koyambedu", "Thirumangalam", "Anna Nagar Tower", "Anna Nagar East", "Shenoy Nagar",
  "Pachaiyappa's College", "Kilpauk", "Nehru Park", "Egmore",
  "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)"
];

const blueLine = [
  "Chennai International Airport", "Meenambakkam", "OTA - Nanganallur Road",
  "Arignar Anna Alandur (Alandur)", "Guindy", "Little Mount", "Saidapet", "Nandanam",
  "Teynampet", "AG-DMS", "Thousand Lights", "LIC", "Government Estate",
  "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)", "High Court",
  "Mannadi", "Washermanpet", "New Washermenpet Metro", "Tondiarpet Metro", "Tollgate Metro",
  "Thiruvotriyur Theradi Metro", "Thiruvotriyur Metro", "Kaladipet Metro", "Thiagaraya College Metro",
  "Wimco Nagar Metro", "Wimco Nagar Depot"
];

// Tamil to English Station Name Mapping
const stationTranslations = {
  "ஏ.ஜி. – டி.எம்.எஸ்.": "AG – DMS",
  "அண்ணா நகர் கிழக்கு மெட்ரோ நிலையம்": "Anna Nagar East",
  "அண்ணா நகர் கோபுரம்": "Anna Nagar Tower",
  "அறிஞர் அண்ணா ஆலந்தூர்": "Arignar Anna Alandur",
  "அரும்பாக்கம்": "Arumbakkam",
  "அசோக் நகர்": "Ashok Nagar",
  "சென்னை பன்னாட்டு விமான நிலையம்": "Chennai International Airport",
  "எழும்பூர்": "Egmore",
  "ஈக்காட்டுத்தாங்கல்": "Ekkatuthangal",
  "அரசினர் தோட்டம்": "Government Estate",
  "கிண்டி": "Guindy",
  "உயர் நீதிமன்றம்": "High Court",
  "கீழ்ப்பாக்கம்": "Kilpauk",
  "கோயம்பேடு": "Koyambedu",
  "எல். ஐ. சி.": "LIC",
  "சின்னமலை": "Little Mount",
  "மண்ணடி": "Mannadi",
  "மீனம்பாக்கம்": "Meenambakkam",
  "நந்தனம்": "Nandanam",
  "நங்கநல்லூர் சாலை": "Nanganallur Road",
  "நேரு பூங்கா": "Nehru Park",
  "பச்சையப்பன் கல்லூரி": "Pachaiyappa's College",
  "புரட்சித் தலைவர் டாக்டர். எம்.ஜி. இராமச்சந்திரன் சென்ட்ரல்": "Puratchi Thalaivar Dr. M.G. Ramachandran Central",
  "புரட்சித் தலைவி டாக்டர். ஜெ. ஜெயலலிதா புறநகர் பேருந்து நிலையம்": "Puratchi Thalaivi Dr. J. Jayalalithaa CMBT",
  "சைதாப்பேட்டை": "Saidapet",
  "செனாய் நகர்": "Shenoy Nagar",
  "பரங்கிமலை": "St. Thomas Mount",
  "தேனாம்பேட்டை": "Teynampet",
  "திருமங்கலம்": "Thirumangalam",
  "ஆயிரம் விளக்கு": "Thousand Lights",
  "வடபழனி": "Vadapalani",
  "வண்ணாரப்பேட்டை": "Washermanpet"
};








const stationAliases = {
  "Airport": "Chennai International Airport",
  "airport": "Chennai International Airport",
  "Chennai Airport": "Chennai International Airport",
  "OTA": "OTA - Nanganallur Road",
  "Nanganallur": "OTA - Nanganallur Road",
  "Alandur": "Arignar Anna Alandur (Alandur)",
 "Central": "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)",  // ✅ Fix for your issue
 "MGR Central": "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)",  // ✅ Fix for your issue
 "MGR central": "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)",  // ✅ Fix for your issue
  "central": "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)",  // ✅ Fix for your issue
  "Central Metro": "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)", // Added new alias
  "Chennai Central": "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)",  // ✅ Already added
  "Chennai central": "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)",  // ✅ Fix for your issue
  "CMBT": "Puratchi Thalaivi Dr. J. Jayalalithaa CMBT (CMBT)",
  "New Washermenpet": "New Washermenpet Metro",
  "Washermanpet": "Washermanpet Metro",
  "Tondiarpet": "Tondiarpet Metro",
  "Tollgate": "Tollgate Metro",
  "Thiruvotriyur Theradi": "Thiruvotriyur Theradi Metro",
  "Thiruvotriyur": "Thiruvotriyur Metro",
  "Kaladipet": "Kaladipet Metro",
  "Thiagaraya College": "Thiagaraya College Metro",
  "Wimco Nagar": "Wimco Nagar Metro",
  "Ekkatuthangal": "Ekkatuthangal Metro",
  "Ekkattuthangal": "Ekkatuthangal",
  "Ekkatuthangal": "Ekkatuthangal",
  "Arignar Anna Alandur": "Arignar Anna Alandur (Alandur)",
    "Arignar Anna Alandur (Alandur)": "Arignar Anna Alandur (Alandur)",
    "alandur": "Arignar Anna Alandur (Alandur)",
    "Alandur": "Arignar Anna Alandur (Alandur)",
    "Puratchi Thalaivar Dr. M.G. Ramachandran Central": "Chennai Central",
    "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)": "Chennai Central",
    "Chennai Park Town": "Park Town",
    "Chennai Egmore Metro": "Egmore"
};


const extractStations = async (message) => {
  console.log("📩 Sending message:", message);

  try {
      const response = await fetch('/extract_stations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
      });

      const data = await response.json();
      console.log("🛬 Response received:", data);

      if (data.error) return null;

      let src = data.src?.trim();
      let dest = data.dest?.trim();

      console.log("✅ Extracted stations (Tamil):", src, dest);

      // ✅ Convert Tamil names to English using stationAliases
      src = stationAliases[src] || src;
      dest = stationAliases[dest] || dest;

      console.log("🔄 Normalized with aliases:", src, dest);

      const allStations = [...greenLine, ...blueLine];
      console.log(allStations);

      // ✅ Improve station matching with case-insensitive search
      src = allStations.find(st => src.toLowerCase().includes(st.toLowerCase())) || null;
      dest = allStations.find(st => dest.toLowerCase().includes(st.toLowerCase())) || null;

      if (!src || !dest) {
          console.error("🚨 Station names not found in list:", src, dest);
          return null;
      }

      return { src, dest };
  } catch (error) {
      console.error("❌ Error extracting stations:", error);
      return null;
  }
};








  // Load theme and chat data from local storage on page load
  const loadDataFromLocalstorage = () => {
    const savedChats = localStorage.getItem("saved-chats");
    const isLightMode = (localStorage.getItem("themeColor") === "light_mode");

    document.body.classList.toggle("light_mode", isLightMode);
    toggleThemeButton.innerText = isLightMode ? "dark_mode" : "light_mode";

    chatContainer.innerHTML = savedChats || '';
    document.body.classList.toggle("hide-header", savedChats);

    chatContainer.scrollTo(0, chatContainer.scrollHeight);
  };

  // Create a new message element and return it
  const createMessageElement = (content, ...classes) => {
    const div = document.createElement("div");
    div.classList.add("message", ...classes);
    div.innerHTML = content;
    return div;
  };

  window.addEventListener('load', function () {
    // Set the image sources dynamically based on the Flask values
    const userLogo = document.getElementById('user-avatar');
    const geminiLogo = document.getElementById('gemini-avatar');

    if (userLogo && geminiLogo) {
      userLogo.src = window.userLogoSrc;  // Set the user logo
      geminiLogo.src = window.geminiLogoSrc;  // Set the Gemini logo
    }

    document.body.classList.add('loaded');
  });


  // Show typing effect by displaying words one by one
  const showTypingEffect = (text, textElement, incomingMessageDiv) => {
    const words = text.split(' ');
    let currentWordIndex = 0;

    const typingInterval = setInterval(() => {
      textElement.innerText += (currentWordIndex === 0 ? '' : ' ') + words[currentWordIndex++];
      incomingMessageDiv.querySelector(".icon").classList.add("hide");

      if (currentWordIndex === words.length) {
        clearInterval(typingInterval);
        isResponseGenerating = false;
        incomingMessageDiv.querySelector(".icon").classList.remove("hide");
        localStorage.setItem("saved-chats", chatContainer.innerHTML);
      }

      chatContainer.scrollTo(0, chatContainer.scrollHeight);
    }, 10);
  };

  const generateAPIResponse = async (incomingMessageDiv) => {
    const textElement = incomingMessageDiv.querySelector(".text");
    const selectedLang = languageSelector.value; // Get selected language

    try {
        console.log("📩 Checking booking intent first...");

        // ✅ Check for booking intent before calling main API
        const isBookingIntent = await checkBookingIntent(userMessage);
        console.log("🎟️ Booking intent detected?", isBookingIntent);

        if (isBookingIntent) {
            // ✅ Check for booking intent success

            const bookingButton = document.createElement("button");
            bookingButton.innerText = "Click here to Navigate to Ticket Booking Bot";
            bookingButton.classList.add("book-ticket-button");
            bookingButton.onclick = () => {
                window.location.href = "http://127.0.0.1:8001/"; // Redirect to ticket booking bot
            };
            incomingMessageDiv.appendChild(bookingButton);
            console.log("📌 Appended 'Book Ticket' button to chat.");
            speakText(bookingButton.innerText);

            return;  // 🚀 Stop further processing if it's a booking request
        }


            // Extract stations **after Mithra responds**
            let routeData = await extractStations(userMessage);
            console.log("🔍 Extracted routeData:", routeData);
    
            // ✅ Use separate variables for Google Maps (DO NOT modify routeData)
            let mapSrc = convertToMetroStation(routeData?.src);
            let mapDest = convertToMetroStation(routeData?.dest);
    
            // ✅ Pass only **original station names** to `visualizeRoute`
            if (routeData && routeData.src && routeData.dest) {
    
              console.log("🚀 Calling `sendRouteDataToFlask` with:", routeData.src, routeData.dest);
                
              // ✅ CALL sendRouteDataToFlask() HERE
              sendRouteDataToFlask(routeData.src.trim(), routeData.dest.trim());
    
              
                setTimeout(() => {
                    console.log("🚀 Calling visualizeRoute with:", routeData.src, routeData.dest);
                    visualizeRoute(routeData.src.trim(), routeData.dest.trim(), routeData.intermediate);
                }, 500);
            } else {
                console.error("🚨 Route extraction failed. Invalid data:", routeData);
            }
                  // ✅ Create "Open Metro Map" button only if metro stations are found
                  if (mapSrc || mapDest) {
                    const metroMapButton = document.createElement("button");
                    metroMapButton.innerText = mapDest ? "Google Map Route" : "Show Metro Station on Map";
                    metroMapButton.classList.add("metro-map-button");
        
                    // ✅ Event listener to open Google Maps for metro stations
                    metroMapButton.onclick = () => openMetroMap(mapSrc, mapDest);
        
                    // ✅ Append button to chat response
                    incomingMessageDiv.appendChild(metroMapButton);
                }





        //Check if the main api failed or something
        console.log("📩 Sending message to backend...");
        const response = await fetch(BACKEND_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: userMessage,
                language: selectedLang
            }),
        });
        if (!response.ok) {
            throw new Error(`Error generating response: ${response.status}`);
        }

        console.log("📩 Response status:", response.status);

        const data = await response.json();

        console.log("JSON Data",data.response);

        if (!response.ok) throw new Error(data.error || "Error generating response");

        // Display the response in chat
        showTypingEffect(data.response, textElement, incomingMessageDiv);


    
            // Play the generated speech audio if available
            if (data.audio_url) {
                const audio = new Audio(data.audio_url);
                audio.play();
            }
    } catch (error) {
        console.error("Error generating response:", error);
        textElement.innerText = error.message || "An unknown error occurred.";
        textElement.parentElement.closest(".message").classList.add("error");
    } finally {
        incomingMessageDiv.classList.remove("loading");
    }
};

//Fix on the check booking intent
async function checkBookingIntent(userMessage) {
  console.log("📩 Checking booking intent...");
  console.log("📝 User Message:", userMessage);

  try {
      const response = await fetch("http://127.0.0.1:5000/check_booking_intent", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) {
          throw new Error(`Booking intent check failed: ${response.status}`);
      }

      const data = await response.json();
      console.log("🔍 Full Booking Intent Response:", data);
      console.log("🎟️ Booking intent detected?", data.isBookingIntent);

      //Check that the boolean is working correctly
      if (typeof data.isBookingIntent === 'boolean') {

          const incomingMessageDiv = document.createElement("div");
          incomingMessageDiv.classList.add("message", "bot", "loading");

          const textElement = document.createElement("div");
          textElement.classList.add("text");

          const iconSpan = document.createElement("span");
          iconSpan.className = "material-symbols-outlined icon";
          iconSpan.innerText = "smart_toy";

          incomingMessageDiv.appendChild(iconSpan);
          incomingMessageDiv.appendChild(textElement);

          //**APPEND `chatContainer` and test to see what outputs to the DOM
          console.log(`Log variable = ${document.getElementById("chatbox")}`);

         // generateAPIResponse(incomingMessageDiv); // Add this line!//Verify this exists...recursiveness leads to infinite calls
          chatContainer.scrollTo(0, chatContainer.scrollHeight);


          // ✅ Call `showTypingEffect` to display the message
          showTypingEffect(data.response, textElement, incomingMessageDiv);

          return data.isBookingIntent;
      } else {
          console.error("❌ Invalid Booking Intent Response: Not a boolean value");
          return false;
      }
  } catch (error) {
      console.error("🚨 Booking intent check failed:", error);
      return false;
  }
}



// 🔊 Function to Speak Text
const speakText = (text) => {
  if ("speechSynthesis" in window) {
      const speech = new SpeechSynthesisUtterance(text);
      speech.lang = "en-US"; // Set language
      speech.rate = 1; // Adjust speed (1 = normal)
      speech.pitch = 1; // Adjust pitch
      speech.volume = 1; // Adjust volume

      speechSynthesis.speak(speech);
  } else {
      console.warn("❌ Speech synthesis is not supported in this browser.");
  }
};




// ✅ Metro station name mapping (kept separate from visualization logic)
const metroStationMapping = {
    "St. Thomas Mount": "St. Thomas Mount Metro",
    "Arignar Anna Alandur (Alandur)": "Arignar Anna Alandur Metro",
    "Ekkatuthangal": "Ekkatuthangal Metro", //changed spelling
    "Ashok Nagar": "Ashok Nagar Metro",
    "Vadapalani": "Vadapalani Metro",
    "Arumbakkam": "Arumbakkam Metro",
    "Puratchi Thalaivi Dr. J. Jayalalithaa CMBT (CMBT)": "CMBT Metro",
    "Koyambedu": "Koyambedu Metro",
    "Thirumangalam": "Thirumangalam Metro",
    "Anna Nagar Tower": "Anna Nagar Tower Metro",
    "Anna Nagar East": "Anna Nagar East Metro",
    "Shenoy Nagar": "Shenoy Nagar Metro",
    "Pachaiyappa's College": "Pachaiyappa's College Metro",
    "Kilpauk": "Kilpauk Metro",
    "Nehru Park": "Nehru Park Metro",
    "Egmore": "Egmore Metro",
    "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)": "Chennai Central Metro",
    
    "Chennai International Airport": "Chennai International Airport Metro",
    "Meenambakkam": "Meenambakkam Metro",
    "OTA - Nanganallur Road": "OTA - Nanganallur Road Metro",
    "Guindy": "Guindy Metro",
    "Little Mount": "Little Mount Metro",
    "Saidapet": "Saidapet Metro",
    "Nandanam": "Nandanam Metro",
    "Teynampet": "Teynampet Metro",
    "AG-DMS": "AG-DMS Metro",
    "Thousand Lights": "Thousand Lights Metro",
    "LIC": "LIC Metro",
    "Government Estate": "Government Estate Metro",
    "High Court": "High Court Metro",
    "Mannadi": "Mannadi Metro",
    "Washermanpet": "Washermanpet Metro",
    "New Washermenpet Metro": "New Washermenpet Metro",
    "Tondiarpet Metro": "Tondiarpet Metro",
    "Tollgate Metro": "Tollgate Metro",
    "Thiruvotriyur Theradi Metro": "Thiruvotriyur Theradi Metro",
    "Thiruvotriyur Metro": "Thiruvotriyur Metro",
    "Kaladipet Metro": "Kaladipet Metro",
    "Thiagaraya College Metro": "Thiagaraya College Metro",
    "Wimco Nagar Metro": "Wimco Nagar Metro",
    "Wimco Nagar Depot": "Wimco Nagar Depot Metro"
};

function convertToMetroStation(station) {
    if (!station) return null;
    return metroStationMapping[station] || null;
}

// ✅ Function to open Google Maps with metro stations
function openMetroMap(mapSrc, mapDest) {
    let mapUrl = "https://www.google.com/maps";

    if (mapSrc && mapDest) {
        mapUrl += `/dir/${encodeURIComponent(mapSrc)}/${encodeURIComponent(mapDest)}/data=!4m2!4m1!3e3`;  // `3e3` ensures transit (Metro) mode
    } else if (mapSrc) {
        mapUrl += `/search/${encodeURIComponent(mapSrc)}`;
    }

    window.open(mapUrl, "_blank", "width=800,height=600");
}

  // Show loading animation
  const showLoadingAnimation = () => {
    const html = `
      <div class="message-content">
        <div class="avatar mithra-avatar">
          <span class="mithra-text">Mithra: </span>
        </div>
        <p class="text"></p>
        <div class="loading-indicator">
          <div class="loading-bar"></div>
          <div class="loading-bar"></div>
          <div class="loading-bar"></div>
        </div>
      </div>
      <span onClick="copyMessage(this)" class="icon material-symbols-rounded">content_copy</span>
    `;
  
    const incomingMessageDiv = createMessageElement(html, "incoming", "loading");
    chatContainer.appendChild(incomingMessageDiv);
  
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
    generateAPIResponse(incomingMessageDiv);
  };
  

  // Copy message text to clipboard
  const copyMessage = (copyButton) => {
    const messageText = copyButton.parentElement.querySelector(".text").innerText;
    navigator.clipboard.writeText(messageText);
    copyButton.innerText = "done";
    setTimeout(() => copyButton.innerText = "content_copy", 1000);
  };

  // Handle outgoing chat message
  const handleOutgoingChat = () => {
    userMessage = typingForm.querySelector(".typing-input").value.trim() || userMessage;
    if (!userMessage || isResponseGenerating) return;

    isResponseGenerating = true;

    const html = `<div class="message-content">
  <div class="avatar user-avatar">
    <span class="user-text">User: </span>
  </div>
  <p class="text"></p>
</div>`;

    const outgoingMessageDiv = createMessageElement(html, "outgoing");
    outgoingMessageDiv.querySelector(".text").innerText = userMessage;
    chatContainer.appendChild(outgoingMessageDiv);

    typingForm.reset();
    document.body.classList.add("hide-header");
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
    setTimeout(showLoadingAnimation, 500);
  };



// 🎯 Helper function to get a direct path between two stations on a line
function getDirectPath(line, start, end) {
  let startIndex = line.indexOf(start);
  let endIndex = line.indexOf(end);

  if (startIndex === -1 || endIndex === -1) {
      console.warn(`One or both stations not found on the line: ${start}, ${end}`);
      return null;
  }

  return startIndex < endIndex
      ? line.slice(startIndex, endIndex + 1)
      : line.slice(endIndex, startIndex + 1).reverse();
}

// 🎯 Main function to fetch metro route details
function fetch_metro_route_details_from_js(src_station, dest_station) {
  if (!src_station || !dest_station) return { error: "Invalid source or destination." };

  let line_color = "Unknown";

  // 🔹 If both stations are on the Green Line
  if (greenLine.includes(src_station) && greenLine.includes(dest_station)) {
      line_color = "Green Line";
      return {
          source: src_station,
          destination: dest_station,
          path: getDirectPath(greenLine, src_station, dest_station),
          interchange: "None",
          line_color: line_color
      };
  }

  // 🔹 If both stations are on the Blue Line
  if (blueLine.includes(src_station) && blueLine.includes(dest_station)) {
      line_color = "Blue Line";
      return {
          source: src_station,
          destination: dest_station,
          path: getDirectPath(blueLine, src_station, dest_station),
          interchange: "None",
          line_color: line_color
      };
  }

  let routeViaAlandur = null, routeViaCentral = null;
  let finalRoute = null, finalInterchange = "None";

  // 🔹 If switching from Green Line to Blue Line
  if (greenLine.includes(src_station) && blueLine.includes(dest_station)) {
      line_color = "Green to Blue";

      let firstInterchange = "Arignar Anna Alandur (Alandur)";
      routeViaAlandur = getDirectPath(greenLine, src_station, firstInterchange)
          .concat(getDirectPath(blueLine, firstInterchange, dest_station).slice(1));

      let secondInterchange = "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)";
      routeViaCentral = getDirectPath(greenLine, src_station, secondInterchange)
          .concat(getDirectPath(blueLine, secondInterchange, dest_station).slice(1));

      if (routeViaCentral.length > 0) {
          finalRoute = routeViaCentral;
          finalInterchange = secondInterchange;
      } else {
          finalRoute = routeViaAlandur;
          finalInterchange = firstInterchange;
      }
  }

  // 🔹 If switching from Blue Line to Green Line
  if (blueLine.includes(src_station) && greenLine.includes(dest_station)) {
      line_color = "Blue to Green";

      let firstInterchange = "Arignar Anna Alandur (Alandur)";
      routeViaAlandur = getDirectPath(blueLine, src_station, firstInterchange)
          .concat(getDirectPath(greenLine, firstInterchange, dest_station).slice(1));

      let secondInterchange = "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)";
      routeViaCentral = getDirectPath(blueLine, src_station, secondInterchange)
          .concat(getDirectPath(greenLine, secondInterchange, dest_station).slice(1));

      if (routeViaCentral.length > 0) {
          finalRoute = routeViaCentral;
          finalInterchange = secondInterchange;
      } else {
          finalRoute = routeViaAlandur;
          finalInterchange = firstInterchange;
      }
  }

  if (!finalRoute) {
      console.warn("No route found between", src_station, "and", dest_station);
      return {
          source: src_station,
          destination: dest_station,
          path: [],
          interchange: "None",
          line_color: "Unknown"
      };
  }
  console.log("This is for the testttttttttttt",finalRoute);
  return {
      source: src_station,
      destination: dest_station,
      path: finalRoute,
      interchange: finalInterchange,
      line_color: line_color
  };
}

// 🚀 Function to send route data to Flask
function sendRouteDataToFlask(src_station, dest_station) {
  const routeData = fetch_metro_route_details_from_js(src_station, dest_station);

  // 🔹 Prepare data payload
  const requestData = {
      source: src_station,
      destination: dest_station,
      path: routeData.path,
      interchange: routeData.interchange,
      line_color: routeData.line_color // ✅ Include line color
  };

  console.log("Debugging: requestData object (before sending):", requestData);

  // 🔹 Send POST request to Flask
  fetch("http://127.0.0.1:5000/receive_route_data", {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify(requestData)
  })
  .then(response => response.json())
  .then(data => {
      console.log("✅ Response from Flask:", data);
  })
  .catch(error => {
      console.error("❌ Error sending data to Flask:", error);
  });
}



// 🔹 Function to normalize station names and handle aliases
const normalizeStationName = (name) => {
  if (!name) return null;
  let cleanName = name.trim().toLowerCase(); // Remove spaces & lowercase
  return stationAliases[cleanName] || name; // Convert alias to standard name, else return original
};

const visualizeRoute = (src, dest) => {
  console.log("🗺️ visualizeRoute triggered with:", src, dest);

  // Convert user inputs using alias mapping
  src = normalizeStationName(src);
  dest = normalizeStationName(dest);

  console.log("🔄 Normalized Station Names:", src, dest);

  let newMapContainer = document.createElement("div");
  newMapContainer.style.cssText = `
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
      padding: 10px;
      border-top: 2px solid var(--border-color);
      margin-top: 10px;
      max-height: 400px;
      overflow-y: auto;
      background: var(--background-color);
      color: var(--text-color);
  `;

  chatContainer.appendChild(newMapContainer);

  if (!src || !dest) {
      console.error("🚨 Invalid Route (Source and Destination you mentioned):", src, dest);
      newMapContainer.innerHTML = `<p style="color:red; font-weight:bold;">Invalid route.</p>`;
      return;
  }

  let greenLine = [
    "St. Thomas Mount", "Arignar Anna Alandur (Alandur)", "Ekkatuthangal", "Ashok Nagar",
    "Vadapalani", "Arumbakkam", "Puratchi Thalaivi Dr. J. Jayalalithaa CMBT (CMBT)", "Koyambedu",
    "Thirumangalam", "Anna Nagar Tower", "Anna Nagar East", "Shenoy Nagar", "Pachaiyappa's College",
    "Kilpauk", "Nehru Park", "Egmore", "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)"
];

let blueLine = [
    "Chennai International Airport", "Meenambakkam", "OTA - Nanganallur Road",
    "Arignar Anna Alandur (Alandur)", "Guindy", "Little Mount", "Saidapet", "Nandanam",
    "Teynampet", "AG-DMS", "Thousand Lights", "LIC", "Government Estate",
    "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)",
    "High Court", "Mannadi", "Washermanpet", "New Washermenpet Metro", "Tondiarpet Metro",
    "Tollgate Metro", "Thiruvotriyur Theradi Metro", "Thiruvotriyur Metro", "Kaladipet Metro",
    "Thiagaraya College Metro", "Wimco Nagar Metro", "Wimco Nagar Depot"
];
  let interchangeStations = ["Arignar Anna Alandur (Alandur)", "Puratchi Thalaivar Dr. M.G. Ramachandran Central (Chennai Central)"];

  const getDirectPath = (line, start, end) => {
      let startIndex = line.indexOf(start);
      let endIndex = line.indexOf(end);
      if (startIndex === -1 || endIndex === -1) return null;
      return startIndex < endIndex ? line.slice(startIndex, endIndex + 1) : line.slice(endIndex, startIndex + 1).reverse();
  };

  let directGreenPath = getDirectPath(greenLine, src, dest);
  let directBluePath = getDirectPath(blueLine, src, dest);

  if (directGreenPath) {
      plotRoute(newMapContainer, directGreenPath, greenLine, blueLine);
      return;
  }

  if (directBluePath) {
      plotRoute(newMapContainer, directBluePath, greenLine, blueLine);
      return;
  }

  let routeViaAlandur = null, routeViaCentral = null;
  let firstInterchange = interchangeStations[0];
  let secondInterchange = interchangeStations[1];

  if (greenLine.includes(src) && blueLine.includes(dest)) {
      console.log("✅ Interchange scenario: Green ➝ Blue");
      routeViaAlandur = getDirectPath(greenLine, src, firstInterchange)
          .concat(getDirectPath(blueLine, firstInterchange, dest).slice(1));
      routeViaCentral = getDirectPath(greenLine, src, secondInterchange)
          .concat(getDirectPath(blueLine, secondInterchange, dest).slice(1));
  }

  if (blueLine.includes(src) && greenLine.includes(dest)) {
      console.log("✅ Interchange scenario: Blue ➝ Green");
      routeViaAlandur = getDirectPath(blueLine, src, firstInterchange)
          .concat(getDirectPath(greenLine, firstInterchange, dest).slice(1));
      routeViaCentral = getDirectPath(blueLine, src, secondInterchange)
          .concat(getDirectPath(greenLine, secondInterchange, dest).slice(1));
  }

  if (!routeViaAlandur && !routeViaCentral) {
      newMapContainer.innerHTML = `<p style="color:red; font-weight:bold;">No valid route found.</p>`;
      return;
  }

  // Determine shortest and alternate route
  let shortestRoute = routeViaAlandur.length <= routeViaCentral.length ? routeViaAlandur : routeViaCentral;
  let alternateRoute = shortestRoute === routeViaAlandur ? routeViaCentral : routeViaAlandur;
  let finalInterchange = shortestRoute === routeViaAlandur ? firstInterchange : secondInterchange;

  // ✅ Plot correct shortest route
  plotRoute(newMapContainer, shortestRoute, greenLine, blueLine);

  // ✅ Send shortest route to Flask
  let requestData = {
      source: src,
      destination: dest,
      path: shortestRoute,
      interchange: finalInterchange
  };

  fetch('/receive_route_data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
  })
  .then(response => response.json())
  .then(data => {
      console.log("✅ Response from Flask:", data.message);
  })
  .catch(error => {
      console.error("❌ Error sending route data to Flask:", error);
  });

  // Optional: Alternate Route button
  if (alternateRoute && alternateRoute.length > 0) {
      let button = document.createElement("button");
      button.innerText = "Show Alternate Route";
      button.style.cssText = `
          margin-top: 20px;
          padding: 7px 15px;
          background-color: var(--button-bg);
          color: var(--button-text);
          border: 2px solid var(--border-color);
          cursor: pointer;
          font-weight: bold;
          transition: background 0.3s ease;
      `;

      let altRouteContainer = document.createElement("div");
      altRouteContainer.style.cssText = "margin-top: 15px; display: none; flex-direction: column; align-items: center;";

      button.onclick = () => {
          if (altRouteContainer.style.display === "none") {
              altRouteContainer.style.display = "flex";
              button.innerText = "Hide Alternate Route";
              plotRoute(altRouteContainer, alternateRoute, greenLine, blueLine);
          } else {
              altRouteContainer.style.display = "none";
              button.innerText = "Show Alternate Route";
              altRouteContainer.innerHTML = ""; // Clear content when hiding
          }
      };

      newMapContainer.appendChild(button);
      newMapContainer.appendChild(altRouteContainer);
  }
};
const plotRoute = (container, path, greenLine, blueLine) => {
  let previousLine = null; // Track the previous station's line

  path.forEach((station, index) => {
      let stationContainer = document.createElement("div");
      stationContainer.style.cssText = `
          display: flex;
          flex-direction: column;
          align-items: center;
          margin: 5px;
      `;

      let stationDot = document.createElement("div");
      let isGreen = greenLine.includes(station);
      let isBlue = blueLine.includes(station);

      // Determine the dot color based on the previous station's line
      let dotColor;
      if (isGreen && isBlue) {
          // If it's an interchange, decide based on previous and next stations
          let previousStation = path[index - 1];
          let nextStation = path[index + 1];

          let previousIsGreen = previousStation && greenLine.includes(previousStation);
          let previousIsBlue = previousStation && blueLine.includes(previousStation);

          let nextIsGreen = nextStation && greenLine.includes(nextStation);
          let nextIsBlue = nextStation && blueLine.includes(nextStation);

          // If coming from green and continuing green, stay green; else switch
          if (previousIsGreen && nextIsGreen) {
              dotColor = "var(--green-dot)";
              previousLine = "green";
          } else if (previousIsBlue && nextIsBlue) {
              dotColor = "var(--blue-dot)";
              previousLine = "blue";
          } else {
              // Actual interchange: Change the color
              dotColor = previousLine === "green" ? "var(--blue-dot)" : "var(--green-dot)";
              previousLine = previousLine === "green" ? "blue" : "green";
          }
      } else {
          // Normal stations
          dotColor = isGreen ? "var(--green-dot)" : "var(--blue-dot)";
          previousLine = isGreen ? "green" : "blue";
      }

      stationDot.style.cssText = `
          width: 12px; 
          height: 12px; 
          background: ${dotColor}; 
          border-radius: 50%; 
          margin-bottom: 3px;
          border: 2px solid var(--border-color);
      `;

      let stationLabel = document.createElement("div");
      stationLabel.innerText = station;
      stationLabel.style.cssText = `
          font-size: 14px; 
          color: var(--text-color); 
          font-weight: bold; 
          text-align: center;
      `;

      stationContainer.appendChild(stationDot);
      stationContainer.appendChild(stationLabel);
      container.appendChild(stationContainer);

      // **Add connecting line BELOW the station (except for last station)**
      if (index !== path.length - 1) {
          let lineContainer = document.createElement("div");
          lineContainer.style.cssText = `
              display: flex;
              justify-content: center;
              align-items: center;
              height: 25px;
          `;

          let nextStation = path[index + 1];
          let nextIsGreen = greenLine.includes(nextStation);
          let nextIsBlue = blueLine.includes(nextStation);

          let lineColor;
          if (previousLine === "green" && nextIsGreen) {
              lineColor = "var(--green-line)";
          } else if (previousLine === "blue" && nextIsBlue) {
              lineColor = "var(--blue-line)";
          } else {
              lineColor = previousLine === "green" ? "var(--blue-line)" : "var(--green-line)";
          }

          let line = document.createElement("div");
          line.style.cssText = `
              width: 4px; 
              height: 25px; 
              background: ${lineColor};
          `;

          lineContainer.appendChild(line);
          container.appendChild(lineContainer);
      }
  });

  chatContainer.scrollTo(0, chatContainer.scrollHeight);

};



  // Event Listeners
  toggleThemeButton.addEventListener("click", () => {
    const isLightMode = document.body.classList.toggle("light_mode");
    localStorage.setItem("themeColor", isLightMode ? "light_mode" : "dark_mode");
    toggleThemeButton.innerText = isLightMode ? "dark_mode" : "light_mode";
    updateTheme();
});

const updateTheme = () => {
  const isLightMode = document.body.classList.contains("light_mode");

  document.documentElement.style.setProperty("--background-color", isLightMode ? "#f5f5f5" : "#242424");
  document.documentElement.style.setProperty("--text-color", isLightMode ? "#000000" : "#ffffff");
  document.documentElement.style.setProperty("--border-color", isLightMode ? "#ddd" : "#444");

  // ✅ Button Colors for Day/Night Mode
  document.documentElement.style.setProperty("--primary-color", isLightMode ? "#0056b3" : "#2525fc");
  document.documentElement.style.setProperty("--secondary-color", isLightMode ? "#007bff" : "#383838");
  document.documentElement.style.setProperty("--button-text-color", "#ffffff");

  // ✅ Metro Line Colors (If needed)
  document.documentElement.style.setProperty("--green-dot", isLightMode ? "#008000" : "#66ff66");
  document.documentElement.style.setProperty("--blue-dot", isLightMode ? "#0000ff" : "#87cefa");
  document.documentElement.style.setProperty("--gray-dot", isLightMode ? "#808080" : "#000000");

  document.documentElement.style.setProperty("--green-line", isLightMode ? "#008000" : "#66ff66");
  document.documentElement.style.setProperty("--blue-line", isLightMode ? "#0000ff" : "#87cefa");
  document.documentElement.style.setProperty("--gray-line", isLightMode ? "#808080" : "#000000");
};


// **Load Theme from Local Storage**
document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("themeColor") === "light_mode") {
      document.body.classList.add("light_mode");
  }
  updateTheme();
});


  // Add event listener for all existing and future copy buttons
  chatContainer.addEventListener("click", (event) => {
    if (event.target.classList.contains("icon") && event.target.innerText === "content_copy") {
      copyMessage(event.target);
    }
  });

  deleteChatButton.addEventListener("click", () => {
    showConfirmationPopup();
  });
  
  function showConfirmationPopup() {
    const popupContainer = document.createElement("div");
    popupContainer.classList.add("confirmation-popup-container");
  
    const popup = document.createElement("div");
    popup.classList.add("confirmation-popup");
  
    const message = document.createElement("p");
    message.textContent = "Are you sure you want to delete all the chats?";
  
    const confirmButton = document.createElement("button");
    confirmButton.textContent = "Yes, Delete";
    confirmButton.classList.add("confirm-button");
    confirmButton.addEventListener("click", () => {
      localStorage.removeItem("saved-chats");
      loadDataFromLocalstorage();
      popupContainer.remove(); // Close the popup
    });
  
    const cancelButton = document.createElement("button");
    cancelButton.textContent = "Cancel";
    cancelButton.classList.add("cancel-button");
    cancelButton.addEventListener("click", () => {
      popupContainer.remove(); // Close the popup
    });
  
    popup.appendChild(message);
    popup.appendChild(confirmButton);
    popup.appendChild(cancelButton);
    popupContainer.appendChild(popup);
    document.body.appendChild(popupContainer);
  

  }
  


  suggestions.forEach(suggestion => {
    suggestion.addEventListener("click", () => {
      userMessage = suggestion.querySelector(".text").innerText;
      handleOutgoingChat();
    });
  });

  typingForm.addEventListener("submit", (e) => {
    e.preventDefault();
    handleOutgoingChat();
  });
// ✅ Initialize Speech Recognition
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = "en-US";
let isRecognizing = false; // ✅ Track if recognition is active

// 🎤 Start or Stop Voice Recognition
const startVoiceRecognition = () => {
  if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
    alert("🚨 Speech Recognition API is not supported in this browser.");
    return;
  }

  if (isRecognizing) {
    console.log("⏹️ Stopping voice recognition...");
    recognition.stop(); // ✅ Stop if already running
    return;
  }

  console.log("🎤 Starting voice recognition...");
  isRecognizing = true; // ✅ Mark as active
  recognition.start();
};

// 🎬 When Recognition Starts
recognition.onstart = () => {
  console.log("🎤 Voice recognition started...");

  // ✅ Use setTimeout to allow smooth transition
  setTimeout(() => {
    micIcon.classList.add("recording");
  }, 50);
};

// 📝 Capture Speech Result
recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  document.querySelector(".typing-input").value = transcript;
  handleOutgoingChat();
};

// ⚠️ Handle Errors Gracefully
recognition.onerror = (event) => {
  console.error("🚨 Speech recognition error:", event.error);
  isRecognizing = false;
  
  // Ensure the mic icon returns to normal state on error
  setTimeout(() => {
    micIcon.classList.remove("recording");
  }, 100);
};

// ⏹️ When Recognition Ends
recognition.onend = () => {
  console.log("⏹️ Voice recognition stopped.");
  isRecognizing = false; // ✅ Mark as inactive

  // ✅ Smooth transition when stopping
  setTimeout(() => {
    micIcon.classList.remove("recording");
  }, 100);
};

// 🎤 Attach event listener to mic button
micIcon.addEventListener("click", startVoiceRecognition);
  

  // Load data when the page loads
  loadDataFromLocalstorage();
});
