from fastapi import FastAPI, Request, Form,UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
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

        result_df.to_excel("GPT4_results.xlsx", index=False)
        return JSONResponse(content={"success": True})
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




















































@app.get("/dashboard",response_class=HTMLResponse)
def dashboard(request: Request):
    try:
        global table_metadata
        global df
        global firstkey
        firstkey = next(iter(table_metadata))
        an_obj = an.analyticsClass()
        df = an_obj.create_qa_dataframe(firstkey, table_metadata, excel_file_path, output_file_path)
        print("GLOBAL DATAFRAME REFRESHED")
        table_list = list(table_metadata.keys())
        return templates.TemplateResponse("dashboard.html", {"request": request, "table_list" : table_list, "table_metadata":table_metadata})
    except Exception as e:
        return {"ERROR":"SOMETHING WENT WRONG"}
    
@app.get("/updateexcel",response_class=HTMLResponse)
def updateExcel(request: Request):
    try:
        return templates.TemplateResponse("updateexcel.html", {"request": request})
    except Exception as e:
        return {"ERROR":"SOMETHING WENT WRONG"}
    
@app.get("/update-metadata")
def update_metadata(table: str):
    try:
        global df
        an_obj = an.analyticsClass()
        df = an_obj.create_qa_dataframe(table, table_metadata, excel_file_path, output_file_path)
        print("DATAFRAME UPDATED")
        print(df)
        metadata = table_metadata.get(table, {})
        return JSONResponse(content=metadata)
    except Exception as e:
        return JSONResponse(content={"ERROR": "SOMETHING WENT WRONG"}, status_code=500)
    
class RequestData(BaseModel):
    prompt_input: str 

@app.post("/generate")
def generate(o: RequestData):
    try:
        an_obj= an.analyticsClass()
        result= an_obj.genAIQA(df, o.prompt_input)
        return JSONResponse(content={"generated_output": result}) 
    except Exception as e:
        error=str(e)  
        return JSONResponse(content={"generated_output": "Issue occured in API."+ error})
    


@app.post("/updateexcelexecute")
def updateExcelExecute(o: RequestData):
    try:
        bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-west-2')
        global excel_file_path
        input_text = o.prompt_input
        sheet_name = 'General'

        # Read the Excel file and create a DataFrame
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        column_names = df.columns.tolist()
        input_text=o.prompt_input

        words =  input_text.split()
        if len(input_text) == 0 or input_text.replace(" ", "").isdigit() or all(
                word.isdigit() or any(not char.isalpha() for char in word) for word in words):
            return {"error":'Please enter a valid input'}

        else:
            print(df)
            prompt = """Human: Please regard the following data for updation:\n {}. Please provide Python code to Human Input "{}". 
            There are only two attributes Key and Value (Integer Only). Print the data as per the requirement. Avoid including introductory lines or explanations in the python code and exclude user-specific comments or instructions such as paths or notes for replacement.
            Before Generating python code please cross verify all the code if any syntax errors please resolve before sending repsonse. 
            Python code always should be a single string with proper line breakers and comments its can't be a bullet points and it will start with import only,
            After importing the libraries please keep the code:
            pd.set_option('display.max_rows', None)  # Set the maximum number of rows to None for unlimited rows
            pd.set_option('display.max_columns', None)  # Set the maximum number of columns to None for unlimited columns
            In case any extra text came with python code please put those in a comment.
            This string can be really long please give in single string only, and dataframe variable always its a df only.
            "please don't support Garbage text, Single word, and Meaningless sentences", and just print('Please enter valid Text').
            Do not initialize df as it is already initialized.
            Make sure to take exact Key names and value from the Human Input for update.
            Use try catch except block, on successful try print about what updation is made and on exception print error message. Do not print any other thing in code except these. 
            Assistant:
            """.format(df.columns, input_text)
            if column_names != []:
                body = json.dumps({
                    "prompt": prompt, 
                    "max_tokens_to_sample": 2048,
                    "temperature": 0.5,
                    "top_k": 250,
                    "top_p": 0.5,
                    })
                modelId = 'anthropic.claude-v2'  
                accept = 'application/json'
                contentType = 'application/json'
                response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
                response_body = json.loads(response.get('body').read())
                result = response_body.get('completion')
                print(result)
                if 'python' in result.lower() or 'import' in result:
                    try:
                        code_start = result.find("```python")
                        code_end = result.find("```", code_start + len("```python"))
                        python_code = result[code_start + len("```python") : code_end]

                        # Execute the Python code and capture the output
                        old_stdout = sys.stdout
                        new_stdout = io.StringIO()
                        sys.stdout = new_stdout
                        exec(python_code) 
                        code_output = new_stdout.getvalue()
                        sys.stdout = old_stdout  
                        result=code_output
                        print(code_output)
                        
                    except Exception as e:
                        result = 'Something went wrong while doing updation, please enter your input again'
        print("HELLO")
        for process in psutil.process_iter(['pid', 'name']):
            if 'excel.exe' in process.info['name'].lower():
                print(f"Closing Excel process with PID {process.info['pid']}")
                psutil.Process(process.info['pid']).terminate()
                print("Excel process closed successfully.")
        print("HELLO")
        with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            print("HELLO")
            writer.book[sheet_name].index = None
            writer.book[sheet_name].sheet_view.viewTabSelected = 'false'
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print("HELLO")
        return JSONResponse(content={"generated_output": result}) 
    except Exception as e:
        error=str(e)  
        return JSONResponse(content={"generated_output": "Issue occured in API."+ error})
      



    
