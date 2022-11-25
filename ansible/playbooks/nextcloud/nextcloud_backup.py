#!/usr/bin/python3

# nextcloud doc on how to backup and restore:
# * https://docs.nextcloud.com/server/latest/admin_manual/maintenance/backup.html
# * https://docs.nextcloud.com/server/latest/admin_manual/maintenance/restore.html

import os
import shutil
import tarfile
import logging
import logging.config
import docker
import traceback
import sys
import tempfile
import argparse
import getpass

def enable_maintenance_mode(container_name):
  docker_client = docker.from_env()
  container = docker_client.containers.get(container_name)
  return container.exec_run("php occ maintenance:mode --on", tty=True,
    user="www-data")

def get_html_tar(container_name):
  docker_client = docker.from_env()
  container = docker_client.containers.get(container_name)
  blob, meta = container.get_archive("/var/www/html")
  return blob

def put_html_tar(tar_filename, container_name):
  docker_client = docker.from_env()
  container = docker_client.containers.get(container_name)
  tar = open(tar_filename, 'rb').read()
  container.put_archive("/tmp", tar)
  container.exec_run("chown -R www-data:www-data /tmp/html")
  container.exec_run("chmod -R 777 /tmp/html")
  container.exec_run("rsync --acls --archive --one-file-system --delete "
    "/tmp/html /var/www")
  container.exec_run("rm -fr /tmp/html")

def tar_write_to_disk(tar, dest):
  try:
    os.remove(dest)
  except FileNotFoundError:
    pass
  dest_handle = open(dest, 'wb')
  for chunk in tar:
    dest_handle.write(chunk)
  dest_handle.close()

def tar_extract(tar_filename, dest_dir):
  os.system("mkdir -p " + dest_dir)
  tar = tarfile.open(tar_filename)
  tar.extractall(dest_dir)
  tar.close()
  os.remove(tar_filename)

def tar_create(source, tar_filename):
  with tarfile.open(tar_filename, "w") as tar:
    tar.add(source, arcname=os.path.basename(source))

def postgres_get_db_dump(container_name):
  docker_client = docker.from_env()
  container = docker_client.containers.get(container_name)
  return container.exec_run("pg_dumpall --clean --username postgres",
    tty=True, user="postgres").output

def postgres_import_db_dump(dump_file, container_name):
  #docker_client = docker.from_env()
  #docker_db_container = docker_client.containers.get(container_name)
  # TODO: in python machen
  os.system("cat " + dump_file + " | docker exec --interactive " +
    container_name + " psql --username postgres")

def write_to_file(content, filename):
  file_handle = open(filename, 'wb')
  file_handle.write(content)
  file_handle.close()

def replace_old_backup(source_base_dir, dest_base_dir, html_dir, dump_file):
  logger = logging.getLogger(__name__)
  shutil.rmtree(dest_base_dir + "/" + html_dir, ignore_errors=True)
  try:
    os.remove(dest_base_dir + "/" + dump_file)
  except FileNotFoundError:
    pass
  
  os.system("cp -r " + source_base_dir + "/" + html_dir + " " + dest_base_dir)
  os.system("cp " + source_base_dir + "/" + dump_file + " " + dest_base_dir)
  
  user = getpass.getuser()
  logger.debug("Change owner to " + user + ":" + user + " of " + dest_base_dir)
  os.system("sudo chown -R " + user + ":" + user + " " + dest_base_dir)
  logger.debug("Set mode rwx for directories in " + dest_base_dir)
  os.system("find " + dest_base_dir + r" -type d -exec chmod 770 {} \;")
  logger.debug("Set mode rw- for files in " + dest_base_dir)
  os.system("find " + dest_base_dir + r" -type f -exec chmod 660 {} \;")

def disable_maintenance_mode(container_name):
  docker_client = docker.from_env()
  container = docker_client.containers.get(container_name)
  return container.exec_run('php occ maintenance:mode --off', tty=True,
    user='www-data')

def create(backup_base_dir, html_dir, dump_file, docker_web_container_name, docker_db_container_name):
  logger = logging.getLogger(__name__)

  logger.info("Enable maintenance mode on nextcloud server")
  result = enable_maintenance_mode(docker_web_container_name)
  logger.info(result.output)
  
  temp_dir = tempfile.mkdtemp()
  try:
    logger.info("temp_dir is " + temp_dir)
  
    logger.info("Get nextcloud configuration /var/www/html from container " +
      docker_web_container_name)
    nextcloud_html_tar = get_html_tar(docker_web_container_name)
    
    logger.info("Get postgres database dump from container " +
      docker_db_container_name)
    postgres_dump = postgres_get_db_dump(docker_db_container_name)
    
    logger.info("Write nextcloud configuration to " + temp_dir + "/" + html_dir
      + ".tar")
    tar_write_to_disk(nextcloud_html_tar, temp_dir + "/" + html_dir + ".tar")
    
    logger.info("Extract " + temp_dir + "/" + html_dir + ".tar to " + temp_dir +
      " and remove the former.")
    tar_extract(temp_dir + "/" + html_dir + ".tar", temp_dir)
    
    logger.info("Write postgres database dump to " + temp_dir + "/" + dump_file)
    write_to_file(postgres_dump, temp_dir + "/" + dump_file)
    
    logger.info("Backup successful. Replace old backup with new backup.")
    replace_old_backup(temp_dir, backup_base_dir, html_dir, dump_file)
  finally:
    logger.info("Remove temp_dir " + temp_dir + " if it exists")
    shutil.rmtree(temp_dir, ignore_errors=True)
    logger.info("Disable maintenance mode")
    try:
      result = disable_maintenance_mode(docker_web_container_name)
      logger.info(result.output)
    except docker.errors.APIError as err:
      logger.warning("Couldn't disable maintenance mode on nextcloud server.")
      raise err

def restore(backup_base_dir, html_dir, dump_file, docker_web_container_name, docker_db_container_name):
  logger = logging.getLogger(__name__)
  
  logger.info("Enable maintenance mode on nextcloud server")
  result = enable_maintenance_mode(docker_web_container_name)
  logger.info(result.output)
  
  try:
    temp_dir = tempfile.mkdtemp()
    logger.info("temp_dir is " + temp_dir)
    
    logger.info("Create " + temp_dir + "/" + html_dir + ".tar")
    html_tar=temp_dir + "/" + html_dir + ".tar"
    tar_create(backup_base_dir + "/" + html_dir, html_tar)
    
    logger.info("Put " + html_tar + " into container " +
      docker_web_container_name)
    put_html_tar(html_tar, docker_web_container_name)
    
    logger.info("Import postgres database dump")
    postgres_import_db_dump(backup_base_dir + "/" + dump_file,
      docker_db_container_name)
  finally:
    logger.info("Remove temp_dir " + temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)
    logger.info("Disable maintenance mode")
    try:
      result = disable_maintenance_mode(docker_web_container_name)
      logger.info(result.output)
    except docker.errors.APIError as err:
      logger.warning("Couldn't disable maintenance mode on nextcloud server.")
      raise err

def parse_cmd_line():
  parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('operation', help='create|restore',
    choices=["create", "restore"], type=str)
  parser.add_argument("-l", "--log-config-file", type=str,
    help="Path to the log config ini.",
    default=("{{ home }}"
      "/etc/nextcloud/nextcloud_backup.log.ini"))
  parser.add_argument("-d", "--backup-base-dir", type=str,
    help="Directory where the backup is located.",
    default="{{ nextcloud_backup_basedir }}")
  parser.add_argument("--nextcloud-web-container", type=str,
    help="Name of the nextcloud web docker container.",
    default="nextcloud-web-1")
  parser.add_argument("--nextcloud-db-container", type=str,
    help="Name of the nextcloud db docker container.",
    default="nextcloud-db-1")
  return parser.parse_args()

def main():
  args = parse_cmd_line()
  
  html_dir="html"
  dump_file="nextcloud-postgres.dump"
  
  logging.config.fileConfig(args.log_config_file)
  
  if args.operation == "create":
    create(args.backup_base_dir, html_dir, dump_file,
      args.nextcloud_web_container, args.nextcloud_db_container)
  elif args.operation == "restore":
    restore(args.backup_base_dir, html_dir, dump_file,
      args.nextcloud_web_container, args.nextcloud_db_container)
  else:
    assert(False)

if __name__ == "__main__":
  main()
