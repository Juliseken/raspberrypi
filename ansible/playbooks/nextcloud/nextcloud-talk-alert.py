#!/usr/bin/python3

import argparse
import requests

def alert(message, chat_room_token, basic_auth_file):
  # docs https://nextcloud-talk.readthedocs.io/en/latest/chat/
  nextcloud_host="raspberrypi.fritz.box"
  nextcloud_port="8080"
  nextcloud_protocol="http"
  nextcloud_chat_endpoint="/ocs/v2.php/apps/spreed/api/v1/chat"
  url = (nextcloud_protocol + "://" + nextcloud_host + ":" + nextcloud_port +
    nextcloud_chat_endpoint + "/" + chat_room_token)
  
  basic_auth_file_handle = open(basic_auth_file, 'r')
  basic_auth = basic_auth_file_handle.read()
  basic_auth_file_handle.close()
  
  return requests.post(
    url,
    headers = {
      "Authorization": "Basic " + basic_auth,
      "Content-Type": "application/json",
      "Accept": "application/json",
      "OCS-APIRequest": "true"
    },
    json = {
      "token": chat_room_token,
      "message": message})

def parse_cmd_line():
  parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("message", type=str,
    help="The alert message.")
  return parser.parse_args()

def main():
  chat_room_token="{{ nextcloud_chat_room_token }}"
  basic_auth_file="{{ home }}/.nextcloud-basic-auth-service_user"

  args = parse_cmd_line()
  return alert(args.message, chat_room_token, basic_auth_file)

if __name__ == "__main__":
  print(main())
