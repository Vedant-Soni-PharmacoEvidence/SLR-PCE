from fastapi import (
    FastAPI,
    Request,
    Form,
    UploadFile,
    File,
    Query,
    Depends,
    HTTPException,
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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
    db_conn = psycopg2.connect(
        host="localhost", database="PCE", user="postgres", password="root"
    )
    return db_conn


openai.api_type = "azure"
openai.api_base = "https://pce-aiservices600098751.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "abe66c9c81b74e8d9a191f5a8b7932cc"


# STATIC FILES
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


result_file_path = "GPT4_results.xlsx"
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(timestamp)


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/signin", response_class=HTMLResponse)
def updateExcel(request: Request):
    try:
        return templates.TemplateResponse("signin.html", {"request": request})

    except Exception as e:
        return {"ERROR": "SOMETHING WENT WRONG"}


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
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "is_dashboard": True}
    )

@app.get("/secondpasshtml", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("secondpass.html", {"request": request})
##################################################################################################################################################################


@app.post("/signin", response_class=HTMLResponse)
async def signin(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    time.sleep(3)
    # Check credentials
    if username == "test" and password == "test":
        return templates.TemplateResponse(
            "home.html", {"request": request, "username": username}
        )
    else:
        return templates.TemplateResponse(
            "landing.html",
            {"request": request, "error": "Invalid credentials. Please try again."},
        )


class ModelInfo(BaseModel):
    model: str


class GPTRequest(BaseModel):
    uploaded_file_path: str
    model: str


@app.post("/analyse")
async def analyse_model(model_info: ModelInfo):
    # Process the received model information
    selected_model = model_info.model
    print(f"Received model information: {selected_model}")

    # You can perform additional processing or return a response as needed
    return {"message": f"Model information for {selected_model} received successfully"}


async def show_result(request: Request):
    return templates.TemplateResponse(
        "result.html", {"request": request, "model": "GPT"}
    )


project_name = "pankaj01"


def convert_excel_to_csv(excel_file_path):
    csv_file_path = os.path.splitext(excel_file_path)[0] + ".csv"
    df = pd.read_excel(excel_file_path)
    df.to_csv(csv_file_path, index=False)
    return csv_file_path


def push_csv_to_database(csv_file_path):
    try:

        df = pd.read_csv(csv_file_path, encoding="ISO-8859-1")
        df = df.dropna()

        reset_query = f"ALTER SEQUENCE {project_name}.paperid_sequence RESTART WITH 1;"
        db.cursor.execute(reset_query)
        db.dbconn.commit()

        truncate_import_query = f'TRUNCATE TABLE {project_name}."import";'
        db.cursor.execute(truncate_import_query)
        db.dbconn.commit()

        truncate_analyzed_query = f"TRUNCATE TABLE {project_name}.analyzed;"
        db.cursor.execute(truncate_analyzed_query)
        db.dbconn.commit()

        for index, row in df.iterrows():
            insert_query = f"""
                INSERT INTO {project_name}."import" ("paper_id","Title", "Abstract", "PCE ID", "Decision", "Publication Year", "Publication Type", "Reason")
                VALUES (nextval('{project_name}.paperid_sequence'),%s, %s, %s, %s, %s, %s, %s)
            """
            db.cursor.execute(
                insert_query,
                (
                    row["Title"],
                    row["Abstract"],
                    row["PCE ID"],
                    row["Decision"],
                    row["Publication Year"],
                    row["Publication Type"],
                    row["Reason"],
                ),
            )
            db.dbconn.commit()

        db_conn = get_db()
        db_cursor = db_conn.cursor()

        update_query = f"""
            UPDATE {project_name}.import
            SET project_id = '{project_name}';
        """
        db_cursor.execute(update_query)
        db_conn.commit()

        affected_rows = db_cursor.rowcount
        return {
            "message": f"Data from {csv_file_path} has been uploaded to the database. {affected_rows} rows affected."
        }

    except Exception as e:
        return {"error": str(e)}


@app.post("/upload")
async def upload_excel(request: Request, file: UploadFile = File(...)):
    try:

        excel_file_path = f"static/{file.filename}"
        with open(excel_file_path, "wb") as file_object:
            file_object.write(file.file.read())

        csv_file_path = convert_excel_to_csv(excel_file_path)

        result = push_csv_to_database(csv_file_path)

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/cleandb")
async def clean_database():
    try:

        truncate_import_query = f'TRUNCATE TABLE {project_name}."import";'
        db.cursor.execute(truncate_import_query)
        db.dbconn.commit()

        truncate_analyzed_query = f"TRUNCATE TABLE {project_name}.analyzed;"
        db.cursor.execute(truncate_analyzed_query)
        db.dbconn.commit()

        return JSONResponse(
            content={
                "message": "Your Project data has been cleaned! Upload new data to continue."
            },
            status_code=200,
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/dataflush")
def dbdatadelete():

    try:

        truncate_query = f"""
            TRUNCATE TABLE {project_name}.import RESTART IDENTITY;
        """
        db.cursor.execute(truncate_query)
        db.dbconn.commit()

        return {"message": f"Data table truncated."}

    except Exception as e:
        print(e)
        return {"error": str(e)}


# Define a rate limit for processing entries per minute
entries_per_minute_limit = 5


# Fetch data from the database
def fetch_data_from_database():
    db_conn = get_db()
    db_cursor = db_conn.cursor()

    fetch_query = f"""
        SELECT *
        FROM {project_name}.import
        ORDER BY "paper_id" ASC; 
    """
    db_cursor.execute(fetch_query)
    rows = db_cursor.fetchall()

    # Close the cursor and connection
    db_cursor.close()
    db_conn.close()

    # Convert the result to a DataFrame
    columns = [
        "project_id",
        "paper_id",
        "Title",
        "Abstract",
        "PCE ID",
        "Decision",
        "Publication Year",
        "Publication Type",
        "Reason",
    ]
    df = pd.DataFrame(rows, columns=columns)
    # print(df)

    return df


# Assume you have a function to update the classification result in the database
def insert_data_into_analyzed_table(df):
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    print(df)

    for index, row in df.iterrows():
        project_name = row["project_id"]
        paper_id = row["paper_id"]
        title = row["Title"].replace("'", "''")  # Properly escape single quotes
        abstract = row["Abstract"].replace("'", "''")  # Properly escape single quotes
        ai_decision = row["ai_decision"].replace("'", "''")

        insert_query = f"""
        INSERT INTO {project_name}.analyzed ("project_id", "paper_id", "Title", "Abstract", "PCE ID", "Decision", "Publication Year", "Publication Type", "Reason", "ai_decision")
        VALUES ('{project_name}', '{paper_id}', '{title}', '{abstract}', '{row["PCE ID"].replace("'", "''")}', '{row["Decision"].replace("'", "''")}', '{row["Publication Year"]}', '{row["Publication Type"]}', '{row["Reason"]}', '{ai_decision}');
            """
        db_cursor.execute(insert_query)

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
        last_processed_paper_id = json_data.get("last_processed_paper_id", 0)
        analyzed_count = json_data.get("analyzed_count", 0)
        total_rows_to_analyze = json_data.get("total_rows_to_analyze", None)

        if total_rows_to_analyze is None:
            # If total_rows_to_analyze is not provided, default to the total number of rows in the dataset
            df = fetch_data_from_database()
            total_rows_to_analyze = len(df)

        # Fetch Title and Abstract from the database
        df = fetch_data_from_database()

        # Process data in batches
        last_processed_paper_id, analyzed_count, analyzed_df = process_data_in_batches(
            df,
            inclusion_criteria,
            exclusion_criteria,
            last_processed_paper_id,
            analyzed_count,
            total_rows_to_analyze,
        )

        # Continue with the rest of your code...

    except Exception as e:
        # Print an error message
        print(f"Error processing request: {str(e)}")

        # Return JSON response with error
        return JSONResponse(
            content={"success": False, "error": f"Error processing request: {str(e)}"},
            status_code=500,
        )


analyzed_df = pd.DataFrame()


def get_last_processed_paper_id_from_analyzed_table():
    db_conn = get_db()
    db_cursor = db_conn.cursor()

    # Fetch the last row from the analyzed table
    query = f'SELECT "paper_id" FROM {project_name}.analyzed ORDER BY "paper_id" DESC LIMIT 1;'
    db_cursor.execute(query)
    result = db_cursor.fetchone()

    db_cursor.close()
    db_conn.close()

    if result:
        return result[0]
    else:
        return None


# Define a function to fetch and update data in batches
def process_data_in_batches(
    df,
    inclusion_criteria,
    exclusion_criteria,
    last_processed_paper_id,
    analyzed_count,
    total_rows_to_analyze,
):
    processed_rows = []
    global analyzed_df

    # Check the last_processed_paper_id from the analyzed table
    last_processed_paper_id_analyzed = get_last_processed_paper_id_from_analyzed_table()

    # If analyzed table is not empty, use the last_processed_paper_id from analyzed table
    if not pd.isnull(last_processed_paper_id_analyzed):
        last_processed_paper_id = int(last_processed_paper_id_analyzed)

    # Filter rows where paper_id is greater than the last processed one
    pending_rows = df[df["paper_id"] > last_processed_paper_id]

    # Limit the number of rows processed per minute
    rows_to_process = pending_rows.head(entries_per_minute_limit)
    # print(rows_to_process)

    for index, row in rows_to_process.iterrows():
        paper_id = row["paper_id"]
        Title = row["Title"]
        Abstract = row["Abstract"]

        message_text = {
            "role": "system",
            "content": f"""
                Based on the below exclusion and inclusion criteria, please classify the given Citation as "Included" or "Excluded".
                Apply the Exclusion Criteria first. If any statement in the Exclusion Criteria is true, mark the citation as "Excluded".
                If the citation passes the Exclusion Criteria, then check the Inclusion Criteria. Mark the Citation as "Included" only if it strictly and exactly passes all Inclusion Criteria statements; otherwise, mark the citation as "Excluded".
                Inclusion Criteria:
                {inclusion_criteria}
                Exclusion Criteria:
                {exclusion_criteria}

                Title: {Title}
                Abstract: {Abstract}
            """,
        }

        completion = openai.ChatCompletion.create(
            engine="GPT-4",
            messages=[message_text],
            temperature=0.2,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
        )

        response_text = completion.choices[0].message["content"]

        if "included" in response_text.lower():
            classification = "Include"
        else:
            classification = "Exclude"

        print(
            f"Classification for Title: {Title}, Abstract: {Abstract} - {classification}"
        )

        # Update classification in the database
        # update_classification_in_database(paper_id, Title, Abstract, classification)
        row["ai_decision"] = classification
        processed_rows.append(row)

        # Update the last_processed_paper_id
        last_processed_paper_id = paper_id

        # Update counters
        analyzed_count += 1

        # Check if the total number of rows to analyze is reached
        if analyzed_count >= total_rows_to_analyze:
            break

    analyzed_df = pd.DataFrame(processed_rows)
    insert_data_into_analyzed_table(analyzed_df)

    return last_processed_paper_id, analyzed_count, analyzed_df


@app.post("/claude_bedrock_edition_")
async def analyse_aws():
    return {"message": "Analyzing AWS model"}


@app.post("/nlp_model")
async def analyse_nlp():
    return {"message": "Analyzing NLP model"}


@app.post("/google_gemini")
async def analyse_google():
    return {"message": "Analyzing Google model"}


def fetch_analyzed_data():
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    fetch_query = f"""
        SELECT * FROM {project_name}.analyzed;
    """
    db_cursor.execute(fetch_query)
    rows = db_cursor.fetchall()
    # Close the cursor and connection
    db_cursor.close()
    db_conn.close()
    # Convert the result to a DataFrame
    columns = [
        "project_id",
        "paper_id",
        "Title",
        "Abstract",
        "PCE ID",
        "Decision",
        "Publication Year",
        "Publication Type",
        "Reason",
        "ai_decision",
        "ai_reason",
    ]
    df = pd.DataFrame(rows, columns=columns)
    return df


@app.get("/analysis_info")
async def get_analysis_info():
    try:
        db_conn = get_db()
        db_cursor = db_conn.cursor()

        # Get the total count of rows in the import table
        total_rows_query = f'SELECT COUNT(*) FROM {project_name}."import";'
        db_cursor.execute(total_rows_query)
        total_rows = db_cursor.fetchone()[0]

        # Get the count of analyzed decisions
        analyzed_count_query = f"SELECT COUNT(*) FROM {project_name}.analyzed;"
        db_cursor.execute(analyzed_count_query)
        analyzed_count = db_cursor.fetchone()[0]

        # Calculate the remaining count
        remaining_count = total_rows - analyzed_count
        # print(analyzed_count)
        # print(remaining_count)

        # Close the cursor and connection
        db_cursor.close()
        db_conn.close()

        return {"analyzed_count": analyzed_count, "remaining_count": remaining_count}

    except Exception as e:
        return {"error": str(e)}


@app.get("/get_metrics")
async def get_metrics(
    include: bool = Query(False, description="Include decision metrics")
):
    try:
        df = fetch_analyzed_data()

        actual_values = df["Decision"]
        predicted_values = df["ai_decision"]

        # Calculate accuracy
        accuracy = metrics.accuracy_score(actual_values, predicted_values)

        # Calculate precision, recall, and F1-score
        precision, recall, f1_score, _ = metrics.precision_recall_fscore_support(
            actual_values,
            predicted_values,
            average="binary",
            pos_label="Include",
            zero_division=1,
        )

        # Create a summary table
        summary_table = pd.DataFrame(
            {
                "Metric": ["Accuracy", "Precision", "Recall", "F1-Score"],
                "Value": [accuracy, precision, recall, f1_score],
            }
        )

        # Convert the summary table to standard Python types
        summary_json = summary_table.to_dict(orient="records")

        # Additional decision metrics
        decision_metrics = {
            "total_included_human": int(df[df["Decision"] == "Include"].shape[0]),
            "total_excluded_human": int(df[df["Decision"] == "Exclude"].shape[0]),
            "totalHuman": int(df["Decision"].count()),
            "total_included_ai": int(df[df["ai_decision"] == "Include"].shape[0]),
            "total_excluded_ai": int(df[df["ai_decision"] == "Exclude"].shape[0]),
            "totalAI": int(df["ai_decision"].count()),
            "conflicting_decisions_include": int(
                df[
                    (df["Decision"] == "Include") & (df["ai_decision"] == "Exclude")
                ].shape[0]
            ),
            "conflicting_decisions_exclude": int(
                df[
                    (df["Decision"] == "Exclude") & (df["ai_decision"] == "Include")
                ].shape[0]
            ),
            "totalConflicts": int(df[df["Decision"] != df["ai_decision"]].shape[0]),
            "accuracy_percentage": float(accuracy)
            * 100,  # Convert to float for JSON serialization
        }

        # Count 'Include' and 'Exclude' values in 'ai_decision' column
        ai_decision_counts = df["ai_decision"].value_counts().reset_index()

        ai_decision_data = ai_decision_counts.to_dict(orient="records")

        # Convert exclusion reason counts to a list of dictionaries
        exclusion_reason_counts = df["Reason"].value_counts().reset_index()
        exclusion_reason_counts.columns = ["Reason", "Count"]

        exclusion_reason_list = exclusion_reason_counts.to_dict(orient="records")

        # Return the JSON response
        response_content = {
            "success": True,
            "data": {
                "summary_metrics": summary_json,
                "exclusion_reason_counts": exclusion_reason_list,
                "decision_metrics": decision_metrics,
                "ai_decision_data": ai_decision_data,
            },
        }
        return JSONResponse(content=response_content, status_code=200)

    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)}, status_code=500
        )


@app.get("/filter")
def get_filtered_dataframe(include: bool = Query(True), exclude: bool = Query(True)):
    # Define the file path

    df = fetch_analyzed_data()

    df = df.where(pd.notna(df), None)

    df = df.map(
        lambda x: (
            pd.to_datetime(x).to_pydatetime() if isinstance(x, pd.Timestamp) else x
        )
    )

    df["ai_decision"] = df["ai_decision"].astype(str)

    if include and exclude:
        response_data = df.to_dict(orient="records")
    else:

        decision_value = "Include" if include else "Exclude"
        filtered_data = df[df["ai_decision"] == decision_value]

        response_data = filtered_data.to_dict(orient="records")

    return JSONResponse(content=response_data)


@app.get("/secondpass", response_class=JSONResponse)
async def second_pass(request: Request):
    try:
        # Fetch rows with "Include" in ai_decision column
        db_conn = get_db()
        db_cursor = db_conn.cursor()
        
        fetch_query = f"""
            SELECT *
            FROM {project_name}.analyzed
            WHERE ai_decision = 'Include';
        """
        
        # Execute the query
        db_cursor.execute(fetch_query)
        
        # Fetch all rows
        rows = db_cursor.fetchall()

        # Close the cursor and connection
        db_cursor.close()
        db_conn.close()

        # Convert the result to a DataFrame
        columns = [
            "project_id",
            "paper_id",
            "Title",
            "Abstract",
            "PCE ID",
            "Decision",
            "Publication Year",
            "Publication Type",
            "Reason",
            "ai_decision",
            "ai_reason",
        ]
        df = pd.DataFrame(rows, columns=columns)

        # Convert DataFrame to JSON with the 'df' key
        df_json = df.to_json(orient="records")
        response = {"df": df_json}

        return response

    except Exception as e:
        return {"error": str(e)}