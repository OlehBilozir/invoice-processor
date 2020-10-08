FROM binyominco/odbc-drivers:1.1

USER root

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

# EXPOSE 8000

# CMD ["gunicorn", "--workers=2", "app:server", "-b 0.0.0.0:8000"]
