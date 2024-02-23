from fastapi import FastAPI, Request, Form,UploadFile, File, Query,HTTPException, Depends,BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pathlib import Path
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles   
from .jinjatemplates import templates
from pydantic import BaseModel
import pandas as pd
import time
import openai
from typing import Optional, List
from sklearn import metrics
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, timedelta
import asyncio
from openpyxl import load_workbook


app = FastAPI() 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DATABASE_URL = "mysql+mysqlconnector://root:root@localhost/pce"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)




openai.api_type = "azure"
openai.api_base = "https://pce-aiservices600098751.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "abe66c9c81b74e8d9a191f5a8b7932cc"



#STATIC FILES
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static") 


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


result_file_path = "GPT4_results.xlsx"
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(timestamp)


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/signin",response_class=HTMLResponse)
def updateExcel(request: Request):
    try:
        return templates.TemplateResponse("signin.html",{"request": request})
        
    except Exception as e:
        return {"ERROR":"SOMETHING WENT WRONG"}
        
@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/model", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("model.html", {"request": request})

@app.get("/dashboard")
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "is_dashboard": True})
##################################################################################################################################################################


@app.post("/signin", response_class=HTMLResponse)
async def signin(request: Request, username: str = Form(...),  password: str = Form(...)):
    time.sleep(3)
    # Check credentials
    if username == "test"  and password == "test":
        return templates.TemplateResponse("home.html", {"request": request, "username": username})
    else:
        return templates.TemplateResponse("landing.html", {"request": request, "error": "Invalid credentials. Please try again."})



@app.get("/fetch_data")
async def fetch_data(db: Session = Depends(get_db)):
    try:
        # Execute a query to fetch data from MySQL
        query = "SELECT * FROM pce.data50"
        data = pd.read_sql(query, engine)

        # Do something with the data (e.g., print it)
        print(data)

        return JSONResponse(content={"success": True, "data": data.to_dict(orient='records')}, status_code=200)

    except Exception as e:
        # Log the error for debugging
        print(f"Error: {str(e)}")
        return JSONResponse(content={"success": False, "error": "Internal Server Error"}, status_code=500)


@app.get("/filter")
def get_filtered_dataframe(include: bool = Query(True), exclude: bool = Query(True)):
    # Define the file path
    file_path = './GPT4_results.xlsx'

    # Read the Excel file into a DataFrame
    df = pd.read_excel(file_path)

    # Replace NaN or NaT values with None
    df = df.where(pd.notna(df), None)

    # Convert Timestamp objects to standard Python datetime objects
    df = df.map(lambda x: pd.to_datetime(x).to_pydatetime() if isinstance(x, pd.Timestamp) else x)

    # Convert the 'ai_decision' column to string
    df['ai_decision'] = df['ai_decision'].astype(str)

    # Condition to return unfiltered data if both Include and Exclude are selected
    if include and exclude:
        response_data = df.to_dict(orient='records')
    else:
        # Filter the DataFrame based on the decision_value
        decision_value = 'Include' if include else 'Exclude'
        filtered_data = df[df['ai_decision'] == decision_value]
        # Convert the filtered data to a dictionary
        response_data = filtered_data.to_dict(orient='records')

    # Return the JSON response
    return JSONResponse(content=response_data)














@app.post("/upload")
async def upload_excel(request: Request, file: UploadFile = File(...)):
    
    try:
        
        # Save the uploaded Excel file to a directory (in this example, 'static')
        file_path = f"static/{file.filename}"
        global uploaded_file_path
        
        # Save the file
        with open(file_path, "wb") as file_object:
            file_object.write(file.file.read())
        
        uploaded_file_path=file_path
        data = pd.read_excel(uploaded_file_path)
        
        
        
        return JSONResponse(content={"success": True, "data": {"file_path": file_path}}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)
    

##################################################################################################################################################################
class ModelInfo(BaseModel):
    model: str
class GPTRequest(BaseModel):
    uploaded_file_path:str
    model: str

@app.post("/analyse")
async def analyse_model(model_info: ModelInfo):
    # Process the received model information
    selected_model = model_info.model
    print(f"Received model information: {selected_model}")

    # You can perform additional processing or return a response as needed
    return {"message": f"Model information for {selected_model} received successfully"}
async def show_result(request:Request):
    return templates.TemplateResponse("result.html", {"request": request, "model": "GPT"})

# Additional routes based on the selected model













# Function to fetch data from the database
def fetch_data_from_db(timestamp: str, db: Session):
    query = f"SELECT * FROM pce.data50 WHERE timestamp < '{timestamp}' LIMIT 10"
    data = pd.read_sql(query, engine)
    return data

# Function to save DataFrame to Excel
def save_to_excel(result_data, file_path):
    try:
        # Check if the file exists
        file_exists = Path(file_path).exists()

        if file_exists:
            # Load the existing workbook
            wb = load_workbook(file_path)

            # Get the active sheet
            sheet = wb.active

            # Append data to the existing sheet or create a new one
            offset = 0 if file_exists else 1

            # If it's a new sheet, write the headers first
            if offset == 1:
                sheet.append(result_data.columns.tolist())

            # Append data rows
            for row in result_data.iterrows():
                sheet.append(row[1].tolist())

            # Save the workbook
            wb.save(file_path)
        else:
            # Create a new Excel file
            result_data.to_excel(file_path, index=False)

        return True
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return False

# Background task to fetch and process data
async def background_task(db: Session, result_file_path: str, inclusion_criteria: str, exclusion_criteria: str):
    while True:
        global timestamp
        print (timestamp)
        # Fetch data from the database based on time interval
        data = fetch_data_from_db(timestamp, db)
        print(data)
        # json_data = await request.json()
        # inclusion_criteria = json_data.get("criteria", {}).get("inclusion_criteria", "")
        # exclusion_criteria = json_data.get("criteria", {}).get("exclusion_criteria", "")

        if not data.empty:
            titles = []
            abstracts = []
            classifications = []

            for index, row in data.iterrows():
                Title = row['Title']
                Abstract = row['Abstract']

                message_text = {
                    "role": "system",
                    "content": f'''
                         Based on the below exclusion and inclusion criteria, please classify the given Citation as "Included" or "Excluded".
                         Apply the Exclusion Criteria first. If any statement in the Exclusion Criteria is true, mark the citation as "Excluded".
                         If the citation passes the Exclusion Criteria, then check the Inclusion Criteria. Mark the Citation as "Included" only if it strictly and exactly passes all Inclusion Criteria statements; otherwise, mark the citation as "Excluded".
                         Inclusion Criteria:
                         {inclusion_criteria}
                         Exclusion Criteria:
                         {exclusion_criteria}

                         Title: {Title}
                         Abstract: {Abstract}
                    '''
                }

                completion = openai.ChatCompletion.create(
                    engine="GPT-4",
                    messages=[message_text],
                    temperature=0.2,
                    max_tokens=800,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None
                )

                response_text = completion.choices[0].message['content']

                if "included" in response_text.lower():
                    classification = "Include"
                else:
                    classification = "Exclude"  # Placeholder for manual verification

                titles.append(Title)
                abstracts.append(Abstract)
                classifications.append(classification)

            # Create a copy of the original DataFrame
            result_data = data.copy()
            result_data = result_data.drop(columns=['timestamp'])

            # Add the 'ai_decision' column to the copied DataFrame
            result_data['ai_decision'] = classifications
            print(result_data)

            # Save the modified DataFrame
            if result_data is not None:
                if save_to_excel(result_data, result_file_path):
                # Update the last fetch timestamp to the latest timestamp in the fetched data
                    
                    print("File has been successfully updated.")
                    id_list = ', '.join(map(str, data['PCE ID'].tolist()))

                    # Update the timestamp in the database for the processed rows
                    update_query = text(f"UPDATE pce.data50 SET timestamp = :timestamp WHERE `PCE ID` IN ({id_list})")

                    # Execute the query with the new timestamp value and id list
                    db.execute(update_query, {"timestamp": timestamp})
                    db.commit()
            else:
                print("Failed to save in file")

        # Sleep for 1 minute before the next iteration
        await asyncio.sleep(60)

# Endpoint to start the background task
@app.post("/chat_gpt_4")
async def start_background_task(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    global timestamp  # Ensure you are using the global variable
    json_data = await request.json()
    inclusion_criteria = json_data.get("criteria", {}).get("inclusion_criteria", "")
    exclusion_criteria = json_data.get("criteria", {}).get("exclusion_criteria", "")
    background_tasks.add_task(background_task, db, result_file_path, inclusion_criteria,exclusion_criteria)
    return JSONResponse(content={"success": True, "message": "Background task started."})



@app.post("/claude_bedrock_edition_")
async def analyse_aws():
    return {"message": "Analyzing AWS model"}

@app.post("/nlp_model")
async def analyse_nlp():
    return {"message": "Analyzing NLP model"}

@app.post("/google_gemini")
async def analyse_google():
    return {"message": "Analyzing Google model"}










@app.get("/get_metrics")
async def get_metrics(include: bool = Query(False, description="Include decision metrics")):
    try:
        file_path = './GPT4_results.xlsx'
        df = pd.read_excel(file_path)
        
        # Extract 'Decision' and 'ai_decision' columns
        actual_values = df['Decision']
        predicted_values = df['ai_decision']
        

        # Calculate accuracy
        accuracy = metrics.accuracy_score(actual_values, predicted_values)

        # Calculate precision, recall, and F1-score
        precision, recall, f1_score, _ = metrics.precision_recall_fscore_support(actual_values, predicted_values, average='binary', pos_label='Include', zero_division=1)

        # Create a summary table
        summary_table = pd.DataFrame({
            'Metric': ['Accuracy', 'Precision', 'Recall', 'F1-Score'],
            'Value': [accuracy, precision, recall, f1_score]
        })

        # Convert the summary table to standard Python types
        summary_json = summary_table.to_dict(orient='records')

        # Additional decision metrics
        decision_metrics = {
    'total_included_human': int(df[df['Decision'] == 'Include'].shape[0]),
    'total_excluded_human': int(df[df['Decision'] == 'Exclude'].shape[0]),
    'totalHuman': int(df['Decision'].count()),
    'total_included_ai': int(df[df['ai_decision'] == 'Include'].shape[0]),
    'total_excluded_ai': int(df[df['ai_decision'] == 'Exclude'].shape[0]),
    'totalAI': int(df['ai_decision'].count()),
    'conflicting_decisions_include': int(df[(df['Decision'] == 'Include') & (df['ai_decision'] == 'Exclude')].shape[0]),
    'conflicting_decisions_exclude': int(df[(df['Decision'] == 'Exclude') & (df['ai_decision'] == 'Include')].shape[0]),
    'totalConflicts': int(df[df['Decision'] != df['ai_decision']].shape[0]),
    'accuracy_percentage': float(accuracy) * 100 # Convert to float for JSON serialization
}


        
            # Count 'Include' and 'Exclude' values in 'ai_decision' column
        ai_decision_counts = df['ai_decision'].value_counts().reset_index()
            
        ai_decision_data = ai_decision_counts.to_dict(orient='records')
        

        # Convert exclusion reason counts to a list of dictionaries
        exclusion_reason_counts = df['Reason'].value_counts().reset_index()
        exclusion_reason_counts.columns = ['Reason', 'Count']
        
        exclusion_reason_list = exclusion_reason_counts.to_dict(orient='records')

        # Return the JSON response
        response_content = {
            "success": True,
            "data": {
                "summary_metrics": summary_json,
                "exclusion_reason_counts": exclusion_reason_list,
                "decision_metrics": decision_metrics,
                "ai_decision_data": ai_decision_data
            }
        }
        return JSONResponse(content=response_content, status_code=200)

    except Exception as e:        
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)




