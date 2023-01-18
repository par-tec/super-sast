#
# Functions for installing talisman.
#
install_talisman(){
    uname_m=$(uname -m)
    if [ "${uname_m}" != "x86_64" ] ; then
        echo "
        Talisman is not supported on ${uname_m}
        exit 1
        " > /usr/bin/talisman
        chmod +x /usr/bin/talisman
        return 0
    fi
    wget ${TALISMAN_URL} -O /usr/bin/talisman
    chmod +x /usr/bin/talisman
}
