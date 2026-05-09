# Swipe Signals - Streamlit App

I use Streamlit to create a simple app for predicting dating app engagement quality using a local-trained Auto-sklearn model.

Actually, can ignore most of the file.
Important one is the `app.py` this is our main file.
And also the data preprocessing logic it lies in '/scipts/recreate_preprocessors.py'
Others actually not that important, maybe after that you guys can do one more file for UI styling for our app. Maybe using Tailwind CSS to make it looks better, cuz now I do frontend and backend both in streamlit app. 

## 1) Prerequisites

- Docker Desktop installed and running
- Git installed

## 2) Clone The Project

```bash
git clone https://github.com/LOWGUANHOONG/machine-learning-dating-app-behavior-predictor.git
cd "ML autosklearn"
```

## 3) Build Docker Image
From the project root folder:
```bash
docker build -t streamlit-app .
```

## 4) Run the app
Double-click `start_app.bat`
Then, open your browser and type [http://localhost:8501](http://localhost:8501)