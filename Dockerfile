FROM python:3.14

ENV PYTHONPATH=/app

RUN mkdir /app
WORKDIR /app

COPY . /app
RUN pip install tox -e .'[test]'
CMD python manage.py migrate && python manage.py runserver 0.0.0.0:80
