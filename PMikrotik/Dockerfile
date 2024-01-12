FROM python:3.10.13-bookworm
ENV APP /app
RUN mkdir $APP
WORKDIR $APP
COPY requirements.txt .
RUN pip install pip
RUN pip install -r requirements.txt
COPY . .
#CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "run:app"]
CMD [ "flask","run","--host=0.0.0.0"]