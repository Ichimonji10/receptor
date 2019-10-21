#!/usr/bin/env bash

# In OpenShift, containers are run as a random high number uid
# that doesn't exist in /etc/passwd, but Ansible module utils
# require a named user. So if we're in OpenShift, we need to make
# one before Ansible runs.
if [ `id -u` -ge 500 ] || [ -z "${CURRENT_UID}" ]; then

  cat << EOF > /tmp/passwd
root:x:0:0:root:/root:/bin/bash
receptor:x:`id -u`:`id -g`:,,,:/receptor:/bin/bash
EOF

  cat /tmp/passwd > /etc/passwd
  rm /tmp/passwd
fi

if [ ! -f /receptor/receptor.conf ]; then
    cp /tmp/receptor.conf /receptor/receptor.conf
fi

exec tini -- "${@}"