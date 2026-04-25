FROM python:3.11-slim

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir "google-adk==1.27.5" "google-cloud-firestore>=2.16.0" "psycopg2-binary>=2.9.0" && \
    pip install --no-cache-dir --force-reinstall "gradio==5.7.1" "pydantic==2.10.6" "python-dotenv" "httpx>=0.24.1" "google-api-python-client>=2.0" "google-auth>=2.0" && \
    find /usr/local/lib/python3.11/site-packages/google -maxdepth 1 -name "__init__.py" -delete 2>/dev/null || true

WORKDIR /app

COPY pyproject.toml .
COPY ivf_advisor/ ivf_advisor/

# Non-editable install so ivf_advisor package is found in site-packages
RUN pip install --no-cache-dir --no-deps .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "ivf_advisor.ui"]
