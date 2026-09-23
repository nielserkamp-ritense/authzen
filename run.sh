cd valtimo
./gradlew :backend:apps:dev:build

cd ../docker
docker compose --profile gzac up
