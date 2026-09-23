# Axiom AI Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server/ .

ENV DECIDE_BACKEND=axiom-fast
EXPOSE 7860 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request, os; port=os.environ.get('PORT', '7860'); urllib.request.urlopen(f'http://localhost:{port}/healthz')"

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
