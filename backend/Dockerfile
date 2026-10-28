FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# 1 worker + beberapa thread: penguncian rantai audit log berlaku dalam satu proses
CMD ["gunicorn", "-w", "1", "--threads", "8", "-b", "0.0.0.0:5000", "main:app"]
