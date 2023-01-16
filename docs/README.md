# Running


## Compose

To run with docker-compose, use the [docker-compose-sample.yaml](docker-compose-sample.yaml)π file.

```bash
docker-compose up super-sast
```

## Red Hat OpenShift Devfile

If you have [odo](https://odo.dev/) installed, you can run the application with the [devfile.yaml](devfile.yaml) file
on an OpenShift cluster.

```bash
odo dev
```

Then access the container via

```
oc logs deployment.apps/super-sast-app
```

## Devspace.sh (not affilated with Red Hat)

To run with `devspace` command

```bash
DEVSPACE_CONFIG=devspace-super-sast.yaml devspace dev
```


## Pipeline

TBD: help welcome :)

## Github Actions

TBD: help welcome :)
