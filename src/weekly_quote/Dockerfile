FROM python:3.12

WORKDIR /usr/src

COPY src/weekly_quote/main.py .
COPY src/utilities/ src/utilities/
COPY src/weekly_quote/requirement.txt .
COPY data/databases/quote_db.sqlite3 data/databases/

RUN pip install --no-cache-dir -r requirement.txt

CMD [ "python", "./main.py" ]