from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId
from typing import Optional
from database import metrics_collection

app = FastAPI(title="Industrial Power Quality Compliance Engine")

# Enable Cross-Origin Resource Sharing (CORS) for your Streamlit UI
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# 1. Pydantic Input Schema for Data Validation (Used for POST and PUT requests)
class MetricInput(BaseModel):
    timestamp: Optional[str] = "2026-05-25 12:00:00" # Defaults to current timeline environment context
    voltage_LL: float
    voltage_unbalance: float
    current_unbalance: float
    frequency: float
    power_factor: float
    voltage_THD: float
    current_TDD: float
    rms_voltage_pu: float
    flicker_Pst: float


# 2. Database Utility Formatter
def format_metric(item) -> dict:
    return {
        "id": str(item["_id"]),
        "timestamp": item.get("timestamp"),
        "voltage_LL": item.get("voltage_LL"),
        "voltage_unbalance": item.get("voltage_unbalance"),
        "current_unbalance": item.get("current_unbalance"),
        "frequency": item.get("frequency"),
        "power_factor": item.get("power_factor"),
        "voltage_THD": item.get("voltage_THD"),
        "current_TDD": item.get("current_TDD"),
        "rms_voltage_pu": item.get("rms_voltage_pu"),
        "flicker_Pst": item.get("flicker_Pst")
    }


# 3. Core Electrical Compliance Logic (10-Point Evaluation Rules Engine)
def run_compliance_check(data: dict) -> tuple:
    status_str = "Compliant"
    violations = []
    
    # Rule 1: 3-Phase Voltage Limits (IS 12360 / IEC 60038)
    if data["voltage_LL"] < 373.5 or data["voltage_LL"] > 456.5:
        status_str = "Violation"
        violations.append(f"Voltage out of tolerance: {data['voltage_LL']}V (IS 12360 +/-10% limit)")

    # Rule 2: Voltage Unbalance Compliance (IEC 61000-2-2 / IEEE 1159)
    if data["voltage_unbalance"] > 3.0:
        status_str = "Violation"
        violations.append(f"Voltage Unbalance high: {data['voltage_unbalance']}% (Preferred <=2%, Critical >3%)")
        
    # Rule 3: Current Unbalance Compliance (NEMA / IEEE Practice)
    if data["current_unbalance"] > 20.0:
        status_str = "Violation"
        violations.append(f"Critical Current Unbalance: {data['current_unbalance']}% (Motor Diagnostics Danger)")
    elif data["current_unbalance"] > 10.0:
        status_str = "Violation"
        violations.append(f"Current Unbalance Alert: {data['current_unbalance']}% (Exceeded NEMA 10% threshold)")

    # Rule 4: Frequency Code Compliance (Indian Electricity Grid Code / CERC)
    if data["frequency"] < 49.90 or data["frequency"] > 50.05:
        status_str = "Violation"
        violations.append(f"India Grid Band Deviation: {data['frequency']} Hz (IEGC Limit: 49.90-50.05Hz)")

    # Rule 5: Power Factor Compliance (CEA Tariff / Utility Regulations)
    if data["power_factor"] < 0.95:
        status_str = "Violation"
        violations.append(f"Low Power Factor: {data['power_factor']} (CEA Tariff Penalty Lag Limit <0.95)")

    # Rule 6: Voltage THD Compliance (IEEE 519 / IEC 61000)
    if data["voltage_THD"] > 5.0:
        status_str = "Violation"
        violations.append(f"Voltage THD breached: {data['voltage_THD']}% (IEEE 519 Capped Limit: 5.0%)")

    # Rule 7: Current TDD Harmonic Compliance (IEEE 519)
    if data["current_TDD"] > 12.0:
        status_str = "Violation"
        violations.append(f"Load Current Harmonic TDD High: {data['current_TDD']}% (IEEE 519 Limit violation)")

    # Rules 8 & 9: Voltage Sag & Swell Detection (IEEE 1159 Standards)
    if 0.1 <= data["rms_voltage_pu"] <= 0.9:
        status_str = "Violation"
        violations.append(f"Voltage Sag Event: {data['rms_voltage_pu']} pu (IEEE 1159 drop profile)")
    elif 1.1 <= data["rms_voltage_pu"] <= 1.8:
        status_str = "Violation"
        violations.append(f"Voltage Swell Event: {data['rms_voltage_pu']} pu (IEEE 1159 surge profile)")

    # Rule 10: Flicker Evaluation (IEC 61000-4-15)
    if data["flicker_Pst"] > 1.0:
        status_str = "Violation"
        violations.append(f"Short-Term Flicker (Pst) Breached: {data['flicker_Pst']} (IEC 61000 limit <= 1.0)")
        
    return status_str, violations


# ==========================================
#               CRUD ENDPOINTS
# ==========================================

# 📥 [POST] - Create a brand new substation log entry
@app.post("/api/metrics/add", status_code=status.HTTP_201_CREATED)
async def create_grid_metric(incoming_data: MetricInput):
    try:
        new_log = incoming_data.model_dump()
        
        # Process data through rules engine prior to insertion
        log_status, log_violations = run_compliance_check(new_log)
        
        # Add evaluation metadata straight into the document schema
        new_log["status"] = log_status
        new_log["violations"] = log_violations
        
        # Insert document into MongoDB Atlas
        result = await metrics_collection.insert_one(new_log)
        
        return {
            "status": "Success",
            "message": "New grid logging document created successfully",
            "inserted_id": str(result.inserted_id),
            "compliance_state": log_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Write Failure: {str(e)}")


# 📤 [GET] - Fetch and evaluate all log records
@app.get("/api/metrics/check")
async def evaluate_grid_compliance():
    try:
        raw_logs = []
        async for log in metrics_collection.find():
            raw_logs.append(format_metric(log))
            
        report = []
        for row in raw_logs:
            status_str, violations = run_compliance_check(row)
            report.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "metrics": row,
                "status": status_str,
                "violations": violations
            })
            
        return {"total_records": len(report), "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✏️ [PUT] - Modify an existing telemetry record by its ID string
@app.put("/api/metrics/update/{record_id}")
async def update_grid_metric(record_id: str, incoming_update: MetricInput):
    if not ObjectId.is_valid(record_id):
        raise HTTPException(status_code=400, detail="The provided MongoDB Hexadecimal ID structure is invalid.")
        
    try:
        mongo_id = ObjectId(record_id)
        updated_fields = incoming_update.model_dump()
        
        # Re-run evaluation metrics calculations over updated parameters
        new_status, new_violations = run_compliance_check(updated_fields)
        
        db_payload = {
            "timestamp": updated_fields["timestamp"],
            "voltage_LL": updated_fields["voltage_LL"],
            "voltage_unbalance": updated_fields["voltage_unbalance"],
            "current_unbalance": updated_fields["current_unbalance"],
            "frequency": updated_fields["frequency"],
            "power_factor": updated_fields["power_factor"],
            "voltage_THD": updated_fields["voltage_THD"],
            "current_TDD": updated_fields["current_TDD"],
            "rms_voltage_pu": updated_fields["rms_voltage_pu"],
            "flicker_Pst": updated_fields["flicker_Pst"],
            "status": new_status,
            "violations": new_violations
        }
        
        result = await metrics_collection.update_one(
            {"_id": mongo_id},
            {"$set": db_payload}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Grid metric document not found with that matching ID")
            
        return {
            "status": "Success",
            "message": "Substation record updated successfully",
            "new_compliance_state": new_status,
            "logged_violations": new_violations
        }
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ❌ [DELETE] - Erase a specific record out of your database completely
@app.delete("/api/metrics/delete/{record_id}")
async def delete_grid_metric(record_id: str):
    if not ObjectId.is_valid(record_id):
        raise HTTPException(status_code=400, detail="The provided MongoDB Hexadecimal ID structure is invalid.")
        
    try:
        mongo_id = ObjectId(record_id)
        result = await metrics_collection.delete_one({"_id": mongo_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Erase Target Rejected: Document ID not found.")
            
        return {
            "status": "Success",
            "message": f"Telemetry log with ID {record_id} successfully deleted from grid records."
        }
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 6. Safe Local Boot Routine Configuration Block
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


    