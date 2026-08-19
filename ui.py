import chainlit as cl
from chainlit.input_widget import TextInput
import httpx
import uuid
@cl.on_chat_start
async def start():
    """
    Runs whenever a new chat session starts.
    Builds the Master Prompt settings panel in the UI.
    """
    settings = await cl.ChatSettings(
        [
            TextInput(
                id="system_prompt",
                label="Master Prompt (System Instructions)",
                initial="You are a witty, concise, and helpful AI assistant."
            )
        ]
    ).send()
    
    # Store initial settings into the user session
    cl.user_session.set("system_prompt", settings["system_prompt"])
    cl.user_session.set("session_id", str(uuid.uuid4()))

@cl.on_settings_update
async def update_settings(settings):
    """
    Updates the system prompt whenever you edit the text box in the UI.
    """
    cl.user_session.set("system_prompt", settings["system_prompt"])


@cl.on_message
async def send_to_backend(message: cl.Message):
    """
    Pulls the active system prompt, sends both the prompt and system instructions
    to FastAPI, and streams the response back.
    """
    # 1. Retrieve the current master prompt from the session
    system_prompt = cl.user_session.get(
        "system_prompt", 
        "You are a helpful AI assistant."
    )

    session_id = cl.user_session.get("session_id")

    # 2. Create an empty chat bubble in the UI
    ui_message = cl.Message(content="")
    await ui_message.send()

    # 3. Define the backend URL
    backend_url = "http://127.0.0.1:8050/chat/stream"
    
    # 4. Talk to FastAPI, passing both prompt and system_prompt query parameters
    async with httpx.AsyncClient(timeout=None) as client:
        params = {
            "prompt": message.content,
            "system_prompt": system_prompt,
            "session_id": session_id
        }
        
        async with client.stream("GET", backend_url, params=params) as response:
            # 5. Stream chunks into the chat bubble
            async for chunk in response.aiter_text():
                await ui_message.stream_token(chunk)
    
    # 6. Finalize the message visually
    await ui_message.update()