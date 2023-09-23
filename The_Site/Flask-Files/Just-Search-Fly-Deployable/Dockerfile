FROM python:3.8.10

# Copy the current directory to the container root (including the requirements.txt file)
COPY . /

EXPOSE 80
EXPOSE 443
EXPOSE 8080

RUN sudo ufw allow 80
RUN sudo ufw allow 443
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN sudo apt install snapd -y
RUN sudo snap install --classic certbot
RUN sudo ln -s /snap/bin/certbot /usr/bin/certbot
RUN reboot
RUN sudo certbot certonly -d search-engine-api.fly.dev -n — standalone

CMD ["gunicorn","--config", "gunicorn_config.py", "justSearch:app"]