# Edstellar LNA Intelligence Platform

A Streamlit web application for Learning Needs Analysis, Strategy Configuration, and LNI/TNI report generation.

## Pages

| Page | Description |
|------|-------------|
| 🏠 Home | Overview and navigation |
| 📂 Upload Data | Upload Employee Master Excel — validates all 17 sheets |
| 📊 LNA / TNA Report | 17-section LNA report with 15 composite indices + AI insights |
| 🎯 Strategy Configuration | Leadership intent configuration — cultural priorities, skill weights, segment focus |
| 📋 LNI / TNI Report | Strategy-aligned 10-section LNI/TNI action report |

## Setup

### Local

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file: `app.py`
5. Deploy

## Input File

Upload an Employee Master Excel file with these 17 sheets:
- CoverPage, Employees, Employee Attrition
- Skills Master, Role Skills, Employee Skills
- Competency Master, Role-Competency Mapping, Employee Competencies
- Training, Certifications
- Projects, Project Skills, Project Competencies, Employee Projects, Employee Tools
- Org_Industry_Benchmark

## AI Insights (Optional)

Powered by [OpenRouter](https://openrouter.ai). Enter your API key in the LNA Report page.
Free models available — no cost required.
