# Nassau Candy Distributor — Product Line Profitability

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project structure
- `app.py` — Streamlit dashboard
- `nassau_candy_cleaned.csv` — validated dataset with derived metrics and factory mapping
- `research_paper.docx` — EDA, findings, methodology and recommendations
- `executive_summary.docx` — management/government-stakeholder summary

## Important data-quality finding
Order dates range from 2024–2025, while ship dates range from 2026–2030. The resulting order-to-ship gaps are 904–1,642 days. Shipment efficiency should therefore not be interpreted from this dataset until the date issue is resolved.

Gross Profit exactly reconciles to Sales − Cost for all rows. No missing values, zero sales, zero units, negative cost, or negative gross profit records were found.
