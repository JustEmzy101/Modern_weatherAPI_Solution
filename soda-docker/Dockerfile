FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    soda-core==3.3.3 \
    soda-core-postgres==3.3.3

WORKDIR /app/soda

RUN soda --version

CMD ["soda", "--help"]