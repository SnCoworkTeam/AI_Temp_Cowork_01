from fastapi import APIRouter, UploadFile, File, Form
from app.schemas.common import ResponseBase
import os
import shutil
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=ResponseBase)
async def upload_file(
    file: UploadFile = File(...),
    type: str = Form(...)
):
    # Only keep the latest data file
    file_path = os.path.join(settings.UPLOAD_DIR, "data_file.xlsx")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return ResponseBase(success=True, message=f"Uploaded {file.filename} successfully")
