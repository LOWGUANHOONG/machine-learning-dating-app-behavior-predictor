# Swipe Signals - Streamlit App

I use Streamlit to create a simple app for predicting dating app engagement quality using a local-trained Auto-sklearn model.

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