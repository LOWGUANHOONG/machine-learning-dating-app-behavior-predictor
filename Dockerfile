FROM mfeurer/auto-sklearn:master
WORKDIR /opt/app

# Copy dependencies and install
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code and saved artifacts into the image so the app
# can run without mounting volumes at runtime.
COPY app.py ./
COPY final_autosklearn_model.pkl ./
COPY deployment_artifacts/ ./deployment_artifacts/

EXPOSE 8501
CMD ["python3", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0"]