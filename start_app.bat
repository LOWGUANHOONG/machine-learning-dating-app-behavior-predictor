@echo off
REM Start Streamlit app in Docker with bind mount for development

echo Starting Streamlit app...
docker run --rm -p 8501:8501 -v "%cd%:/opt/app" streamlit-app

echo.
echo Streamlit app stopped.
echo To restart, run this script again.
pause