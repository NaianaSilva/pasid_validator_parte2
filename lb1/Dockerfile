FROM python:3.11-slim

WORKDIR /app

COPY . .

# Instala dependências do sistema para opencv e pillow
RUN apt-get update && apt-get install -y \
  gcc \
  libgl1-mesa-glx \
  libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
RUN pip install --no-cache-dir \
  numpy \
  opencv-python-headless \
  matplotlib \
  pillow

CMD ["python", "lb1.py"]
