# Civic Complaint Prioritizer

An end-to-end data-science engineering dashboard that helps municipal teams identify ward-level grievance backlogs and prioritize civic issues from complaint data.

## Why this project matters

City teams receive thousands of issues involving roads, waste, water, electrical infrastructure, and streetlights. Raw CSV files make it difficult to identify the largest unresolved backlogs. This project cleans complaint records, standardizes public-data schemas, and produces an interactive action dashboard.

## Features

- Upload a complaint CSV and validate required fields.
- Automatically convert public BBMP Bengaluru grievance data into the app's standard schema.
- Analyze report volume by category and area/ward.
- Identify the top 10 wards with the highest unresolved grievance backlogs.
- Generate an explainable, downloadable priority queue.
- Flag text-based duplicates only when real complaint narratives are available.

## Data source

The dashboard supports the public [BBMP Bengaluru grievance dataset from OpenCity](https://data.opencity.in/dataset/bbmp-grievances-data). It includes complaint ID, category, sub-category, grievance date, ward name, and grievance status.

The public source does not include original citizen narratives or an official severity field. For BBMP uploads, this project derives severity through transparent category rules and disables duplicate detection. Derived values are **not official BBMP values**.

## Architecture

```text
CSV upload
   ↓
BBMP adapter / standard schema
   ↓
Validation and cleaning pipeline
   ↓
Explainable prioritization and backlog analysis
   ↓
Streamlit dashboard + downloadable action queue
```

## Run locally

```powershell
conda create -n civic-project python=3.12 -y
conda activate civic-project
pip install -r requirements.txt
python generate_sample_data.py
streamlit run app.py
```

To use real data, download a BBMP grievance CSV from the source above and upload it from the dashboard sidebar.

## Priority score

```text
priority = severity × 12 + recent similar reports × 8 + safety signal + age bonus
```

Scores are meant to support human review, not automate public-safety decisions.

## Resume description

> Built an end-to-end Streamlit civic-analytics dashboard that standardizes 200K+ Bengaluru grievance records, identifies ward-level unresolved backlogs, and generates explainable priority queues using Python, Pandas, Plotly, and data-validation pipelines.

## Tech stack

Python, Pandas, Streamlit, Plotly, scikit-learn, CSV data pipelines.

## Future improvements

- Add compatible datasets from more Indian cities.
- Add geographic clustering where source coordinates are available.
- Train and evaluate a text classifier on a labeled narrative dataset.
- Add automated tests, an API, and deployment.
- This project is actively being developed as a civic-tech hackathon prototype.
- hello world
- good day
