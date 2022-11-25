# raspberrypi

This repository contains different scripts used for provisioning of a raspberrypi.

## provisioning

    cd ansible
    ansible-playbook playbooks/provision-basic.yaml
    ansible-playbook playbooks/nextcloud/nextcloud.yml
    ansible-playbook playbooks/mirror_share.yml
    ansible-playbook playbooks/borg_backup.yml
