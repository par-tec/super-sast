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

You can build a ppc64le image on a linux host using
the  [multiarch/qemu-user-static](https://github.com/multiarch/qemu-user-static) image.
Beware that this image executes as root a script
that registers below kind of /proc/sys/fs/binfmt_misc/qemu-$arch files for all supported processors except the current one in it when running the container (e.g. see `ls -la /proc/sys/fs/binfmt_misc/qemu-*` on your host).
For further information, see the original repo.

```bash
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

**Note**: ppc64le does not support all the tools.

## Running

You can enable/disable specific tools setting to false the following
environment variables.

Environment variables:

- General variables

|Variable|Default|Tool|
|--------|-------|----|
|RUN_ALL_TOOLS|true|Run all available tools. Set it to false to selectively enable single tools.|
|MAVEN_ARGS| |Pass extra arguments to maven3 checks, e.g. `-ntp` to skip logging dependency downloads.|

- Tools variables

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
|SPOTBUGS_CONFIG_FILE||spotbugs. Set this to a file in the current repository, e.g. /code/spotbugs-exclude.xml|
|RUN_OWASP_DEPENDENCY_CHECK|true|owasp_dependency_check|
|RUN_SPOTLESS_CHECK|true|spotless_check|
|RUN_SPOTLESS_APPLY|false|spotless_apply|
