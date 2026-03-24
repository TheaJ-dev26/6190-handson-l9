FROM python:3.10-slim

WORKDIR /app
COPY data_generator.py /app
RUN pip install faker

CMD ["python", "data_generator.py"]
