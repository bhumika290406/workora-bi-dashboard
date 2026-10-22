# Workora BI Dashboard

Interactive dashboard made with Streamlit + Plotly using the supplied synthetic data bundle.

## Run locally
1. Install Python 3.10+.
2. Open this folder in VS Code.
3. In the VS Code terminal, run:
   ```bash
   python -m venv .venv
   ```
4. Activate the environment:
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
   - If activation is blocked, use Command Prompt: `.venv\Scripts\activate.bat`
5. Install packages: `pip install -r requirements.txt`
6. Start dashboard: `streamlit run app.py`
7. Open the localhost URL shown in terminal.

## Data note
All supplied records are synthetic. The files do not share a common key, so the dashboard analyzes each dataset independently. KPI definitions and cleaning assumptions are documented in the dashboard.
