FROM us-central1-docker.pkg.dev/ivf-agent/ivf-advisor/base:latest

WORKDIR /app

COPY pyproject.toml .
COPY ivf_advisor/ ivf_advisor/

# Install the package properly (non-editable so it's found as a real package)
RUN pip install --no-cache-dir "google-cloud-firestore>=2.16.0" "psycopg2-binary>=2.9.0" \
    "pydantic==2.10.6" "python-dotenv" && \
    pip install --no-cache-dir --no-deps .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "ivf_advisor.ui"]
