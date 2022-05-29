## Docker

The entire architecture can be set up in containerized environment using Docker images.
The following instructions do not include the OpenRA game servers, only the web 
servers.

These instructions expect you to know the basics of Docker and the Docker CLI.

### Build

First, you have to build the Docker images. To streamline this process, a shell script 
is packaged with this repository. Run the shell script from the repository root 
directory:

```sh
chmod +x .docker/build.sh
.docker/build.sh
```

The script builds three Docker images:

1. `oraladder/base:latest`, that collects all project files and dependencies
2. `oraladder/ragl:latest`, that initializes the RAGL web server
3. `oraladder/ladder:latest`, that initializes the Ladder web server

### Run

Export the path to your replay directory into the environment variable 
`REPLAY_DIRECTORY`. Then run the RAGL or Ladder web service with the following 
commands:

```sh
docker run --rm --name ragl -dit -p 8000:8000 -v $REPLAY_DIRECTORY:/replays/:ro oraladder/ragl:latest
```

```sh
docker run --rm --name ladder -dit -p 8001:8000 -v $REPLAY_DIRECTORY:/replays/:ro oraladder/ladder:latest
```

NB: These containers will be removed entirely when stopped due to the `--rm` flag.

### Update database

To update the database files, you can use `docker exec` as follows for the 
`ladder` container:

```sh
docker exec -it ladder venv/bin/ora-ladder -d instance/db-ra-all.sqlite3 /replays
```

To update the RAGL container, run

```sh
docker exec -it ragl venv/bin/ora-ragl -d instance/db-ragl.sqlite3 /replays
```
