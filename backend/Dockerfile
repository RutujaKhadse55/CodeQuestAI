# Production image (plan §6 Phase 3 item 7): non-root, optional baked MiniLM, native sandbox inside the container.
# Build from the repo root:  docker build -f backend/Dockerfile -t codequest-backend .
#   --build-arg EXTRAS="ai agents profile_rag"   requirement files to install (default "ai agents"; profile_rag is heavy: torch)
#   --build-arg BAKE_MINILM=1        pre-download sentence-transformers/all-MiniLM-L6-v2 (Agents' memory model)
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 \
    SANDBOX_MODE=native HF_HOME=/opt/hf DATABASE_URL=sqlite:///./data/codequest.db
WORKDIR /srv
COPY requirements/ requirements/
ARG EXTRAS="ai agents"
RUN pip install -r requirements/base.txt && for f in $EXTRAS; do pip install -r requirements/$f.txt; done
ARG BAKE_MINILM=0
RUN if [ "$BAKE_MINILM" = "1" ]; then \
      pip install sentence-transformers && \
      python -c "from sentence_transformers import SentenceTransformer as S; S('sentence-transformers/all-MiniLM-L6-v2')"; \
    fi
COPY backend/app app
RUN useradd --system --uid 10001 --no-create-home app && mkdir -p /srv/data /opt/hf && chown -R app /srv/data /opt/hf
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import os,urllib.request as u; u.urlopen(u.Request('http://127.0.0.1:8000/health', headers={'X-API-Token': os.environ.get('API_TOKEN','change-me')}))"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
