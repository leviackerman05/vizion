FROM node:24-bookworm-slim AS web-build
WORKDIR /build
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci --ignore-scripts
COPY apps/web apps/web
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PORT=8000 DATA_DIR=/tmp/vizion PIPER_MODEL=/opt/piper/en_US-ljspeech-high.onnx \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libcairo2-dev libpango1.0-dev pkg-config gcc g++ fonts-dejavu-core espeak-ng \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
RUN python -c "import tomllib; p=tomllib.load(open('pyproject.toml','rb'))['project']; print('\n'.join(p['dependencies'] + p['optional-dependencies']['render']))" > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt
RUN mkdir -p /opt/piper && python -m piper.download_voices --data-dir /opt/piper en_US-ljspeech-high
COPY services/video services/video
RUN pip install --no-deps .
COPY --from=web-build /build/apps/web/dist apps/web/dist
RUN useradd --create-home --uid 10001 vizion && mkdir -p /tmp/vizion && chown vizion:vizion /tmp/vizion
USER vizion
EXPOSE 8000
CMD ["python", "-m", "vizion.entrypoint"]
