#
# Functions for installing kubescape.
#
install_kubescape(){
    uname_m=$(uname -m)
    if [ "${uname_m}" != "x86_64" ] ; then
        return 0
    fi

    wget ${KUBESCAPE_URL} -O /usr/bin/kubescape
    chmod +x /usr/bin/kubescape
    /usr/bin/kubescape download framework
}
