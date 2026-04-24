from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, SavedComparison, Vehicle
from schemas import GarageSaveRequest, GarageOut
from .auth import read_bearer_token, JWT_SECRET, JWT_ALG
from jose import jwt, JWTError

router = APIRouter(prefix="/api/garage", tags=["Garage"])

def get_current_user_id(authorization: str | None = Header(default=None)) -> int:
    token = read_bearer_token(authorization)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid subject")
    return int(user_id)

@router.get("", response_model=list[GarageOut])
def get_garage(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    items = db.query(SavedComparison).filter(SavedComparison.user_id == user_id).order_by(SavedComparison.created_at.desc()).all()
    valid_items = []
    
    for item in items:
        try:
            ids = [int(v_id.strip()) for v_id in str(item.vehicle_ids).split(",") if v_id.strip()]
            if not ids:
                continue
                
            vehicles = db.query(Vehicle).filter(Vehicle.id.in_(ids)).all()
            if len(vehicles) == 0:
                # None of the vehicles in this comparison exist anymore; prune it.
                db.delete(item)
            else:
                valid_items.append(item)
        except Exception:
            pass
            
    db.commit()
    return valid_items

@router.post("", response_model=GarageOut)
def save_to_garage(req: GarageSaveRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    # Check if duplicate exists for exactly the same string (e.g. "12")
    existing = db.query(SavedComparison).filter(
        SavedComparison.user_id == user_id, 
        SavedComparison.vehicle_ids == req.vehicle_ids
    ).first()
    
    if existing:
        return existing
        
    new_save = SavedComparison(
        user_id=user_id,
        vehicle_ids=req.vehicle_ids,
        name=req.name
    )
    db.add(new_save)
    db.commit()
    db.refresh(new_save)
    return new_save

@router.delete("/{save_id}")
def delete_from_garage(save_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    item = db.query(SavedComparison).filter(SavedComparison.id == save_id, SavedComparison.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Saved item not found")
    db.delete(item)
    db.commit()
    return {"success": True}
