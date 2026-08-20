// 1. Grab the UI elements from our HTML
const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const systemPrompt = document.getElementById('system-prompt');

// 2. Generate a unique session ID for this browser tab
const sessionId = crypto.randomUUID();

// 3. Helper function to create chat bubbles on the screen
function appendMessage(role, text) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', role === 'user' ? 'user-message' : 'ai-message');

    const bubbleDiv = document.createElement('div');
    bubbleDiv.classList.add('bubble');
    bubbleDiv.textContent = text;

    messageDiv.appendChild(bubbleDiv);
    chatWindow.appendChild(messageDiv);
    
    // Auto-scroll to the bottom
    chatWindow.scrollTop = chatWindow.scrollHeight; 

    // We return the bubble so we can inject streaming text into it later
    return bubbleDiv; 
}

// 4. The main function to talk to FastAPI
async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Add user's message to UI and clear the input box
    appendMessage('user', text);
    userInput.value = '';

    // Create an empty bubble for the AI's response
    const aiBubble = appendMessage('ai', '');

    // Build the URL exactly how FastAPI expects it
    const promptParam = encodeURIComponent(text);
    const sysParam = encodeURIComponent(systemPrompt.value);
    const url = `http://127.0.0.1:8050/chat/stream?prompt=${promptParam}&system_prompt=${sysParam}&session_id=${sessionId}`;

    try {
        // Knock on FastAPI's door
        const response = await fetch(url);
        if (!response.ok) throw new Error("Network response was not ok");

        // Set up the reader to catch the streaming tokens
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        // Loop to catch every single word as it arrives
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            // Decode the chunk into text and append it to the bubble
            const chunk = decoder.decode(value, { stream: true });
            aiBubble.textContent += chunk;
            
            // Keep scrolling down as text generates
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    } catch (error) {
        aiBubble.textContent = "Error connecting to the backend.";
        console.error(error);
    }
}

// 5. Trigger the send function when clicking the button or hitting Enter
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});