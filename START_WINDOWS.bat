@echo off
setlocal
echo Installing ParcelPilot dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)
echo Starting ParcelPilot...
streamlit run app.py
