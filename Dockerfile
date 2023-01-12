#
# An all-in-one Dockerfile for running Super-Linter and other
# static analysis tools.
#

# Dependencies
FROM aquasec/trivy:0.35.0 as trivy
FROM openpolicyagent/conftest:v0.36.0 as conftest
FROM jenkins/jnlp-agent-maven as maven
RUN mkdir /app/java-validators -p
COPY pom.xml /app/java-validators
RUN --mount=type=cache,target=/root/.m2 sh -c '(cd /app/java-validators &&  \
                mvn package && \
                cp -r /root/.m2 /app/java-validators/)'


# Base image
FROM python:alpine as base_image


# Config vars
ARG TOX_VERSION=3.23.1
ARG PYTEST_VERSION=6.2.5
ARG PRE_COMMIT_VERSION=2.15.0
ARG TALISMAN_VERSION=v1.29.4
ARG TALISMAN_URL=https://github.com/thoughtworks/talisman/releases/download/${TALISMAN_VERSION}/talisman_linux_386
ARG KUBESCAPE_VERSION=v2.0.180
ARG KUBESCAPE_URL=https://github.com/kubescape/kubescape/releases/download/${KUBESCAPE_VERSION}/kubescape-ubuntu-latest


RUN apk add --no-cache \
	openjdk11-jre \
        git \
        gcompat

# Install talisman.
RUN wget ${TALISMAN_URL} -O /usr/bin/talisman
RUN chmod +x /usr/bin/talisman

# Install kubescape.
RUN wget ${KUBESCAPE_URL} -O /usr/bin/kubescape && chmod +x /usr/bin/kubescape && kubescape download framework

# Install trivy.
COPY --from=trivy /usr/local/bin/trivy /usr/bin/trivy

# Add maven.
RUN mkdir -p /usr/share
COPY --from=maven /usr/share/maven /usr/share/maven
COPY --from=maven /app/java-validators /app/java-validators
RUN ln -s  /usr/share/maven/bin/mvn /usr/bin/mvn

# Install conftest.
COPY --from=conftest /usr/local/bin/conftest /usr/bin/conftest

# Install python deps.
RUN pip3 install tox==${TOX_VERSION} \
        pre-commit==${PRE_COMMIT_VERSION} \
        pytest==${PYTEST_VERSION}
COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

COPY config /app/config/
COPY entrypoint.py /

#
# Default variables.
#
# Dowload maven deps to /tmp/.m2/
ENV M2_HOME=/tmp

# Read-only checks
ENV RUN_SPOTBUGS=true
ENV RUN_OWASP_DEPENDENCY_CHECK=true
ENV RUN_TRIVY_FILESYSTEM=true
ENV RUN_TRIVY_CONFIG=true
ENV RUN_SPOTLESS_CHECK=true
ENV RUN_CONFTEST=true
ENV RUN_KUBESCAPE=true
ENV RUN_TALISMAN=true

# Write checks.
ENV RUN_SPOTLESS_APPLY=false

USER 1000
HEALTHCHECK NONE
ENTRYPOINT ["python", "/entrypoint.py"]
