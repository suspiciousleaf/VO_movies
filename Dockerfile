FROM python:3.12.3

# Set working directory
WORKDIR /app

# Install dependencies
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the files to the directory
COPY . /app

# Expose port 8000
EXPOSE 8000

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]