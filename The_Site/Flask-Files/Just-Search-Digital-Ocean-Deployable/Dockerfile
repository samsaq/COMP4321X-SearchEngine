FROM python:3.8.10

EXPOSE 80
EXPOSE 443

# Copy the current directory to the container root (including the requirements.txt file)
COPY . /

RUN apt-get update
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN apt-get install python3-venv libaugeas0 -y
RUN python3 -m venv /opt/certbot/
RUN /opt/certbot/bin/pip install --upgrade pip
RUN /opt/certbot/bin/pip install certbot certbot
RUN ln -s /opt/certbot/bin/certbot /usr/bin/certbot
RUN certbot certonly -d search-engine-api.fly.dev -n --standalone --agree-tos -m sameereza@gmail.com

CMD ["gunicorn","--config", "gunicorn_config.py", "justSearch:app"]