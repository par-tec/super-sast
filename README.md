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

Use this image as a template in jenkins.


## Contributing

This project uses [pre-commit](https://pre-commit.com/) to manage git hooks. To install the hooks, run:

```bash
pre-commit install
```

Pre-commit will generate a CycloneDX SBOM using trivy.

## Building

To speed up building, use

```
DOCKER_BUILDKIT=1 docker build . -t super-sast
```


## Running

You can enable/disable specific tools setting to false the following
environment variables.

- CHECK_SPOTBUGS=true
- CHECK_OWASP_DEPENDENCY_CHECK=true
- CHECK_TRIVY=true
- CHECK_SPOTLESS=true
- CHECK_SPOTLESS_GOAL=check (or apply)
- CHECK_CONFTEST=true
- CHECK_KUBESCAPE=true
- CHECK_TALISMAN=true
