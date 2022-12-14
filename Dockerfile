#
# An all-in-one Dockerfile for running Super-Linter and other
# static analysis tools.
#

# Dependencies
FROM aquasec/trivy:0.35.0 as trivy
FROM jenkins/jnlp-agent-maven as maven
FROM openpolicyagent/conftest:v0.36.0 as conftest

# Base image
FROM jenkins/jnlp-agent-python as base_image


# Add maven
RUN mkdir -p /usr/share
COPY --from=maven /usr/share/maven /usr/share/maven
RUN ln -s  /usr/share/maven/bin/mvn /usr/bin/mvn

COPY --from=conftest /usr/local/bin/conftest /usr/bin/conftest


# Install python deps.
RUN pip3 install tox pre-commit pytest


RUN mkdir /app/java-validators -p
COPY pom.xml /app/java-validators
RUN sh -c '(cd /app/java-validators && mvn package)'


COPY entrypoint.sh /

USER 1000
ENTRYPOINT ["/entrypoint.sh"]
