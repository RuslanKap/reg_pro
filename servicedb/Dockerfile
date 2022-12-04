FROM python:3.10
RUN apt-get update && apt-get install python3-pip -y && pip install --upgrade pip && pip install pipenv
RUN mkdir -p /servicedb/
WORKDIR /servicedb/
COPY . /servicedb/
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]