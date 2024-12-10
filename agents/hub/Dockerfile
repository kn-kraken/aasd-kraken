FROM python:3.10
RUN pip install spade

WORKDIR /app
COPY . /app

RUN chmod +x main.py
CMD python -u main.py
