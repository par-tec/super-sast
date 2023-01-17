#
# Functions for installing kubescape.
#
install_talisman(){
    uname_m=$(uname -m)
    if [ "${uname_m}" != "x86_64" ] ; then
        return 0
    fi
    wget ${TALISMAN_URL} -O /usr/bin/talisman
    chmod +x /usr/bin/talisman
}
