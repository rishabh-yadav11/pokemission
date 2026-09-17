FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Create writable directories for non-root user
RUN mkdir -p /tmp /home/appuser/.cache && chown -R appuser:appuser /app /tmp /home/appuser

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/mission/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]