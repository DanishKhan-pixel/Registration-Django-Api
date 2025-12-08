# Django Project Setup on Ubuntu

## Prerequisites
Ensure you have the following installed on your Ubuntu system:
- Python (3.8 or higher)
- pip (Python package manager)
- virtualenv
- Git

## Step 1: Clone the Repository
```bash
git clone git@github.com:Tech-Scrappers/pulsse-authentication.git
cd pulsse-authentication
```

## Step 2: Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Activate the virtual environment
```

## Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 4: Set Up Environment Variables
Copy the example environment file and configure it:
```bash
cp env.example .env
```
Open `.env` and update the required values (such as database credentials, secret keys, etc.).

## Step 5: Apply Migrations
```bash
python manage.py migrate
```

## Step 6: Run the Development Server
```bash
python manage.py runserver
```
The server should now be running at `http://127.0.0.1:8000/`

## Step 7: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## Troubleshooting
- If you get permission errors, try `sudo chmod +x manage.py`
- If dependencies fail to install, ensure `pip` is up to date: `pip install --upgrade pip`
  
---
Your Django project is now set up and running on Ubuntu! 🚀
