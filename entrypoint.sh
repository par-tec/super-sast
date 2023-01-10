#!/bin/sh
#
# By default, run /usr/local/bin/jenkins-agent
#
export MAVEN_OPTS="-Duser.home=/tmp"
export USER=nobody

run_talisman() {
    talisman -s || \
        cat talisman_report/talisman_reports/data/report.json
}

run_trivy() {
    trivy config .
}

run_kubescape() {
    kubescape scan .
}

run_owasp_dependency_check() {
    # Reuse downloaded maven dependencies from the image.
    test -d /tmp/.m2 || cp -r /app/java-validators/.m2 /tmp/
    mvn org.owasp:dependency-check-maven:check
}

run_spotbugs() {
    mvn com.github.spotbugs:spotbugs-maven-plugin:check
}

run_spotbugs
run_owasp_dependency_check
run_trivy
run_kubescape
# run_talisman
# pre-commit run -a
