import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from litellm import acompletion
from fastapi import Depends
from sqlalchemy.orm import Session as DBSession
from database import SessionLocal, Session, Message

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def ollama_stream_generator(prompt: str, db: DBSession, session_id: str, system_prompt: str):
    full_response = ""
    
    # --- 1. RECALL LOGIC ---
    # 1. Fetch the history
    history = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp.desc()).limit(10).all()
    history.reverse()
    
    # 2. THIS LINE CREATES THE LIST (Make sure this line is in your code!)
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in history]
    
    # 3. THIS LINE MODIFIES THE LIST (It must come after step 2)
    formatted_messages.insert(0, {"role": "system", "content": system_prompt})

    try:
        response = await acompletion(
            model="ollama/llama3.1",
            messages=formatted_messages, # <-- We pass the full history here instead of just the prompt!
            api_base="http://localhost:11434",
            stream=True,
        )
        
        async for chunk in response:
            content = chunk.choices[0].delta.content or ""
            if content:
                full_response += content 
                yield content
                
        # --- 2. ACCUMULATOR LOGIC ---
        # The stream is done, save the AI's final thought to the database
        ai_message = Message(
            session_id=session_id,
            role="assistant",
            content=full_response
        )
        db.add(ai_message)
        db.commit()
        
    except Exception as e:
        yield f"\n[Backend Error]: {str(e)}\n"

@app.get("/chat/stream")
async def chat_stream(
    prompt: str, 
    db: DBSession = Depends(get_db), 
    system_prompt: str = "You are a highly sarcastic, unhelpful AI.",
    session_id: str = "default_session"
):
    # 1. Ensure a session exists to satisfy the relational database
    if not db.query(Session).filter(Session.id == session_id).first():
        db.add(Session(id=session_id))
        db.commit()
    
    # 2. Save the user's incoming message to the database
    new_message = Message(
        session_id=session_id,
        role="user",
        content=prompt
    )
    db.add(new_message)
    db.commit()

    # 3. Stream the response back to Chainlit (your original code)
    return StreamingResponse(
        ollama_stream_generator(prompt, db, session_id, system_prompt),
        media_type="text/plain",
    )