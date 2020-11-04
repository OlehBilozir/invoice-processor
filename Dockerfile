FROM binyominco/odbc-drivers:1.1

USER root

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt
