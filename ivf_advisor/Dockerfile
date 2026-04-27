FROM python:3.11-slim

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir "google-adk==1.27.5" "google-cloud-firestore>=2.16.0" "psycopg2-binary>=2.9.0" && \
    pip install --no-cache-dir --force-reinstall "gradio==5.7.1" "python-dotenv" "httpx>=0.24.1" "google-api-python-client>=2.0" "google-auth>=2.0" && \
    find /usr/local/lib/python3.11/site-packages/google -maxdepth 1 -name "__init__.py" -delete 2>/dev/null || true

WORKDIR /app

COPY pyproject.toml .
COPY ivf_advisor/ ivf_advisor/

RUN pip install --no-cache-dir --no-deps . && \
    python -c "from ivf_advisor.models import ConversationState; print('ivf_advisor.models OK')" && \
    python -c "
# Patch gradio_client bug: get_type crashes when schema is bool
import gradio_client.utils as u, re
path = u.__file__
with open(path) as f:
    src = f.read()
old = 'def get_type(schema: dict):\n    if \"const\" in schema:'
new = 'def get_type(schema: dict):\n    if not isinstance(schema, dict): return \"any\"\n    if \"const\" in schema:'
if old in src:
    with open(path, 'w') as f:
        f.write(src.replace(old, new))
    print('Patched gradio_client.utils.get_type')
else:
    print('Patch not needed or already applied')
"

# Add /app to PYTHONPATH so ivf_advisor package is always found
ENV PYTHONPATH=/app
ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "ivf_advisor.ui"]
