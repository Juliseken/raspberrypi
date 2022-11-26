mirror_share
=========

This role installs a script for mirroring data via rsync from a share to a directory.

Role Variables
--------------

    mirror_share_home: /home/dir
    mirror_share_host: the-host
    mirror_share_name: the share name
    mirror_share_mountpoint: /the/mountpoint
    mirror_share_credentials_file: /the/credentials/file
    mirror_share_destination: /the/destination/directory
    mirror_share_user_id: theuser
    mirror_share_group_id: thegroup
    mirror_share_alert_command: the-alert-command

Example Playbook
----------------

    - hosts: localhost
      roles:
        - role: roles/mirror_share
      vars:
        mirror_share_home: /home/dir
        mirror_share_host: the-host
        mirror_share_name: the share name
        mirror_share_mountpoint: /the/mountpoint
        mirror_share_credentials_file: /the/credentials/file
        mirror_share_destination: /the/destination/directory
        mirror_share_user_id: theuser
        mirror_share_group_id: thegroup
        mirror_share_alert_command: the-alert-command
