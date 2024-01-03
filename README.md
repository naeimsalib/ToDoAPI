# ToDoAPI

## Overview
ToDoAPI is a Flask-based REST API designed to manage and track tasks. It provides a suite of features including task creation, updating, deletion, marking tasks as complete, and listing all or completed tasks.

## Features
- User Registration and Authentication
- Task Management (Create, Read, Update, Delete)
- Mark tasks as completed
- View all tasks and completed tasks
- Search functionality for tasks
- Admin privileges to list all users

## Local Setup
Follow these steps to get the ToDoAPI running on your local machine:

### Prerequisites
- Python 3
- pip (Python package manager)

### Installation
1. **Clone the repository:**
```bash
git clone https://github.com/naeimsalib/ToDoAPI.git
cd ToDoAPI
```

2. **Set up a virtual environment (optional but recommended):**
 ```bash
python -m venv venv
source venv/bin/activate # On Windows use venv\Scripts\activate
```


3. **Install dependencies:**
 ```bash
pip install -r requirements.txt
```


4. **Initialize the database:**
- Modify the `app.py` to include `db.create_all()` within an application context, if not already present.
- Run the Flask application once to create the SQLite database.
 app.py

5. **Run the application:**
 ```bash
flask run
```
or
 ```bash
python
```


## Testing
The `Testing.txt` file contains examples of testing commands for various API functionalities. You can use these commands with tools like `curl` or Postman to test the API endpoints.

## Contribution
Feel free to fork the project, submit pull requests, or suggest new features by opening issues.
