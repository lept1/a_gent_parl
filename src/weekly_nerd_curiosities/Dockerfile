FROM python:3.12

WORKDIR /usr/src

COPY src/weekly_nerd_curiosities/main.py .
COPY src/weekly_nerd_curiosities/config.py .
COPY src/weekly_nerd_curiosities/database.py .
COPY src/weekly_nerd_curiosities/__init__.py weekly_nerd_curiosities/__init__.py
COPY src/utilities/ src/utilities/
COPY src/weekly_nerd_curiosities/requirement.txt .

RUN pip install --no-cache-dir -r requirement.txt

CMD [ "python", "./main.py" ]