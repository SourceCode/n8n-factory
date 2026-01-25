FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY templates/ templates/
COPY README.md .

RUN pip install --no-cache-dir .

ENTRYPOINT ["n8n-factory"]
CMD ["--help"]
