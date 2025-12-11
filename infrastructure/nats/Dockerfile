FROM nats:2.10-alpine

# Copy NATS configuration
COPY nats-server.conf /nats-server.conf

# Expose ports
# 4222: Client connections
# 8222: HTTP monitoring
EXPOSE 4222 8222

# Run NATS with JetStream enabled
CMD ["--config", "/nats-server.conf"]
