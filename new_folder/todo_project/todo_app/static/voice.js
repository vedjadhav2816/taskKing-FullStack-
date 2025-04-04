document.addEventListener("DOMContentLoaded", function () {
    let voiceBtn = document.getElementById("voice-btn");
    let taskInput = document.getElementById("task-title");
    let statusText = document.getElementById("status");

    if (window.SpeechRecognition || window.webkitSpeechRecognition) {
        let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.continuous = false;

        voiceBtn.addEventListener("click", function () {
            try {
                recognition.start();
                statusText.textContent = "🎤 Listening...";
                taskInput.classList.add("recording");
                console.log("🎤 Listening for speech...");
            } catch (error) {
                console.error("⚠️ Error starting recognition:", error);
            }
        });

        recognition.onresult = function (event) {
            let spokenText = event.results[0][0].transcript;
            taskInput.value = spokenText;
            statusText.textContent = "✅ Speech recognized!";
            console.log("📝 Recognized: ", spokenText);
        };

        recognition.onspeechend = function () {
            recognition.stop();
            statusText.textContent = "🛑 Speech ended.";
            taskInput.classList.remove("recording");
            console.log("🛑 Speech ended.");
        };

        recognition.onerror = function (event) {
            console.error("⚠️ Speech recognition error:", event.error);
            statusText.textContent = "⚠️ Error: " + event.error;

            if (event.error === "no-speech") {
                alert("⚠️ No speech detected. Please try again.");
            }
        };
    } else {
        alert("⚠️ Speech Recognition is not supported in this browser.");
        console.error("⚠️ Speech Recognition is not supported in this browser.");
    }
});


