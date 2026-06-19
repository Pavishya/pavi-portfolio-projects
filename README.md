# Pavishya Janakiraman — Data Analyst Portfolio Projects

**Portfolio website:** https://pavishya.netlify.app  
**LinkedIn:** https://www.linkedin.com/in/pavishya  
**Email:** j.pavishya@gmail.com

---

This repository contains three end-to-end analytics projects demonstrating depth in SQL, Python, Power BI, Tableau, and test automation.

| Project | Domain | Tools |
|---|---|---|
| [project-1-healthcare-readmission](./project-1-healthcare-readmission) | Healthcare | SQL · Python · Tableau |
| [project-2-maternal-health-dashboard](./project-2-maternal-health-dashboard) | Maternal & Perinatal Health | PostgreSQL · Power BI · DAX |
| [project-3-data-quality-automation](./project-3-data-quality-automation) | QA / Testing | Python · pytest |

---

## Quick Start

```bash
# Install Python dependencies
pip install pandas numpy matplotlib seaborn scipy scikit-learn faker jupyter pytest pytest-html

# Project 1 — Healthcare
cd project-1-healthcare-readmission
# Download UCI dataset to data/diabetic_readmission.csv first
jupyter notebook python/01_eda.ipynb

# Project 2 — Maternal Health (in progress)
cd project-2-maternal-health-dashboard
# See README for ETL pipeline, data model, and sprint roadmap

# Project 3 — Tests
cd project-3-data-quality-automation
pytest tests/ --html=reports/test_report.html --self-contained-html -v
open reports/test_report.html
```
