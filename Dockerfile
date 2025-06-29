# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Ensure pip is up-to-date (good practice)
RUN pip install --no-cache-dir --upgrade pip

# Install uv. We will use uv to install the project dependencies.
# We explicitly install it globally to avoid issues with virtual environments in this context.
RUN pip install --no-cache-dir uv

# Copy only the dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install project dependencies using uv.
# By default, uv sync will install into the current environment if no virtual environment is active.
# Since we didn't activate or create one, it will install globally.
RUN uv sync

# Copy the rest of your application code
COPY . .

# Expose the port your server will listen on
# Smithery will inject the PORT environment variable
ENV PORT=8080
EXPOSE $PORT

# Command to run the application
# We use uvicorn to serve the FastMCP application
CMD ["uvicorn", "main:mcp", "--host", "0.0.0.0", "--port", "8080"]