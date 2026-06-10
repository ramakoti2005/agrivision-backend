from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import json

from app.schemas import AnalysisResponse, ScanHistorySchema
from app.services.preprocessing import preprocess_image
from app.services.inference import run_inference
from app.services.auth import get_current_user
from app.models import User, ScanHistory
from app.database import get_db

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_leaf_image(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint to upload a leaf image and get a disease analysis report.
    """
    # 1. Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    
    try:
        # Read the file bytes
        image_bytes = await file.read()
        
        # 2. Preprocess the image
        preprocessed_image = preprocess_image(image_bytes)
        
        # 3. Run Inference
        response_data = run_inference(preprocessed_image, filename=file.filename)
        
        # 4. Save scan to database history
        try:
            db_scan = ScanHistory(
                user_id=current_user.id,
                plant_name=response_data.plant_name,
                scientific_name=response_data.scientific_name,
                confidence=response_data.confidence,
                image_quality=response_data.image_quality,
                possible_matches=json.dumps(response_data.possible_matches),
                issues_detected=json.dumps(response_data.issues_detected),
                solution_suggestion=response_data.solution_suggestion
            )
            db.add(db_scan)
            db.commit()
        except Exception as db_err:
            # Print database errors, but don't crash user's instant response if saving fails
            print(f"Error saving scan history: {db_err}")
        
        # 5. Return structured JSON report
        return response_data
        
    except Exception as e:
        # In a real app, log the error before returning
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")

@router.get("/history", response_model=List[ScanHistorySchema])
def get_scan_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint to retrieve the scan history for the logged-in user.
    """
    try:
        scans = db.query(ScanHistory).filter(ScanHistory.user_id == current_user.id).order_by(ScanHistory.id.desc()).all()
        results = []
        for s in scans:
            try:
                possible = json.loads(s.possible_matches) if s.possible_matches else []
            except Exception:
                possible = []
            try:
                issues = json.loads(s.issues_detected) if s.issues_detected else []
            except Exception:
                issues = []
            
            results.append({
                "id": s.id,
                "plant_name": s.plant_name,
                "scientific_name": s.scientific_name,
                "confidence": s.confidence,
                "possible_matches": possible,
                "image_quality": s.image_quality,
                "issues_detected": issues,
                "solution_suggestion": s.solution_suggestion,
                "timestamp": s.timestamp
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scan history: {str(e)}")
