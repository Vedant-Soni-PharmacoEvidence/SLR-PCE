from fastapi import FastAPI, Request, Form,UploadFile, File, Query,HTTPException
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


app = FastAPI() 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
openai.api_type = "azure"
openai.api_base = "https://pce-aiservices600098751.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "abe66c9c81b74e8d9a191f5a8b7932cc"
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

# Additional routes based on the selected model

@app.post("/chat_gpt_4")
async def analyse_gpt(request: Request):
    try:
        json_data = await request.json()
        inclusion_criteria = json_data.get("criteria", {}).get("inclusion_criteria", "")
        exclusion_criteria = json_data.get("criteria", {}).get("exclusion_criteria", "")

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

        # Add the 'ai_decision' column to the copied DataFrame
        result_data['ai_decision'] = classifications

        # Save the modified DataFrame
        if result_data is not None:
            global result_file_path
            result_file_path = "GPT4_results.xlsx"

            try:
                # Save the DataFrame to Excel
                result_data.to_excel(result_file_path, index=False)

                # Print a success message
                print("File has been successfully updated.")

                # Return JSON response with success and file path
                response_content = {"success": True, "result_file_path": result_file_path}
                return JSONResponse(content=response_content), RedirectResponse(url="/dashboard")

            except Exception as e:
                # Print an error message
                print(f"Error saving file: {str(e)}")

                # Return JSON response with error
                response_content = {"success": False, "error": f"Error saving file: {str(e)}"}
                return JSONResponse(content=response_content, status_code=500)

        else:
            # Print an error message
            print("Failed to save in file")

            # Return JSON response with error
            response_content = {"success": False, "error": "Failed to save in file"}
            return JSONResponse(content=response_content, status_code=500)

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






@app.get("/get_publications_by_year_and_type")
async def get_publications_by_year_and_type(selected_years: Optional[str] = Query(None, title="Selected Years"), selected_types: Optional[str] = Query(None, title="Selected Types")):
    try:
        # Fetch the latest data
        file_path = './GPT4_results.xlsx'
        df = pd.read_excel(file_path)
        

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

        # Get unique values for 'Publication Year' and 'Publication Type'
        unique_years = df['Publication Year'].unique().astype(str).tolist()
        unique_types = df['Publication Type'].unique().astype(str).tolist()

        # Group data by year and count publications
        publications_by_year = df.groupby('Publication Year').size().reset_index(name='Count')

        # Convert 'Publication Year' to string before returning the data
        publications_by_year['Publication Year'] = publications_by_year['Publication Year'].astype(str)

        # Group data by type and count publications
        publications_by_type = df.groupby('Publication Type').size().reset_index(name='Count')

        return JSONResponse(content={
            "unique_years": unique_years,
            "unique_types": unique_types,
            "publications_by_year": publications_by_year.to_dict(orient='records'),
            "publications_by_type": publications_by_type.to_dict(orient='records')
        })

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)
    






@app.get("/get_unique_values", response_class=JSONResponse)
async def get_unique_values():
    try:
        df = pd.read_excel("./Gpt Test.xlsx")
        unique_years = df["Publication Year"].unique().tolist()
        unique_types = df["Publication Type"].unique().tolist()

        return {"publicationYear": unique_years, "publicationType": unique_types}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")






@app.get("/filtered_data", response_class=HTMLResponse)
async def get_filtered_data(
    publication_year: List[str] = Query(..., description="Filter by Publication Year"),
    publication_type: List[str] = Query(..., description="Filter by Publication Type"),
):
    try:
        # Apply filters
        df = pd.read_excel("./Gpt Test.xlsx")
        filtered_data = df

        # Apply inclusive filtering logic based on selected criteria
        if publication_year:
            year_conditions = filtered_data["Publication Year"].isin(publication_year) | (filtered_data["Publication Year"] == "")
            filtered_data = filtered_data[year_conditions]
        if publication_type:
            type_conditions = filtered_data["Publication Type"].isin(publication_type) | (filtered_data["Publication Type"] == "")
            filtered_data = filtered_data[type_conditions]

        # Log the filtered data for troubleshooting
        print(filtered_data)

        # Convert filtered data to HTML table
        html_table = filtered_data.to_html(index=False)

        # Return the HTML response
        return HTMLResponse(content=html_table)

    except Exception as e:
        # Handle exceptions and log the error
        print(f"An error occurred: {str(e)}")
        return HTMLResponse(content=f"An error occurred: {str(e)}")
    




@app.get("/filtered_data")
async def get_filtered_data(
    publication_year: Optional[int] = Query(None),
    publication_type: Optional[str] = Query(None),
):
    filtered_data = data

    if publication_year:
        filtered_data = [item for item in filtered_data if item["Publication_Year"] == publication_year]

    if publication_type:
        filtered_data = [item for item in filtered_data if item["Publication_Type"] == publication_type]

    return filtered_data