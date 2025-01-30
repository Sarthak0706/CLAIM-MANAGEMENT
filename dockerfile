# Step 1: Use an official Python runtime as a base image
FROM python:3.9-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the requirements.txt (or equivalent) into the container
COPY requirements.txt /app/

# Step 4: Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the FastAPI app into the container
COPY . /app/

# Step 6: Expose the port the app will run on
EXPOSE 8000

# Step 7: Define the command to run the app (using uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
