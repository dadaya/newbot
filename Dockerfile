FROM python:3.10

WORKDIR /app
COPY main.py requirements.txt ./
RUN pip install -r requirements.txt
CMD ["python", "main.py"]