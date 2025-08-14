FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py /app/
COPY run.sh /app/
RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
