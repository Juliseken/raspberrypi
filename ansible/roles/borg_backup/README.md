borg_backup
=========

This role installs some borg backup utility scripts on the target machine.

Role Variables
--------------

    borg_bin_dir: /home/bin
    borg_backup_name: local
    borg_source_directory: /the/source/dir
    borg_repository: /the/borg/repository
    borg_passcommand: "cat passphrasefile"
    borg_mountpoint: /the/borg/mountpoint
    borg_archive_prefix: prefix-
    borg_alert_command: echo
    borg_keep:
      daily: 7
      weekly: 2
      monthly: 2

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - name: install borg backup scripts for local backup
      hosts: localhost
      roles:
         - role: roles/borg_backup
      vars:
        borg_bin_dir: /home/bin
        borg_backup_name: local
        borg_source_directory: /the/source/dir
        borg_repository: /the/borg/repository
        borg_passcommand: "cat passphrasefile"
        borg_mountpoint: /the/borg/mountpoint
        borg_archive_prefix: prefix-
        borg_alert_command: echo
        borg_keep:
          daily: 7
          weekly: 2
          monthly: 2
