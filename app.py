import subprocess

def run_fastapi_app():
    command = "uvicorn app.main:app --reload"
    subprocess.run(command, shell=True)

if __name__ == "__main__":
    run_fastapi_app()
