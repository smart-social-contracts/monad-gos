FROM ollama/ollama:latest

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Optional Cloudflare tunnel (same pattern as geister/Dockerfile)
RUN curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb \
    -o /tmp/cloudflared.deb && \
    dpkg -i /tmp/cloudflared.deb && \
    rm /tmp/cloudflared.deb

WORKDIR /app
COPY cloudflared/config.yml /app/cloudflared/config.yml
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 11434
CMD ["/app/start.sh"]
