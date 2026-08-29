FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose server port
EXPOSE 8000

# Start server daemon with Pond Protocol and web dashboard
CMD ["uvicorn", "yc_launch_monitor.pond.server:app", "--host", "0.0.0.0", "--port", "8000"]
