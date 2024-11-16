FROM python:3.12

EXPOSE 5000

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY . /app/

ENV PYTHONUNBUFFERED=true

CMD [ "fastapi", "dev", "--port", "5000", "--host", "0.0.0.0" ]