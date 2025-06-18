# Use Python 3.13.4
FROM python:3.13.4

# Set working directory
WORKDIR /app

# Copy project files into the container
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port
EXPOSE 10000

# Start your app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
