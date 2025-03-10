FROM python:3.11-slim-bookworm

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install --upgrade uv
COPY requirements.txt requirements.txt
RUN uv pip install -r requirements.txt --system
COPY . .
RUN pip install -e ./

EXPOSE 8000

CMD ["python", "src/app.py"]
