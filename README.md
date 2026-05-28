⚡ Power Quality Compliance Engine & Dashboard

An industrial-grade telemetry monitoring platform engineered to audit substation grid stability metrics and track power distribution compliance thresholds. Built utilizing FastAPI for core processing, MongoDB for datalog retention, and Streamlit for multi-channel grid analytics visualizations.
 Execution Guide

Follow these sequential steps in your terminal to run the full stack locally:

 1. Initialize Virtual Environment & Dependencies
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn pymongo pydantic streamlit requests pandas
2. Seed the MongoDB Database Collections
Bash
python seed.py
3. Spin Up the FastAPI Backend Engine
Bash
uvicorn main.py:app --reload
Backend Endpoint URL: http://127.0.0.1:8000/api/metrics/check
4. Run the Streamlit User Interface Layout
Open a separate terminal tab and run:
.\.venv\Scripts\Activate.ps1
streamlit run app_frontend.py
Dashboard URL: http://localhost:8501
