# Usar Python 3.12.4 como base
FROM python:3.12.4-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo de requerimientos
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Variable de entorno para Python
ENV PYTHONUNBUFFERED True

# Establecer las variables de entorno para Gmail
ENV GMAIL_USER=$GMAIL_USER
ENV GMAIL_PASSWORD=$GMAIL_PASSWORD

# Exponer puerto 8080 (el puerto estándar para Cloud Run)
ENV PORT 8080
EXPOSE 8080

# Comando para ejecutar la aplicación Flask con Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app