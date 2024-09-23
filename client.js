function connectToWebSocket() {
    const wsUrl = 'ws://localhost:8765';
    const socket = new WebSocket(wsUrl);

    // Handle connection open event
    socket.addEventListener('open', function(event) {
        console.log('Connected to WebSocket server.');
        document.getElementById('status').innerText = 'Connected. Waiting for response...';

        // Capture audio and send it to the server
        navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
            const mediaRecorder = new MediaRecorder(stream);
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

            // Stop recording after a certain duration
            setTimeout(() => {
                mediaRecorder.stop();
            }, 5000); // Stop recording after 5 seconds for testing

        }).catch(function(err) {
            console.error('Error accessing the microphone: ', err);
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
    });

    // Handle errors
    socket.addEventListener('error', function(error) {
        console.log('WebSocket error: ', error.message);
        document.getElementById('status').innerText = 'Error occurred.';
    });
}

document.getElementById('connectButton').addEventListener('click', function() {
    connectToWebSocket();
});
