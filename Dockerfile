FROM python:3

# Fix ENV format
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only requirements first (better caching)
COPY requirements.txt /app/

# Install dependencies safely
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy rest of the project files
COPY . /app/

EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "0.0.0.0"]
