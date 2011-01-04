#!/usr/bin/env python
import ConfigParser

class AuthDetails(object):
	""" this is just a basic wrapper around ConfigParser to make storing a username and a password easier """

	def __init__(self, auth_file_loc, username="", password=""):
		self._username = username
		self._password = password
		self.auth_file_loc = auth_file_loc
		self.config = ConfigParser.RawConfigParser()

	def store_user_pass(self):
		self.config.add_section("auth")
		self.config.set("auth", "password", self._password)
		self.config.set("auth", "username", self._username)

		self._save()

	def _save(self):
		with open(self.auth_file_loc, "wb") as configfile:
			self.config.write(configfile)

	def read_config(self):
		self.config.read(self.auth_file_loc)

	def get_username(self):
		return self.config.get("auth", "username")

	def get_password(self):
		return self.config.get("auth", "password")

def main():
	""" just a quick usage test """
	s = AuthDetails("/tmp/testme123", "myusername", "mypassword")
	s.store_user_pass()
	x = AuthDetails("/tmp/testme123")
	x.read_config()
	assert x.get_username() == "myusername"
	assert x.get_password() == "mypassword"

if __name__ == "__main__":
	main()
