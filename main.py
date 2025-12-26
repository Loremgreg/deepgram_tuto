from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from deepgram import DeepgramClient
from dotenv import load_dotenv
import os
from typing import Dict, Callable


load_dotenv()

app = FastAPI()

# Configurer le client Deepgram
dg_client = DeepgramClient(api_key=os.getenv('DEEPGRAM_API_KEY'))

templates = Jinja2Templates(directory="templates")

# La fonction de connexion à Deepgram (extraite pour plus de clarté)
async def connect_to_deepgram(transcript_received_handler: Callable[[Dict], None]):
    try:
        socket = await dg_client.transcription.live({'punctuate': True, 'interim_results': False, 'language': 'fr'})
        socket.registerHandler(socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
        socket.registerHandler(socket.event.TRANSCRIPT_RECEIVED, transcript_received_handler)
        return socket
    except Exception as e:
        raise Exception(f'Could not open socket: {e}')

@app.get("/", response_class=HTMLResponse)
def get(request: Request):
    # Servir la page HTML principale
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/listen")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        deepgram_socket = await process_audio(websocket)

        while True:
            data = await websocket.receive_bytes()
            deepgram_socket.send(data)

    except Exception as e:
        raise Exception(f'Could not process audio: {e}')
    finally:
        await websocket.close()

async def process_audio(fast_socket: WebSocket):
    async def get_transcript(data: Dict) -> None:
        if 'channel' in data:
            transcript = data['channel']['alternatives'][0]['transcript']

            if transcript:
                await fast_socket.send_text(transcript)

    deepgram_socket = await connect_to_deepgram(get_transcript)

    return deepgram_socket

async def connect_to_deepgram(transcript_received_handler: Callable[[Dict], None]):
    try:
        socket = await dg_client.transcription.live({'punctuate': True, 'interim_results': False})
        socket.registerHandler(socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
        socket.registerHandler(socket.event.TRANSCRIPT_RECEIVED, transcript_received_handler)

        return socket
    except Exception as e:
        raise Exception(f'Could not open socket: {e}')

