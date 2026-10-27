FROM python:3.12-slim
WORKDIR /srv
COPY ml/requirements.txt ml/requirements.txt
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY ml ml
COPY backend backend
WORKDIR /srv/backend
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
