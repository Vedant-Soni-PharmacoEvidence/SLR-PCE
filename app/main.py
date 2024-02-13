from fastapi import FastAPI, Request, Form,UploadFile, File,Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pathlib import Path
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles   
from .jinjatemplates import templates
from pydantic import BaseModel
import boto3
import json
import pandas as pd
from openpyxl import load_workbook
import io
import sys
import time
from mangum import Mangum
import psutil
import numpy as np  
from app.businesslogic import analytics as an
from typing import List
import openai
import matplotlib.pyplot as plt
import mpld3
import plotly.express as px
from typing import Optional


# excel_file_path = 'app/data/PSM.xlsx'
# output_file_path = 'app/data/output.csv'


openai.api_type = "azure"
openai.api_base = "https://pce-aiservices600098751.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "abe66c9c81b74e8d9a191f5a8b7932cc"
app = FastAPI() 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
handler=Mangum(app)
#STATIC FILES
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static") 

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/signin",response_class=HTMLResponse)
def updateExcel(request: Request):
    try:
        return templates.TemplateResponse("signin.html",{"request": request})
        
    except Exception as e:
        return {"ERROR":"SOMETHING WENT WRONG"}
        
@app.post("/signin", response_class=HTMLResponse)
async def signin(request: Request, username: str = Form(...),  password: str = Form(...)):
    time.sleep(3)
    # Check credentials
    if username == "test"  and password == "test":
        return templates.TemplateResponse("home.html", {"request": request, "username": username})
    else:
        return templates.TemplateResponse("landing.html", {"request": request, "error": "Invalid credentials. Please try again."})
    

    

@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/model", response_class=HTMLResponse)

def home(request: Request):
    return templates.TemplateResponse("model.html", {"request": request})


##################################################################################################################################################################
@app.post("/upload")
async def upload_excel(request: Request, file: UploadFile = File(...)):
    global uploaded_file_path
    try:
        # Save the uploaded Excel file to a directory (in this example, 'static')
        file_path = f"static/{file.filename}"
        
        
        # Save the file
        with open(file_path, "wb") as file_object:
            file_object.write(file.file.read())
        
        uploaded_file_path=file_path
        return JSONResponse(content={"success": True, "data": {"file_path": file_path}}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)
    

##################################################################################################################################################################
class ModelInfo(BaseModel):
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
@app.post("/chat_gpt_4")
async def analyse_gpt():
    # return {"message": "Analyzing GPT model"}
    global uploaded_file_path
    
    
    try:
            # Read Excel file into a Pandas DataFrame
        data = pd.read_excel(uploaded_file_path)

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
                     1. Condition: The study must mention one of the specified salt terms or their synonyms in relation to the specified health outcomes: 'salt', 'salt intake', 'sodium intake', '24-hour urinary excretion', 'spot urine analysis', 'sodium urine excretion', 'Nacl', 'low-salt', 'high-salt', 'low-sodium', 'high-sodium', 'sodium content', 'sodium', 'salt loaded', 'salt restricted', 'salt depletion', 'salted', 'medium salt', 'dietary salt', 'impact of sodium'. Synonyms of salt terms or association with salt should also be considered, except for salt intake as a covariate.
                     2. Health outcome: The study should focus on the specified health outcomes and must be directly related to the mentioned salt terms or their synonyms where the health outcomes can be from the following list 'anal fistula', 'Arthritis specific outcomes', 'any hepatic disorder','any Urologic Disease','any obstetrics and gynaecological disorder','Safety', 'Metabolic syndrome', 'blood pressure', 'any health outcome', 'Weight gain', 'BMI', 'HDL', 'LDL', 'Hypertension', 'Adverse events associated with sodium intake', 'All-cause mortality', 'any type of Cardiovascular disease', 'eGFR', 'any Gastrointesinal disease', 'Kidney Disease', 'heart failure', 'renal function', 'Cancer', 'diabetes' etc. Consider the synonyms of these terms also.
                     3. Population: The study must involve human adult patients aged 18 years and older.
                     4. Objective: Strictly check the study must provide a relationship or association between salt terms and health outcomes.
                     Exclusion Criteria:
                     1. Study Type: Strictly Exclude the citation if it falls under the following study types: Literature reviews, meta-analysis, systematic reviews, narrative reviews, case reports, case series.
                     2. Population: Strictly mark Studies excluded that involving adolescents, children, animals (like mice, rats, etc).
                     3. Exclude studies that mention relative salt term with mineral and hormones.
                     4. Exclude studies analyzing populations with less than 10 individuals.
                     5. Exclude studies focusing on populations of pregnant women, child-bearing women, lactating mothers, or preeclampsia but not premenopausal or menopausal.
                     6. Exclude studies evaluating the association of genetic variation, polymerase chain reaction, single nucleotide polymorphism, or any synonym  with health outcomes and/or outcome responses to salt
                     7. Strictly exclude studies that fail to demonstrate a direct relationship or association between salt terms and health outcomes.
                     8. Strictly exclude studies that only estimating the salt or sodium concentration among population or groups by different estimation methods.
                     9. Strictly exclude studies that only assessing salt intake as covariate or adjusted factors or covariate adjusted models but not assessing the relationship of salt and health outcomes.
                     10. Exclude studies focusing solely on the influence of sodium or salt on the response to pharmacological or non-pharmacological interventions without investigating the relationship with health outcomes.
                     11. Exclude studies assessing the association of pharmacological or non-pharmacological interventions with health outcomes with salt intake as covariate or adjusted factors or studying "serum sodium", "plasma sodium", adherence, compliance without investigating the relationship with health outcomes.
                     12. Strictly mark the citation excluded if it is review or pooled study.
                 
                 
                     Title: {Title}
                     Abstract: {Abstract}
                '''
            }

            completion = openai.ChatCompletion.create(
                engine="GPT-4",
                messages=[message_text],
                temperature=0.2,
                max_tokens=2000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )

            response_text = completion.choices[0].message['content']

            # Refine Parsing Logic
            if "included" in response_text.lower():
                classification = "Include"
            else:
                classification = "Exclude"  # Placeholder for manual verification

            titles.append(Title)
            abstracts.append(Abstract)
            classifications.append(classification)

        result_df = pd.DataFrame({
            'Title': titles,
            'Classification': classifications
        })
        data['ai_decision'] = classifications
        global result_file_path

        result_file_path = "GPT4_results_with_decision.xlsx"
        data.to_excel(result_file_path, index=False)
        

        # Return JSON response with success and file path
        response_content = {"success": True, "result_file_path": result_file_path}

        # Redirect to /dashboard upon successful file saving
        return JSONResponse(content=response_content), RedirectResponse(url="/dashboard")
    
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/claude_bedrock_edition_")
async def analyse_aws():
    return {"message": "Analyzing AWS model"}

@app.post("/nlp_model")
async def analyse_nlp():
    return {"message": "Analyzing NLP model"}

@app.post("/google_gemini")
async def analyse_google():
    return {"message": "Analyzing Google model"}

################################################################################    GPT    ####################################################################################################
class GPTRequest(BaseModel):
    uploaded_file_path:str
    model: str


################################################################################    GPT END   ####################################################################################################


@app.get("/dashboard")
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "is_dashboard": True})


# @app.get("/get_excel_data")
# async def get_excel_data():
#     file_path = 'app/data/GPT4_results_with_decision.xlsx'
#     global result_file_path
#     try:
#         data = pd.read_excel(file_path)  # Set header=0 to use the first row as column names
#         columns = [{"title": col} for col in data.columns]
#         data_dict = {"data": data.to_dict(orient="records"), "columns": columns}
#         return JSONResponse(content={"success": True, "data": data_dict})
#     except Exception as e:
#         return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


file_path = 'app/data/Test.xlsx'
data = pd.read_excel(file_path)



@app.get("/get_publications_by_year_and_type")
async def get_publications_by_year_and_type(selected_years: Optional[str] = None, selected_types: Optional[str] = None):
    try:
        # Fetch the latest data
        df = pd.DataFrame(data)

        # Convert numeric columns to standard Python types
        df['Publication Year'] = df['Publication Year'].astype(int)

        # Filter data based on selected years and types
        if selected_years:
            selected_years_list = selected_years.split(',')
            df = df[df['Publication Year'].astype(str).isin(selected_years_list)]

        if selected_types:
            selected_types_list = selected_types.split(',')
            df = df[df['Publication Type'].astype(str).isin(selected_types_list)]
        if selected_years and selected_types:
            df = df[df['Publication Year'].astype(str).isin(selected_years_list) & df['Publication Type'].astype(str).isin(selected_types_list)]
        # Drop NaN values from the DataFrame
        df = df.dropna()

        # Group data by year and count publications
        publications_by_year = df.groupby('Publication Year').size().reset_index(name='Count')

        # Convert 'Publication Year' to string before returning the data
        publications_by_year['Publication Year'] = publications_by_year['Publication Year'].astype(str)

        # Group data by type and count publications
        publications_by_type = df.groupby('Publication Type').size().reset_index(name='Count')

        return JSONResponse(content={
            "publications_by_year": publications_by_year.to_dict(orient='records'),
            "publications_by_type": publications_by_type.to_dict(orient='records')
        })

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

















