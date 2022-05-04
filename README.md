# Motion Light Box

This is a project of a movable light box
controlled via Home Assistant and an Arduino based
stepper motor driven motion system.

The project is of personal nature and currently being built.
Parts of it might be still interesting for others.

## Execution via docker-compose

For simplicity the app mostly consisting of a few
FastAPI handlers embedded in Uvicorn is wrapped using Docker
and can be run via docker-compose.

```bash
docker-compose up```

is enough to launch the docker app.

```yaml
version: "3.9"  # optional since v1.27.0
services:
  app:
    environment:
      - API_PORT=8000
      - SERIAL_DEVICE=/dev/ttyACM0
    build: .
    ports:
      - "8000:8000"
    devices:
      - /dev/ttyACM0
```

Changing the behavior of the app api can be done using env variables.

In particular the `HASS_API_TOKEN` and `HASS_DOMAIN` needs to be fed.
`HASS_DOMAIN` could be e.g. "192.168.0.13:8123".

```bash
HASS_API_TOKEN=<HASS LONG TOKEN> HASS_DOMAIN=<HASS DOMAIN AND PORT> docker-compose up -d
```
