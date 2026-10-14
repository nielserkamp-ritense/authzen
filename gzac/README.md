# GZAC (backend)

The GZAC backend for the AuthZEN demo, including Valtimo's `authorization-authzen` module.

Valtimo comes from the `../valtimo` submodule through a Gradle composite build (`includeBuild` in `settings.gradle`). It is not downloaded from a Maven repository. To use another checkout, pass `-PvaltimoDir=/path/to/valtimo`.

## How to build

You don't build this project by hand. `../run.sh` builds it inside Docker with the multi-stage `Dockerfile`. The build context is the repository root, limited by `Dockerfile.dockerignore`.

To build only the image:

```bash
docker compose -f ../docker/docker-compose.yaml --profile gzac build gzac-backend
```

The case definition, BPMN, forms, plugin configurations and permissions in `src/main/resources/config/` are deployed automatically when the backend starts.
