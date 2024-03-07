import PyPDF2
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, UploadFile, File

import openai

# Initialize OpenAI API
openai.api_type = "azure"
openai.api_base = "https://pce-aiservices600098751.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "abe66c9c81b74e8d9a191f5a8b7932cc"

app = FastAPI()

def extract_text_from_pdf(pdf_file):
    text = ""
    with open(pdf_file, 'rb') as file:
        reader = PyPDF2.PdfFileReader(file)
        for page_num in range(reader.numPages):
            text += reader.getPage(page_num).extractText()
    return text

def split_into_chunks(text, chunk_size=3500):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    return chunks

def summarize_chunk(chunk):
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Summarize the following text:\n\n{chunk}",
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].text.strip()

def summarize_pdf(pdf_file):
    pdf_text = extract_text_from_pdf(pdf_file)
    chunks = split_into_chunks(pdf_text)
    
    with ThreadPoolExecutor() as executor:
        summaries = list(executor.map(summarize_chunk, chunks))
    
    combined_summary = "\n".join(summaries)
    return combined_summary

@app.post("/summarize-pdf/")
async def summarize_pdf_endpoint(pdf_file: UploadFile = File(...)):
    try:
        summary = summarize_pdf(pdf_file.file)
        return {"summary": summary}
    except Exception as e:
        return {"error": str(e)}
