import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User
from .auth import read_bearer_token, JWT_SECRET, JWT_ALG
from jose import jwt, JWTError
from scripts.import_excel import read_import_state, run_import
from services.ev_rag import ev_rag_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])

def get_current_admin_id(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> int:
    token = read_bearer_token(authorization)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user ID")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user.id

@router.post("/upload-dataset")
async def upload_dataset(
    file: UploadFile = File(...), 
    admin_id: int = Depends(get_current_admin_id),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are allowed")

    # Define the save path
    raw_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the file with a specific name that run_import prefers
    target_path = raw_dir / "latest_upload_import.xlsx"
    
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Trigger the import script logic
        result = run_import()
        if not result.get("success"):
            raise RuntimeError(result.get("message") or "Unknown import error")
        return {
            "success": True,
            "message": "Dataset uploaded and processed successfully.",
            "import": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.get("/stats")
def get_stats(admin_id: int = Depends(get_current_admin_id), db: Session = Depends(get_db)):
    from models import Vehicle
    total_vehicles = db.query(Vehicle).count()
    import_state = read_import_state() or {}
    try:
        rag_vehicle_count = len(ev_rag_service.artifacts.vehicles)
    except Exception:
        rag_vehicle_count = 0
    return {
        "success": True,
        "total_vehicles": total_vehicles,
        "rag_vehicle_count": rag_vehicle_count,
        "faiss_ready": import_state.get("faiss_ready", False),
        "last_dataset_sync": import_state.get("imported_at"),
        "source_file": import_state.get("dataset_name"),
        "api_status": "Healthy",
    }
