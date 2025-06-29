# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install uv for efficient dependency management
RUN pip install uv

# Copy only the dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies using uv into the system Python environment
RUN uv sync --system

# Copy the rest of your application code
COPY . .

# Expose the port your server will listen on
# Smithery will inject the PORT environment variable
ENV PORT=8080
EXPOSE $PORT

# Command to run the application
# We use uvicorn to serve the FastMCP application
CMD ["uvicorn", "main:mcp", "--host", "0.0.0.0", "--port", "8080"]