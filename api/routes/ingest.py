import shutil, tempfile, os
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from retrieval.store import ingest_document

router = APIRouter()


@router.post("/")
async def ingest_files(files: List[UploadFile] = File(...)):
    """
    Upload one or more PDF / DOCX / TXT files.
    Each file is saved to a temp path, ingested, then cleaned up.
    """
    results = []

    for file in files:
        suffix = os.path.splitext(file.filename)[-1].lower()
        if suffix not in {".pdf", ".docx", ".txt"}:
            results.append({"file": file.filename, "error": "Unsupported file type"})
            continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        try:
            result = ingest_document(
                tmp_path,
                original_filename=file.filename   # ← pass real name here
            )
            result["file"] = file.filename
            results.append(result)
        except Exception as e:
            results.append({"file": file.filename, "error": str(e)})
        finally:
            os.unlink(tmp_path)
