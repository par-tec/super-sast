#!/bin/sh
#
# By default, run /usr/local/bin/jenkins-agent
#
M2_HOME_DEFAULT="/tmp"
M2_HOME="${M2_HOME:-"${M2_HOME_DEFAULT}"}"
export MAVEN_OPTS="${MAVEN_OPTS:-"-Duser.home=${M2_HOME}"}"
export USER=nobody
TRIVY_OPTIONS="  --cache-dir /tmp"

run_talisman() {
    talisman -s || \
        cat talisman_report/talisman_reports/data/report.json
}

run_trivy() {
    trivy ${TRIVY_OPTIONS} config  .
    trivy ${TRIVY_OPTIONS} filesystem --exit-code 1 --severity HIGH,CRITICAL --no-progress .
}

run_kubescape() {
    kubescape --cache-dir /tmp scan .
}

run_owasp_dependency_check() {
    mvn org.owasp:dependency-check-maven:check
}

run_spotbugs() {
    mvn com.github.spotbugs:spotbugs-maven-plugin:check
}

run_spotless() {
    local goal="${1:-"check"}"
    mvn com.diffplug.spotless:spotless-maven-plugin:${goal}
}

init() {
    # shellcheck disable=SC1091
    # Reuse downloaded maven dependencies from the image.
    test -d "${M2_HOME}/.m2" || cp -r /app/java-validators/.m2 "${M2_HOME}"
}

CHECK_SPOTBUGS="${CHECK_SPOTBUGS:-"false"}"
CHECK_OWASP_DEPENDENCY_CHECK="${CHECK_OWASP_DEPENDENCY_CHECK:-"false"}"
CHECK_TRIVY="${CHECK_TRIVY:-"false"}"
CHECK_KUBESCAPE="${CHECK_KUBESCAPE:-"false"}"
CHECK_TALISMAN="${CHECK_TALISMAN:-"false"}"
CHECK_TALISMAN="false"
CHECK_SPOTLESS_GOAL="${CHECK_SPOTLESS_GOAL:-"check"}"

init

[ "${CHECK_SPOTBUGS}" != "false" ] && run_spotbugs
[ "${CHECK_OWASP_DEPENDENCY_CHECK}" != "false" ] && run_owasp_dependency_check
[ "${CHECK_SPOTLESS}" != "false" ] && run_spotless "${CHECK_SPOTLESS_GOAL}"
[ "${CHECK_TRIVY}" != "false" ] && run_trivy
[ "${CHECK_KUBESCAPE}" != "false" ] && run_kubescape
[ "${CHECK_TALISMAN}" != "false" ] && run_talisman

# pre-commit run -a
