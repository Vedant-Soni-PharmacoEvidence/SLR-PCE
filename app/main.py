from fastapi import FastAPI, Request, Form, UploadFile, File, Query, Depends,HTTPException
from fastapi.responses import HTMLResponse, JSONResponse,RedirectResponse
from app import database as db
from pathlib import Path
import os
import re
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .jinjatemplates import templates
from pydantic import BaseModel
import pandas as pd
import time
import openai
from sklearn import metrics
import numpy as np
import psycopg2
from datetime import datetime
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





def get_db():
    db_conn = psycopg2.connect(host='localhost', database='PCE', user='postgres', password='root')
    return db_conn

openai.api_type = "azure"
openai.api_base = "https://pce-aiservices600098751.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "abe66c9c81b74e8d9a191f5a8b7932cc"



#STATIC FILES
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static") 




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


project_name= "pankaj01"



@app.get("/dataupload")
def dbdataimport():
    try:
        csv_file_path = "app/data/datagpt.csv"

        # Read the CSV file into a DataFrame with explicit encoding
        df = pd.read_csv(csv_file_path, encoding='ISO-8859-1')

        df = df.dropna()
        reset_query='''ALTER SEQUENCE PANKAJ01.paperid_sequence RESTART WITH 1;'''
        db.cursor.execute(reset_query)
        db.dbconn.commit()


        for index, row in df.iterrows():
            insert_query = '''
                
                INSERT INTO 
                    PANKAJ01."aidecision" ("paper_id","Title", "Abstract", "PCE ID", "Decision", "Publication Year", "Publication Type", "Reason")
                    VALUES (nextval('PANKAJ01.paperid_sequence'),%s, %s, %s, %s, %s, %s, %s)
                
                '''
            db.cursor.execute(insert_query, (
                row['Title'], row['Abstract'], row['PCE ID'], row['Decision'], row['Publication Year'],
                row['Publication Type'], row['Reason']))
            db.dbconn.commit()
        db_conn = get_db()
        # Create a cursor
        db_cursor = db_conn.cursor()
        
        

        update_query = f'''
            UPDATE {project_name}.aidecision
            SET project_id = '{project_name}';
            
        '''
        db_cursor.execute(update_query)
        db_conn.commit()
        affected_rows = db_cursor.rowcount
        print(f"Affected Rows: {affected_rows}")
        return {"message": "Import successful and project assigned"}
    

    except Exception as e:
        print(e)
        return {"error": str(e)}

@app.get("/dataflush")
def dbdatadelete():
    
    try:

        truncate_query = f"""
            TRUNCATE TABLE {project_name}.aidecision RESTART IDENTITY;
        """
        db.cursor.execute(truncate_query)
        db.dbconn.commit()

        return {
            "message": f"Data table truncated."
        }

    except Exception as e:
        print(e)
        return {"error": str(e)}


def fetch_data_from_database():
    db_conn = get_db()
    db_cursor = db_conn.cursor()

    fetch_query = f'''
        SELECT "Title", "Abstract"
        FROM {project_name}.aidecision; -- Modify the schema if needed
    '''
    db_cursor.execute(fetch_query)
    rows = db_cursor.fetchall()

    # Close the cursor and connection
    db_cursor.close()
    db_conn.close()

    # Convert the result to a DataFrame
    columns = ["Title", "Abstract"]
    df = pd.DataFrame(rows, columns=columns)

    print(df)

    return df
# Assume you have a function to update the classification result in the database
def update_classification_in_database(title, abstract, classification):
    db_conn = get_db()
    db_cursor = db_conn.cursor()

    title = title.replace("'", "''")  # Properly escape single quotes
    abstract = abstract.replace("'", "''")  # Properly escape single quotes

    update_query = f'''
        UPDATE {project_name}.aidecision
        SET ai_decision = '{classification}'
        WHERE "Title" = '{title}' AND "Abstract" = '{abstract}'; -- Modify the schema if needed
    '''
    db_cursor.execute(update_query)

    db_conn.commit()

    db_cursor.close()
    db_conn.close()

# Your FastAPI endpoint
@app.post("/chat_gpt_4")
async def analyse_gpt(request: Request):
    try:
        json_data = await request.json()
        inclusion_criteria = json_data.get("criteria", {}).get("inclusion_criteria", "")
        exclusion_criteria = json_data.get("criteria", {}).get("exclusion_criteria", "")

        # Fetch Title and Abstract from the database
        df = fetch_data_from_database()
        print(df)

        for index, row in df.iterrows():
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
                classification = "Exclude"

            # Print the classification for debugging
            print(f"Classification for Title: {Title}, Abstract: {Abstract} - {classification}")

            # Update classification in the database
            update_classification_in_database(Title, Abstract, classification)

           

        # Continue with the rest of your code...

    except Exception as e:
        # Print an error message
        print(f"Error processing request: {str(e)}")

        # Return JSON response with error
        return JSONResponse(content={"success": False, "error": f"Error processing request: {str(e)}"}, status_code=500)








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

@app.get("/filter")
def get_filtered_dataframe(include: bool = Query(True), exclude: bool = Query(True)):
    # Define the file path
    file_path = './GPT4_results.xlsx'


    df = pd.read_excel(file_path)


    df = df.where(pd.notna(df), None)


    df = df.map(lambda x: pd.to_datetime(x).to_pydatetime() if isinstance(x, pd.Timestamp) else x)


    df['ai_decision'] = df['ai_decision'].astype(str)


    if include and exclude:
        response_data = df.to_dict(orient='records')
    else:

        decision_value = 'Include' if include else 'Exclude'
        filtered_data = df[df['ai_decision'] == decision_value]

        response_data = filtered_data.to_dict(orient='records')

    return JSONResponse(content=response_data)



