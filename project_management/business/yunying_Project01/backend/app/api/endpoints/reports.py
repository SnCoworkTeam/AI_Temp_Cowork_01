from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.schemas.report import Report, ReportCreate
from app.services import report_generation_service, data_processing_service
from app.core.config import settings
from typing import List
import os
import uuid
from datetime import datetime

router = APIRouter()

# In-memory storage for mock reports
reports_db = {}

def process_report_task(report_id: str, report_in: ReportCreate):
    try:
        # Update status to processing
        if report_id in reports_db:
            reports_db[report_id].status = "processing"
            
        # Define callback to update progress
        def progress_callback(processed, total):
            if report_id in reports_db:
                reports_db[report_id].processed_rows = processed
                reports_db[report_id].total_rows = total
                reports_db[report_id].progress = int((processed / total) * 100) if total > 0 else 0

        # Run generation
        report = report_generation_service.generate_report(
            report_in, 
            data_processing_service, 
            report_id=report_id,
            progress_callback=progress_callback
        )
        
        # Update final report in DB
        reports_db[report_id] = report
    except Exception as e:
        if report_id in reports_db:
            reports_db[report_id].status = "failed"
        print(f"Report generation failed: {e}")

@router.post("/generate", response_model=Report)
def generate_report(report_in: ReportCreate, background_tasks: BackgroundTasks):
    report_id = str(uuid.uuid4())
    
    # Create initial report object
    report = Report(
        id=report_id,
        title=report_in.title,
        period_start=report_in.period_start,
        period_end=report_in.period_end,
        created_at=datetime.now(),
        status="pending",
        progress=0,
        total_rows=0,
        processed_rows=0,
        price_analysis=[],
        supply_demand_analysis=[],
        profit_analysis=[]
    )
    
    reports_db[report_id] = report
    
    # Start background task
    background_tasks.add_task(process_report_task, report_id, report_in)
    
    return report

@router.get("/{report_id}", response_model=Report)
def get_report(report_id: str):
    if report_id in reports_db:
        return reports_db[report_id]
    raise HTTPException(status_code=404, detail="Report not found")

@router.get("/", response_model=List[Report])
def list_reports():
    return list(reports_db.values())

@router.get("/download/{filename}")
def download_report(filename: str):
    file_path = os.path.join(settings.REPORT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    raise HTTPException(status_code=404, detail="File not found")
