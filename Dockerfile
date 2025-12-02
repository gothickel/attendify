FROM python:3.11-slim


# Install ffmpeg and system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
ffmpeg \
libgl1 \
&& rm -rf /var/lib/apt/lists/*


WORKDIR /app


# Copy only what's needed
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


COPY main.py ./


ENV PORT=8000
EXPOSE 8000


# Use gunicorn in production
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "3", "--timeout", "0"]
