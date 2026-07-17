# Docker Compose Logging Hardening (Phase 6)

Add the following `logging` block under each service definition in docker-compose.yml:

```yaml
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Apply to: api, mqtt, redis, postgres, worker services.
