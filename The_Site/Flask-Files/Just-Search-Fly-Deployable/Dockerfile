FROM python:3.8.10-slim

# Copy the current directory to the container root (including the requirements.txt file)
COPY . /

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8080

CMD ["gunicorn","--config", "gunicorn_config.py", "justSearch:app"]