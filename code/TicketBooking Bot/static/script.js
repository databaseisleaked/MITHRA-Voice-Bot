document.addEventListener("DOMContentLoaded", () => {
  // Selecting DOM elements
  const typingForm = document.querySelector(".typing-form");
  const chatContainer = document.querySelector(".chat-list");
  const toggleThemeButton = document.querySelector("#theme-toggle-button");
  const deleteChatButton = document.querySelector("#delete-chat-button");
  const micIcon = document.querySelector(".mic-icon");

  const historyButton = document.getElementById("history-button");
  const historyPopup = document.getElementById("history-popup");
  const closeHistory = document.getElementById("close-history");
  const historyTableBody = document.querySelector("#history-table tbody");


 // Retrieve chatStarted flag from localStorage
//let chatStarted = localStorage.getItem("chatStarted") === "true";
let chatStarted = false;
  
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

  // Apply typing effect to subtitle
  const subtitleText = document.getElementById("subtitle-text");
  typeText(subtitleText, subtitleText.textContent, 120); // Adjust speed as necessary


  // State variables
  let userMessage = null;
  let isResponseGenerating = false;

  // Backend API configuration
  const BACKEND_API_URL = "/ask";

  /* function speakResponse(text, language) {
    const synth = window.speechSynthesis;
    const utterance = new SpeechSynthesisUtterance(text);

    // Map detected language to full locale codes
    const languageMap = {
        "en": "en-US",
        "ta": "ta-IN",
        "hi": "hi-IN"
    };

    let selectedLang = languageMap[language] || "en-US"; // Default to English (US)
    
    let voices = synth.getVoices();
    let selectedVoice = voices.find(voice => voice.lang === selectedLang);

    if (selectedVoice) {
        utterance.voice = selectedVoice;
    } else {
        console.warn("Preferred voice not found, using default.");
    }

    synth.speak(utterance);
  } */


  // Create a parent container for avatar and chat list
  const chatWrapper = document.createElement("div");
  chatWrapper.classList.add("chat-wrapper");

  // Wrap avatar and chat list dynamically
  const avatarWrapper = document.createElement("div");
  avatarWrapper.classList.add("avatar-section");



  //changes done for hiding the avatar initially
  avatarWrapper.style.display = "none"; // Hide initially



  // Move the avatar element into the avatarWrapper
  const userLogo = document.getElementById('user-avatar');
  const geminiLogo = document.getElementById('gemini-avatar');
  
  if (userLogo) {
    avatarWrapper.appendChild(userLogo); // Add the user avatar
  }
  
  if (geminiLogo) {
    avatarWrapper.appendChild(geminiLogo); // Add the Gemini avatar
  }

  // Insert the chatWrapper into the DOM
  chatContainer.parentNode.insertBefore(chatWrapper, chatContainer);
  chatWrapper.appendChild(avatarWrapper); // Add the avatar wrapper
  chatWrapper.appendChild(chatContainer); // Add the chat list container

  // Apply 50/50 layout with JS for the avatar and chat section
  // Add this after you set up the avatarWrapper
// Store the avatar video reference globally
let avatarVideo = null;
let isTimeLogicExecuted = false;  // Flag


const setLayout = () => {
  chatWrapper.style.display = "flex";
  chatWrapper.style.flexDirection = "column";
  chatWrapper.style.height = "100vh"; // Full height minus 1 rem for spacing above the footer

  avatarWrapper.style.flex = "0 0 30%"; // 50% for avatar
  avatarWrapper.style.display = "flex";
  avatarWrapper.style.justifyContent = "center";
  avatarWrapper.style.alignItems = "center";

  // Create the video element
  avatarVideo = document.createElement("video");
  avatarVideo.autoplay = true; // Play automatically
  avatarVideo.loop = true; // Loop the video
  avatarVideo.muted = true; // Mute to avoid autoplay restrictions
  avatarVideo.style.width = "100%"; // Make it responsive
  avatarVideo.style.height = "auto"; // Maintain aspect ratio
  avatarVideo.style.display = "block"; // Prevent extra spacing
  avatarVideo.style.margin = "0 auto"; // Center horizontally

  // Apply transition for smooth change of maxWidth
  avatarVideo.style.transition = "max-width 0.5s ease-in-out"; // Smooth transition for max-width

  // Set initial max-width based on chatStarted flag
  avatarVideo.style.maxWidth = chatStarted ? "500px" : "990px";  

  // Set the appropriate video source based on the theme
  if (document.body.classList.contains("light_mode")) {
    avatarVideo.src = "static/avatarvids/greetday.mp4"; // Day video
  } else {
    avatarVideo.src = "static/avatarvids/greet.mp4"; // Night video
  }

  // Ensure avatarWrapper centers the video
  avatarWrapper.style.display = "flex";
  avatarWrapper.style.justifyContent = "center";
  avatarWrapper.style.alignItems = "center";
  avatarWrapper.style.width = "100%";
 

  avatarWrapper.appendChild(avatarVideo); // Append video to the avatarWrapper

  chatContainer.style.flex = "1 1 70%"; // 50% for chat messages
  chatContainer.style.overflowY = "auto"; // Allow scrolling when chat grows
  chatContainer.style.padding = "10px";
  chatContainer.style.marginBottom = "9rem"; // Ensure space above the footer
};

// for creating the time based logics
const formContainer = document.querySelector(".typing-area");
const timeDisplayContainer = document.createElement("div");
timeDisplayContainer.id = "time-display-container";

timeDisplayContainer.style.textAlign = "center";
timeDisplayContainer.style.fontSize = "2em";
timeDisplayContainer.style.padding = "20px";

const timeDisplay = document.createElement("div");
timeDisplay.id = "current-time";
timeDisplayContainer.appendChild(timeDisplay);

const availabilityMessage = document.createElement("p");
availabilityMessage.textContent = "Services start at 4:30 AM";
availabilityMessage.appendChild(document.createElement("br")); // Add line break
const subText = document.createElement("p"); // Create element for subtext
subText.textContent = "Please visit again";
availabilityMessage.appendChild(subText);

timeDisplayContainer.appendChild(availabilityMessage);
availabilityMessage.style.marginTop = "10px";

const startHour = 4; // 4:30 AM in 24-hour format
const startMinute = 30;
const endHour = 23;
const endMinute = 0; // 11:00 PM

function updateTime() {
    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();

    const formattedTime = String(currentHour).padStart(2, '0') + ":" + String(currentMinute).padStart(2, '0') + ":" + String(now.getSeconds()).padStart(2, '0');
    timeDisplay.textContent = formattedTime;

    let isWithinRange = false;

    if (currentHour > startHour || (currentHour === startHour && currentMinute >= startMinute)) {
        if (currentHour < endHour || (currentHour === endHour && currentMinute <= endMinute)) {
            isWithinRange = true;
        }
    }


    if (isWithinRange) {
        formContainer.style.display = "block"; // Or ""
        timeDisplayContainer.style.display = "none";
         if (!isTimeLogicExecuted) {  // Execute only once when time is valid
            setLayout();
            isTimeLogicExecuted = true;
         }
        
    } else {
        formContainer.style.display = "none";
        timeDisplayContainer.style.display = "block";
    }
}

updateTime();
setInterval(updateTime, 1000);
formContainer.parentNode.insertBefore(timeDisplayContainer, formContainer);
//end of time logic


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
  }, 75);
};



// Fetch response from the Flask backend
const generateAPIResponse = async (incomingMessageDiv) => {
  const textElement = incomingMessageDiv.querySelector(".text");

  try {
    console.log("Sending message to backend...");
    const response = await fetch(BACKEND_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage }),
    });

    console.log("Response status:", response.status);

    const contentType = response.headers.get("Content-Type");
    if (!contentType || !contentType.includes("application/json")) {
      throw new Error("Expected JSON response but got: " + contentType);
    }

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Error generating response");

    // Display the response in chat
    showTypingEffect(data.response, textElement, incomingMessageDiv);

    // ✅ QR CODE LOGIC ✅
    if (data.qr_base64) {
      console.log("✅ QR Base64 data received:", data.qr_base64);

      const buttonContainer = document.createElement('div');
      buttonContainer.className = 'button-container';

      const downloadButton = document.createElement('button');
      downloadButton.textContent = 'Download Your Ticket';
      downloadButton.className = 'download-button'; 
      downloadButton.addEventListener('click', () => {
        let downloadLink = document.createElement('a');
        downloadLink.href = 'data:image/png;base64,' + data.qr_base64;
        downloadLink.download = `ticket_${data.ticket_id}.png`;

        document.body.appendChild(downloadLink);
        downloadLink.click();
        downloadLink.remove();
      });

      buttonContainer.appendChild(downloadButton);
      incomingMessageDiv.appendChild(buttonContainer);
    }

    // ✅ PLAY AUDIO IF AVAILABLE ✅
    if (data.audio_url) {
      const audio = new Audio(data.audio_url);

      audio.onplay = () => {
        if (avatarVideo) {
          avatarVideo.currentTime = 0;  
          avatarVideo.play();
        }
      };

      audio.onended = () => {
        if (avatarVideo) {
          avatarVideo.pause();
          avatarVideo.currentTime = 0;
        }
      };

      audio.play();
    }

    // ✅ SHRINK AVATAR AFTER EVERY MESSAGE ✅
    avatarVideo.style.transition = "max-width 0.5s ease-in-out"; // Smooth transition
    avatarVideo.style.maxWidth = "500px"; // Keep avatar small

    // ✅ Store chatStarted flag in localStorage ✅
    if (!chatStarted) {
      chatStarted = true;
      localStorage.setItem("chatStarted", "true");
    }

  } catch (error) {
    console.error("Error generating response:", error);
    isResponseGenerating = false;
    textElement.innerText = error.message || "An unknown error occurred.";
    textElement.parentElement.closest(".message").classList.add("error");
  } finally {
    incomingMessageDiv.classList.remove("loading");
  }
};


// ✅✅✅ CHECK LOCAL STORAGE ON PAGE LOAD ✅✅✅
document.addEventListener("DOMContentLoaded", () => {
  if (chatStarted) {
    avatarVideo.style.maxWidth = "500px"; // Ensure avatar stays small after refresh
  }
});  
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

    // Show avatar when user starts chatting
    avatarWrapper.style.display = "flex"; 

     // Activate chat mode to remove unnecessary scrolling
     document.body.classList.add("chat-active");

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


// Function to calculate time left and format it
function getTimeLeft(expiryTime) {
  let now = new Date();
  let timeDiff = new Date(expiryTime) - now;

  if (timeDiff <= 0) {
      return "Expired";
  }

  let hours = Math.floor(timeDiff / (1000 * 60 * 60));
  let minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
  let seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);

  return `${hours}h ${minutes}m ${seconds}s`;
}

// Function to update countdown timers dynamically
function updateCountdownTimers() {
  document.querySelectorAll(".time-left").forEach(timerElement => {
      let expiryTime = timerElement.getAttribute("data-expiry");
      let timeLeft = getTimeLeft(expiryTime);
      timerElement.textContent = timeLeft;
      if (timeLeft === "Expired") {
          timerElement.classList.add("expired"); // Add styling if expired
      }
  });
}

// Fetch and display booking history
historyButton.addEventListener("click", function () {
  console.log("Fetching ticket history...");

  fetch("/get_history")  // Fetch data from Flask
      .then(response => {
          if (!response.ok) {
              throw new Error(`HTTP Error! Status: ${response.status}`);
          }
          return response.json();
      })
      .then(data => {
          console.log("Received data:", data);
          historyTableBody.innerHTML = "";  // Clear existing data
          
          if (data.length === 0) {
              historyTableBody.innerHTML = "<tr><td colspan='12'>No tickets found.</td></tr>";
          } else {
              data.forEach(ticket => {
                  let row = document.createElement("tr");

                  if (!ticket.expiry_time) {
                      console.error("Missing expiry_time for ticket:", ticket);
                      return;
                  }

                  let expiryTime = new Date(ticket.expiry_time);
                  let now = new Date();
                  console.log(`Ticket Expiry: ${expiryTime}, Now: ${now}`);

                  let status = expiryTime < now ? "Expired" : "Valid";
                  let statusClass = expiryTime < now ? "expired" : "valid";
                  let timeLeft = getTimeLeft(expiryTime);

                  row.innerHTML = `
                      <td>${ticket.source}</td>
                      <td>${ticket.destination}</td>
                      <td>${ticket.num_tickets}</td>
                      <td>${ticket.journey_type}</td>
                      <td>${ticket.phone_number}</td>
                      <td>${ticket.cost}</td>
                      <td>${ticket.payment_method}</td>
                      <td>${ticket.booking_time}</td>
                      <td>${ticket.expiry_time}</td>
                      <td class="${statusClass}">${status}</td>
                      <td class="time-left" data-expiry="${ticket.expiry_time}">${timeLeft}</td>
                  `;

                  historyTableBody.appendChild(row);
              });

              // Update countdown every second
              setInterval(updateCountdownTimers, 1000);
          }

          historyPopup.style.display = "block";
      })
      .catch(error => console.error("Error fetching history:", error));
});

// Close History Popup
closeHistory.addEventListener("click", function () {
  historyPopup.style.display = "none";
});

// Close Popup on Outside Click
window.addEventListener("click", function (event) {
  if (event.target === historyPopup) {
      historyPopup.style.display = "none";
  }
});


// Event Listeners
toggleThemeButton.addEventListener("click", () => {
    const isLightMode = document.body.classList.toggle("light_mode");
    localStorage.setItem("themeColor", isLightMode ? "light_mode" : "dark_mode");
    toggleThemeButton.innerText = isLightMode ? "dark_mode" : "light_mode";

    // 🎨 **Update Theme Dynamically**
    updateTheme();

    // 🎥 **Pause & Reset Video Before Switching**
    if (avatarVideo) {
      avatarVideo.pause();
      avatarVideo.currentTime = 0; // Reset to start before changing source
    }

    // 🔄 **Update Video Source Based on Theme**
    avatarVideo.src = isLightMode ? "static/avatarvids/greetday.mp4" : "static/avatarvids/greet.mp4";

    // ▶️ **Ensure it plays from the beginning when loaded**
    avatarVideo.onloadeddata = () => {
      avatarVideo.currentTime = 0; // Ensure it resets
      avatarVideo.play();
    };
});

// 🎨 **Update Theme Dynamically**
const updateTheme = () => {
  const isLightMode = document.body.classList.contains("light_mode");

  document.documentElement.style.setProperty("--background-color", isLightMode ? "#f5f5f5" : "#1e1e1e");
  document.documentElement.style.setProperty("--text-color", isLightMode ? "#000000" : "#ffffff");
  document.documentElement.style.setProperty("--border-color", isLightMode ? "#ddd" : "#444");
};

  
  
  
  
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
      resetAvatarSize();  // Reset avatar size after deletion
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
    document.body.appendChild(popupContainer); // Append popup to body
  }
  
  // Function to reset the avatar size with a smooth transition
  function resetAvatarSize() {
    // Apply a smooth transition to reset avatar size
    avatarVideo.style.transition = "max-width 0.5s ease-in-out"; // Transition for resizing
  
    // Reset the avatar video maxWidth to 990px
    avatarVideo.style.maxWidth = "990px";
  }
  
  typingForm.addEventListener("submit", (e) => {
    e.preventDefault();
    handleOutgoingChat();
  });
  
  // Voice Recognition (Using Web Speech API)
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