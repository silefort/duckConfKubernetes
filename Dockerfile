FROM python:3.12-slim
WORKDIR /app
COPY app/server.py .
EXPOSE 8080/tcp
EXPOSE 5000/udp
CMD ["python", "server.py"]
