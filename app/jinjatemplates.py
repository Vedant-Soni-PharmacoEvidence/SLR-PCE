from pathlib import Path
import os
from fastapi.templating import Jinja2Templates
 
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = os.path.join(BASE_DIR,"templates")
templates =Jinja2Templates(directory=TEMPLATE_DIR)