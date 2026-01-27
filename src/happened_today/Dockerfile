FROM python:3.12

WORKDIR /usr/src

COPY main.py .
COPY utilities/ utilities/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


CMD [ "python", "./main.py" ]