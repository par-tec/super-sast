#
# An all-in-one Dockerfile for running Super-Linter and other
# static analysis tools.
#
# Dependencies
FROM openpolicyagent/conftest:v0.36.0 as conftest
FROM aquasec/trivy:0.35.0 as trivy

# Java builder
FROM maven:3.6.3-openjdk-11 as maven
RUN mkdir /app/java-validators -p
COPY pom.xml /app/java-validators
RUN --mount=type=cache,target=/root/.m2 sh -c '( \
        cd /app/java-validators &&  \
        mvn dependency:copy-dependencies  dependency:resolve-plugins && \
        cp -r /root/.m2 /app/java-validators/)'

# Pin a python version.
FROM python:3.11.1-alpine as base_python

# Python builder.
FROM base_python as build
RUN  apk add --no-cache \
	openjdk11-jre \
	git \
	gcompat \
	build-base \
	libffi-dev \
	rust \
	cargo

RUN pip3 install --upgrade pip
COPY requirements.txt /
RUN --mount=type=cache,target=/root/.cache pip3 install -r /requirements.txt

# Base image
FROM base_python as base_image


# Config vars

RUN apk add --no-cache \
	openjdk11-jre \
        git \
        gcompat

#
# Skip talisman and kubescape for now.
#
#ARG TALISMAN_VERSION=v1.29.4
#ARG TALISMAN_URL=https://github.com/thoughtworks/talisman/releases/download/${TALISMAN_VERSION}/talisman_linux_386
#ARG KUBESCAPE_VERSION=v2.0.180
#ARG KUBESCAPE_URL=https://github.com/kubescape/kubescape/releases/download/${KUBESCAPE_VERSION}/kubescape-ubuntu-latest
COPY ./scripts /app/scripts
# Install talisman.
# RUN . /app/scripts/install_talisman.sh && install_talisman
# Install kubescape.
# RUN . /app/scripts/install_kubescape.sh && install_kubescape

# Install trivy.
COPY --from=trivy /usr/local/bin/trivy /usr/bin/trivy

# Add maven.
RUN mkdir -p /usr/share
COPY --from=maven /usr/share/maven /usr/share/maven
COPY --from=maven /app/java-validators /app/java-validators
RUN ln -s  /usr/share/maven/bin/mvn /usr/bin/mvn

# Install conftest.
COPY --from=conftest /usr/local/bin/conftest /usr/bin/conftest

# Copy python dependencies to speed up
# an expensive pip install.
COPY requirements.txt /app/
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy the rest of the code.
COPY config /app/config/
COPY entrypoint.py /

#
# Default variables.
#
# Dowload maven deps to /tmp/.m2/
ENV M2_HOME=/tmp

# Read-only checks
ENV RUN_ALL_TOOLS=true


# Write checks.
ENV RUN_SPOTLESS_APPLY=false

USER 1000
HEALTHCHECK NONE
ENTRYPOINT ["python", "/entrypoint.py"]
