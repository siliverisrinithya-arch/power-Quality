import asyncio
from datetime import datetime
from database import metrics_collection

async def seed_data():
    await metrics_collection.delete_many({})
    
    # 3 Sample states representing complete health profiles matching your document table
    sample_data = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "voltage_LL": 415.0,           # Nominal 415V
            "voltage_unbalance": 1.1,      # Compliant (<=2%)
            "current_unbalance": 7.5,      # Compliant (<10%)
            "frequency": 50.01,            # Compliant (49.90 - 50.05 Hz)
            "power_factor": 0.98,          # Compliant (>=0.95 target)
            "voltage_THD": 3.2,            # Compliant (<=5%)
            "current_TDD": 4.5,            # Compliant (Based on IEEE 519 limits)
            "rms_voltage_pu": 1.0,         # Normal voltage profile (No Sag / Swell)
            "flicker_Pst": 0.65            # Compliant (<=1.0 short term limit)
        },
        {
            "timestamp": datetime.utcnow().isoformat(),
            "voltage_LL": 352.0,           # VIOLATION: Beyond -10% nominal drop
            "voltage_unbalance": 3.4,      # VIOLATION: High phase asymmetry (>3%)
            "current_unbalance": 22.5,     # VIOLATION: Critical motor damage risk (>20%)
            "frequency": 50.02,            
            "power_factor": 0.89,          # VIOLATION: Low PF triggering DISCOM penalty (<0.95)
            "voltage_THD": 4.1,            
            "current_TDD": 11.2,           
            "rms_voltage_pu": 0.65,         # VIOLATION: Voltage Sag detected (0.1 - 0.9 pu)
            "flicker_Pst": 0.82            
        },
        {
            "timestamp": datetime.utcnow().isoformat(),
            "voltage_LL": 485.0,           # VIOLATION: Over-voltage beyond +10% nominal
            "voltage_unbalance": 1.5,      
            "current_unbalance": 12.1,     # ALERT: Exceeded preferred 10% line
            "frequency": 49.82,            # VIOLATION: Dropped below India Grid Band limit (<49.90 Hz)
            "power_factor": 0.96,          
            "voltage_THD": 7.4,            # VIOLATION: Breached waveform purity (>5% IEEE 519 limit)
            "current_TDD": 16.8,           # VIOLATION: Excess harmonic distortion injected into system
            "rms_voltage_pu": 1.45,         # VIOLATION: Voltage Swell detected (1.1 - 1.8 pu)
            "flicker_Pst": 1.35            # VIOLATION: Short term flash limit breached (>1.0)
        }
    ]
    await metrics_collection.insert_many(sample_data)
    print("🚀 Success! All 10 table parameters are successfully pushed to MongoDB!")

if __name__ == "__main__":
    asyncio.run(seed_data())