Factory Automation System

A Python-based office and management automation prototype designed to help manufacturing companies register, track, and analyze internal requests.

Features

- Management dashboard with request metrics and interactive charts
- Request registration with department, category, priority, and due date
- Rule-based priority suggestions using text keywords
- Request filtering and status updates
- Follow-up notes and request status history
- Overdue request detection
- Filterable reports by date, department, and status
- CSV and Excel report exports
- SQLite database for persistent data storage

Tech Stack

- Python
- Streamlit
- SQLite
- Pandas
- Plotly
- OpenPyXL

Installation

1. Clone or download this repository.

2. Create and activate a Python virtual environment.

3. Install dependencies:
   
   pip install -r requirements.txt

4. Run the application:
   
   python -m streamlit run app.py

The SQLite database is created automatically in the "data" directory.

Project Structure

Factory_Automation/
├── app.py
├── database.py
├── README.md

Business Value

The system provides a centralized way to record internal requests, monitor their progress, identify overdue tasks, and produce operational reports. It can serve as a foundation for improving administrative coordination and management visibility in a manufacturing environment.

Limitations and Future Improvements

- The priority suggestion mechanism uses simple keyword rules, not a trained AI model.
- User authentication and role-based access control are not implemented.
- Approval workflows and automatic notifications are not yet available.
- Integration with ERP, inventory, or production systems is not implemented.
- Automated tests and production deployment configuration can be added in future versions.

Disclaimer

This is a portfolio and learning project. It has not been validated for production use in a real factory.
