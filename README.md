# super-sast

A docker image that can even be used in jenkins
with different static analysis tools, including:

- pre-commit
- tox
- trivy
- maven
- openpolicyagent conftest

## Usage

Use this image as a template in jenkins.


## Contributing

This project uses [pre-commit](https://pre-commit.com/) to manage git hooks. To install the hooks, run:

```bash
pre-commit install
```

Pre-commit will generate a CycloneDX SBOM using trivy.
