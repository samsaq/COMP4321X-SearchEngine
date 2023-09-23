FROM python:3.8.10

# Copy the current directory to the container root (including the requirements.txt file)
COPY . /

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN sudo apt-get install nginx -y
RUN sudo ln -s /etc/nginx/sites-available/search-engine-api.conf /etc/nginx/sites-enabled/
RUN sudo apt install snapd -y
RUN sudo snap install --classic certbot
RUN sudo ln -s /snap/bin/certbot /usr/bin/certbot
RUN reboot
RUN sudo systemctl start nginx

EXPOSE 8080

CMD ["gunicorn","--config", "gunicorn_config.py", "justSearch:app"]