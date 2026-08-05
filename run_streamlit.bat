@echo off
echo Starting FinPilot AI Streamlit Web Application...
call backend\venv\Scripts\activate.bat
python -m streamlit run app_streamlit.py --server.port 8501 --server.address 127.0.0.1
