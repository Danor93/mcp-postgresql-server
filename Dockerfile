FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run tests on container startup - container will fail if tests fail
RUN pip install pytest
CMD ["sh", "-c", "pytest tests/ && python app.py"]