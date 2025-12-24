from deepgram import Deepgram
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

dg_client = Deepgram(os.getenv('DEEPGRAM_API_KEY'))