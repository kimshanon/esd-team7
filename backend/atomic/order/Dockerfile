#Dockerfile
FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./order.py .
COPY ../../firebase-adminsdk.json .
EXPOSE 5001
CMD [ "python", "./order.py" ]
