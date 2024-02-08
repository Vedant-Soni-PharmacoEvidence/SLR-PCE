@app.post("/updateexcelexecute")
def updateExcelExecute(o: RequestData):
    try:
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

        with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            writer.book[sheet_name].index = None
            writer.book[sheet_name].sheet_view.viewTabSelected = 'false'
            df.to_excel(writer, sheet_name=sheet_name, index=False)

        return JSONResponse(content={"generated_output": result}) 
    except Exception as e:
        error=str(e)  
        return JSONResponse(content={"generated_output": "Issue occured in API."+ error})