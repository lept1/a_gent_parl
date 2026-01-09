FROM python:3.12

COPY data/ usr/data/

WORKDIR /usr/src

COPY src/weekly_nerd_curiosities/main.py .
COPY src/utilities/ /utilities
COPY src/conf /conf
COPY src/weekly_nerd_curiosities/requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./main.py" ]