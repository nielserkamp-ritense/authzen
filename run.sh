cd gzac
./gradlew build

cd ../docker
docker compose --profile gzac up --build
