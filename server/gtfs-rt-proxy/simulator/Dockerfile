FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY generate.py server.py patterns.json ./

EXPOSE 9000

CMD ["python", "-u", "server.py"]
