FROM us-central1-docker.pkg.dev/ivf-agent/ivf-advisor/base:latest

WORKDIR /app

COPY pyproject.toml .
COPY ivf_advisor/ ivf_advisor/

RUN pip install --no-cache-dir "gradio==5.7.1" "pydantic==2.10.6" "python-dotenv" && \
    pip install --no-cache-dir -e . --no-deps

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "ivf_advisor.ui"]
