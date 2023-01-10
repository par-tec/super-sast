#!/usr/bin/sh
#
# By default, run /usr/local/bin/jenkins-agent
#
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

run_talisman
run_trivy
run_kubescape
# pre-commit run -a
