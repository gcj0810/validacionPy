FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Asegúrate de que todos los archivos se copien al contenedor
COPY . .

CMD ["python", "app.py"]
