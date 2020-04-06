# BEGIN: BUILD IMAGE
FROM python:3.8-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PATH="/venv/bin:$PATH"

# Install a few essentials and clean apt caches afterwards.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        apt-transport-https build-essential curl git libpq-dev \
        postgresql-client libffi-dev  && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN python -m venv /venv
WORKDIR /app

# We copy the pip requirements first to leverage Docker caching.
COPY ./requirements.txt /app/
RUN pip install -U pip \
    && pip install --no-cache-dir -r requirements.txt
# END: BUILD IMAGE

# BEGIN: FINAL IMAGE
FROM python:3.8-slim AS final
WORKDIR /app
ENV PATH="/venv/bin:$PATH"
COPY --from=backend /venv/ /venv/
COPY ./probe_search probe_search

CMD ["python", "-m", "probe_search.import"]
# END: FINAL IMAGE
