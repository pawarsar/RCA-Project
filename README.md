# 🚀 RCA Intelligence Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_svg)](https://share.streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A premium, Multi-Agent Root Cause Analysis (RCA) system powered by **AutoGen** and **Streamlit**. This engine automates the process of analyzing IT incidents, identifying root causes, and generating actionable mitigation plans through collaborative AI agents.

---

## ✨ Key Features

- **Multi-Agent Collaboration**: Specialized agents for Incident Analysis, Root Cause Identification, Mitigation Planning, and Validation.
- **Interactive UI**: A sleek, dark-themed dashboard built with Streamlit for real-time analysis tracking.
- **Persistent Storage**: All agent reasoning and final reports are stored in a PostgreSQL database.
- **Exportable Reports**: Generate and download professional RCA reports in **Markdown** and **Microsoft Word (.docx)** formats.
- **Automated Validation**: A "Validator" agent ensures the quality and logic of the analysis before finalizing the report.

---

## 🛠️ Tech Stack

- **Framework**: [AutoGen](https://microsoft.github.io/autogen/) (Multi-Agent Orchestration)
- **Frontend**: [Streamlit](https://streamlit.io/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy](https://www.sqlalchemy.org/)
- **LLM**: Azure OpenAI (GPT-4o)
- **Languages**: Python 3.9+

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/rca-intelligence-engine.git
cd rca-intelligence-engine
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory and add your credentials:
```env
# OpenAI Configuration
MODEL=gpt-4o
AZURE_API_KEY=your_azure_api_key
AZURE_API_BASE=your_azure_endpoint
AZURE_API_VERSION=2023-03-15-preview

# PostgreSQL Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/rca_db
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run app.py
```

---

## 🌐 Deployment (Free Resources)

This project is optimized for deployment using free resources:
1. **Database**: [Vercel Postgres](https://vercel.com/storage/postgres) (Free Tier)
2. **App Hosting**: [Streamlit Community Cloud](https://share.streamlit.io/) (Free)

For detailed deployment steps, refer to the [Deployment Plan](./deployment_plan.md).

---

## 📂 Project Structure

```text
├── agents.py          # AutoGen agent definitions and logic
├── app.py             # Streamlit UI and main application flow
├── database.py        # SQLAlchemy models and DB connection
├── init_db.py         # Script to initialize the database schema
├── samples.py         # Pre-defined incident scenarios
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

---

## 🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements.

## 📄 License
This project is licensed under the MIT License.
