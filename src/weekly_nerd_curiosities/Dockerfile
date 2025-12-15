FROM python:3.12

WORKDIR /usr/src

COPY src/weekly_nerd_curiosities/main.py .
COPY src/utilities/ src/utilities/
COPY src/weekly_nerd_curiosities/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./main.py" ]