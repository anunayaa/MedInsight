@echo off
echo Starting MedInsight in 'ai' Conda environment...
conda run -n ai streamlit run app.py --server.port 8502
pause
