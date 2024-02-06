# Usage: docker run -e ADDRESS=<internal-address> -p 8000:8000 -v /var/run/docker.sock:/var/run/docker.sock nuclio-fusionizer-server
FROM python:3.12

# Set working directory in container to /app
WORKDIR /app

# Copy dependency and src contents into the container at /app
COPY ./nuclio_fusionizer ./nuclio_fusionizer
COPY ./requirements.txt .

# Install docker cli
RUN apt-get update && apt-get install -y docker.io
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Install nuctl
RUN curl -s https://api.github.com/repos/nuclio/nuclio/releases/latest \
	| grep -i "browser_download_url.*nuctl.*$(uname)" \
	| cut -d : -f 2,3 \
	| tr -d \" \
	| wget -O nuctl -qi - && chmod +x nuctl
RUN mv nuctl /bin/

ENV PYTHONPATH /app/nuclio_fusionizer:$PYTHONPATH
COPY ./deployment/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/bin/bash", "/entrypoint.sh" ]
