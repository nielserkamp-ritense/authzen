# syntax=docker/dockerfile:1

# Build context is the repository root (see docker/docker-compose.yaml), so both
# gzac/ and the valtimo/ submodule used by the composite build are available.
# gzac/Dockerfile.dockerignore limits the context to what the build needs.

FROM eclipse-temurin:21-jdk-noble AS build

WORKDIR /src
COPY valtimo ./valtimo
COPY gzac ./gzac

WORKDIR /src/gzac
RUN --mount=type=cache,target=/root/.gradle \
    ./gradlew bootWar --no-daemon

FROM eclipse-temurin:21-jre-noble

COPY --from=build /src/gzac/build/libs/gzac-*.war /app.war

ENTRYPOINT ["java", "-jar", "/app.war"]
