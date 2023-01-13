# super-sast

A docker image that can even be used in jenkins
with different static analysis tools, including:

- pre-commit
- tox
- trivy
- maven
- openpolicyagent conftest
- owasp dependency check
- spotless + google-java-format

## Usage

You can run this image with the following command:

```bash
docker run -v $PWD:/code -e M2_HOME=/code -e HOME=/code -w /code ghcr.io/par-tec/super-sast:latest
```

See [docs](docs/README.md) for more information on how to use this image in docker-compose or in [devspace](https://devspace.sh).


## Contributing

This project uses [pre-commit](https://pre-commit.com/) to manage git hooks. To install the hooks, run:

```bash
pre-commit install
```

Pre-commit will generate a CycloneDX SBOM using trivy.

To test the image, run:

```bash
docker-compose up --build test
```

To test the remote image (latest), run:

```bash
docker-compose up --build test-latest
```

## Building

To speed up building, use

```
DOCKER_BUILDKIT=1 docker build . -t super-sast
```


## Running

You can enable/disable specific tools setting to false the following
environment variables.

Environment variables:

|Variable|Default|Tool|
|--------|-------|----|
|RUN_TRIVY_CONFIG|true|trivy_config|
|TRIVY_CONFIG_CONFIG_FILE|/app/config/trivy.yaml|trivy_config|
|RUN_TRIVY_FILESYSTEM|true|trivy_filesystem|
|TRIVY_FILESYSTEM_CONFIG_FILE|/app/config/trivy.yaml|trivy_filesystem|
|RUN_BANDIT|true|bandit|
|BANDIT_CONFIG_FILE|/app/config/bandit.yaml|bandit|
|RUN_SAFETY|true|safety|
|SAFETY_CONFIG_FILE|/app/config/safety.yaml|safety|
|RUN_KUBESCAPE|true|kubescape|
|KUBESCAPE_ARGS|--cache-dir /tmp|kubescape|
|RUN_CHECKOV|true|checkov|
|CHECKOV_CONFIG_FILE|/app/config/.checkov.yaml|checkov|
|RUN_SEMGREP|true|semgrep|
|SEMGREP_CONFIG_FILE|auto|semgrep|
|RUN_SPOTBUGS|true|spotbugs|
|RUN_OWASP_DEPENDENCY_CHECK|true|owasp_dependency_check|
|RUN_SPOTLESS_CHECK|true|spotless_check|
|RUN_SPOTLESS_APPLY|false|spotless_apply|
