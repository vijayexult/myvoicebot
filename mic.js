let socket; // Declare socket globally for access across functions
let mediaRecorder; // Declare mediaRecorder globally to stop it later if needed

document.getElementById('connect').addEventListener('click', connectToWebSocket);
document.getElementById('disconnect').addEventListener('click', disconnectFromWebSocket);

function connectToWebSocket() {
    const wsUrl = 'ws://localhost:8765'; // Adjust if necessary
    socket = new WebSocket(wsUrl);

    // Handle connection open event
    socket.addEventListener('open', function(event) {
        console.log(`Connected to WebSocket server at ${wsUrl}.`);
        document.getElementById('disconnect').disabled = false; // Enable disconnect button

        const micButton = document.getElementById('micButton');

        // Capture audio and send it to the server when the microphone is clicked
        micButton.addEventListener('click', function() {
            micButton.classList.add('speaking'); // Add animation class when speaking

            navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();

                mediaRecorder.ondataavailable = function(e) {
                    if (e.data.size > 0) { // Ensure there's data to send
                        const reader = new FileReader();
                        reader.readAsArrayBuffer(e.data);
                        reader.onloadend = function() {
                            const audioBuffer = reader.result;
                            socket.send(audioBuffer);
                            console.log("Audio data sent to server");
                            updateMessageWindow("Sending audio..."); // Update message window
                        };
                    } else {
                        console.error("No audio data available.");
                    }
                };

                mediaRecorder.onstop = function() {
                    micButton.classList.remove('speaking'); // Remove animation class when stopped
                    console.log('Recording stopped.');
                };

                // Stop recording after a certain duration (5 seconds for testing)
                setTimeout(() => {
                    mediaRecorder.stop();
                }, 5000); // Adjust this duration as needed

            }).catch(function(err) {
                console.error('Error accessing the microphone: ', err);
            });
        });
    });

    // Handle incoming messages from the server
    socket.addEventListener('message', function(event) {
        if (typeof event.data === 'string') {
            // Update the message window with the incoming message
            updateMessageWindow(event.data);
            // Set the assistant's response in the text area
            document.getElementById('responseText').value = event.data; // Display the assistant's response
            // Optionally update the message window again to indicate the response
            updateMessageWindow("Assistant response: " + event.data);
        } else {
            // Handle binary audio data received from the server
            const blob = new Blob([event.data], { type: 'audio/mp3' });
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);
            audio.play();
            console.log('Server response audio is playing...');
            updateMessageWindow("Receiving audio response...");
        }
    });

    // Handle connection close event
    socket.addEventListener('close', function(event) {
        console.log('Disconnected from WebSocket server.');
        document.getElementById('disconnect').disabled = true; // Disable disconnect button when disconnected
    });

    // Handle errors
    socket.addEventListener('error', function(error) {
        console.log('WebSocket error: ', error.message);
    });
}

// Disconnect function
function disconnectFromWebSocket() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop(); // Stop the recording if it's still active
    }

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
        console.log('Disconnected manually from WebSocket server.');
        document.getElementById('disconnect').disabled = true; // Disable disconnect button
    } else {
        console.log('No active WebSocket connection to disconnect.');
    }
}

// Function to update the message window
function updateMessageWindow(message) {
    const messageWindow = document.getElementById('messageWindow');
    messageWindow.innerText += message + '\n'; // Append new message
    messageWindow.scrollTop = messageWindow.scrollHeight; // Auto-scroll to bottom
}
