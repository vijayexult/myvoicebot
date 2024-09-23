// Configuration: Change this flag to toggle between local and server environment
const isLocal = true; // Set to false for production server

// Define the WebSocket URLs for local and server environments
const wsUrls = {
    local: 'ws://localhost:8765',  // Local WebSocket URL (for development)
    server: 'wss://your-production-server-url',  // Server WebSocket URL (for deployment)
};

// Function to get the appropriate WebSocket URL based on the environment
function getWebSocketUrl() {
    return isLocal ? wsUrls.local : wsUrls.server;
}

let socket; // Declare socket globally for access across functions
let mediaRecorder; // Declare mediaRecorder globally to stop it later if needed

function connectToWebSocket() {
    const wsUrl = getWebSocketUrl(); // Use the appropriate WebSocket URL based on the environment
    socket = new WebSocket(wsUrl);

    // Handle connection open event
    socket.addEventListener('open', function(event) {
        console.log(`Connected to WebSocket server at ${wsUrl}.`);
        document.getElementById('status').innerText = 'Connected. Waiting for response...';

        // Capture audio and send it to the server when the microphone button is clicked
        const micButton = document.getElementById('micButton');
        const disconnectButton = document.getElementById('disconnectButton');

        micButton.addEventListener('click', function() {
            // Hide the mic button and show the disconnect button immediately
            micButton.style.display = 'none';
            disconnectButton.style.display = 'flex';

            // Start audio capture and WebSocket communication
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
                        };
                    } else {
                        console.error("No audio data available.");
                    }
                };

                mediaRecorder.onstop = function() {
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
        // Check if the message is audio data
        const blob = new Blob([event.data], { type: 'audio/mp3' });
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        audio.play();
        console.log('Server response audio is playing...');
    });

    // Handle connection close event
    socket.addEventListener('close', function(event) {
        console.log('Disconnected from WebSocket server.');
        document.getElementById('status').innerText = 'Disconnected.';
        document.getElementById('disconnectButton').style.display = 'none'; // Hide disconnect button when disconnected
        document.getElementById('micButton').style.display = 'flex'; // Show mic button again
    });

    // Handle errors
    socket.addEventListener('error', function(error) {
        console.log('WebSocket error: ', error.message);
        document.getElementById('status').innerText = 'Error occurred.';
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
        document.getElementById('status').innerText = 'Disconnected manually.';
    } else {
        console.log('No active WebSocket connection to disconnect.');
    }
}

// Automatically connect to the WebSocket when the script loads
connectToWebSocket();

// Add disconnect button functionality
document.getElementById('disconnectButton').addEventListener('click', function() {
    disconnectFromWebSocket();
});
