FROM modelw/base:2025.07

COPY --chown=user back/pyproject.toml back/poetry.lock ./
COPY --chown=user chat_rag /chat_rag

RUN modelw-docker install

COPY --chown=user back/ .

RUN modelw-docker build

CMD ["modelw-docker", "serve"]
