FROM python:3.8-slim

WORKDIR /usr/src/app

# Install Poetry
RUN apt-get -qq update && apt-get install -qq curl > /dev/null
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* ./

# Allow install dependencies
RUN poetry install --no-root --no-dev

COPY ./src ./src/

ENTRYPOINT ["python", "src/runner.py"]
