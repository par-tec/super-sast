#
# Functions for installing kubescape.
#
install_kubescape(){
    uname_m=$(uname -m)
    if [ "${uname_m}" != "x86_64" ] ; then
        echo "
        Kubescape is not supported on ${uname_m}
        exit 1
        " > /usr/bin/kubescape
        chmod +x /usr/bin/kubescape
        return 0
    fi

    wget ${KUBESCAPE_URL} -O /usr/bin/kubescape
    chmod +x /usr/bin/kubescape
    /usr/bin/kubescape download framework
}
