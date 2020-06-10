FROM python:3.7.5-slim-stretch

# Create app directory
WORKDIR /opt/panic_oasis

# Install app dependencies
COPY Pipfile* ./

RUN pip install pipenv
RUN pipenv sync

# Bundle app source
COPY . .

CMD [ "pipenv", "run", "python", "run_alerter.py" ]
