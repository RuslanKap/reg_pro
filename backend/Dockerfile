FROM python:3.10
RUN apt-get update && apt-get install python3-pip -y && pip install --upgrade pip && pip install pipenv
RUN mkdir -p /backend/
WORKDIR /backend/
COPY . /backend/
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python3", "main.py"]