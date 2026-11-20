FROM modelw/base:2026.10

# The widget library is imported from the sibling directory.
COPY --chown=user widget /widget
COPY --chown=user front /front

WORKDIR /front

RUN pnpm install --ignore-scripts

RUN modelw-docker build

CMD ["modelw-docker", "serve"]
