import os
import openai
import pandas as pd
import zipfile
import tempfile
from fastapi import FastAPI, File, UploadFile, Form
from typing import Optional
import os
# Initialize FastAPI app
app = FastAPI()


# Set your OpenAI API Key


ALLOWED_EXTENSIONS = {".csv", ".txt", ".md", ".zip"}  # Added '.zip'

def allowed_file(filename: str) -> bool:
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

@app.post("/api/")
async def process_question(
    question: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    extracted_data = ""

    # If a file is uploaded, process it
    if file:
        filename = file.filename

        if not allowed_file(filename):
            return {"error": "Unsupported file format. Upload .csv, .txt, .md, or .zip"}

        contents = file.file.read()

        # Handle ZIP files
        if filename.endswith(".zip"):
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "uploaded.zip")
                with open(zip_path, "wb") as f:
                    f.write(contents)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)
                    for extracted_file in zip_ref.namelist():
                        ext = os.path.splitext(extracted_file)[1]
                        if ext in {".csv", ".txt", ".md"}:
                            with open(os.path.join(temp_dir, extracted_file), "r", encoding="utf-8") as f:
                                extracted_data += f.read() + "\n"

        # Handle CSV files
        elif filename.endswith(".csv"):
            from io import StringIO
            df = pd.read_csv(StringIO(contents.decode("utf-8")))
            extracted_data = df.to_string()

        # Handle TXT and MD files
        elif filename.endswith((".txt", ".md")):
            extracted_data = contents.decode("utf-8")

    # Prepare the OpenAI query
    prompt = f"Question: {question}\n"
    if extracted_data:
        prompt += f"File Data:\n{extracted_data}\n"

    prompt += "Answer:"

    # Call OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    answer = response["choices"][0]["message"]["content"]

    return {"question": question, "answer": answer}
