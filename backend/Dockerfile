FROM python:3.11-slim
WORKDIR /app
COPY requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/base.txt
COPY app /app/app
RUN useradd -m app && chown -R app /app
USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
