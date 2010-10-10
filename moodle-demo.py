#!/usr/bin/env python
import urllib
import pycurl
import StringIO
import sys
import os
import getpass
from lxml import html

__author__ = "dave bl. db@d1b.org"
__version__= "0.3"
__license__= "gpl v2"
__program__ = "FOS moodle schedule info / file downloader"

def return_red(text):
	return "\033[0;41m" + text + "\033[m"

def return_blue(text):
	return "\033[0;44m" + text + "\033[m"

def return_green(text):
	return "\033[01;42m" + text + "\033[m"

def get_resources_from_resource_page(the_page, front_part_of_url="https://moodle.comp.mq.edu.au/mod/resource/"):
	dict_res = {}
	doc = html.fromstring(the_page)
	for resource in doc.xpath("//td[@class='cell c1']/a"):
		safe_name = replace_f_name_with_safer_version(resource.text)
		dict_res[safe_name] = front_part_of_url + resource.attrib['href']
	return dict_res

def get_alt_resource_link(the_page):
	doc = html.fromstring(the_page)
	for resource in doc.xpath("//div[@class='popupnotice']/a/@href"):
		return resource

def replace_f_name_with_safer_version(name):
	name = name.strip()
	name = name.replace("/", "_")
	name = name.replace(" ", "_")
	name = name.replace("..", "_")
	name = name.replace("\"", "_")
	name = name.replace("~", "_")
	name = name.replace('"', "_")
	name = name.replace("'", "_")
	name = name.replace(".py", "_python")
	name = name[0:253]
	return name


def get_events(the_page):
	submited = []
	not_submited = []
	graded = []
	doc = html.fromstring(the_page)

	for assign in doc.xpath("//div[@class='assignment overview']"):
		for name, date,in zip (assign.xpath("div[@class='name']/a/text()"), assign.xpath("div[@class='info']/text()")):
			status = assign.xpath("text()")[0]
			as_details = name + " " + date
			if "not submitted" in status.lower():
				not_submited.append(return_red(as_details))
			elif "graded" in status.lower() and "not graded" not in status.lower():
				graded.append(return_green(as_details))
			elif "submitted," in status.lower():
				submited.append(return_blue(as_details))
	result = graded + submited + not_submited
	return result

def create_directory(dir_loc):
	if not os.path.exists(dir_loc):
		os.mkdir(dir_loc)
		os.chmod(dir_loc, 16832)

def get_input():
	return str (raw_input() )

def get_user_credentials_from_user_input(conn_details):
	"""get username / password """
	print "enter your username "
	conn_details["username"] = get_input()
	conn_details["password"] = getpass.getpass("enter your password\n")
	return conn_details

def get_moodle(url_login, url_target, conn_details):
	submit_data_t = [ ('username', str(conn_details["username"]) ), ('password', conn_details["password"])  ]
	submit_data_t = urllib.urlencode(submit_data_t)
	cookie_loc = os.path.expanduser("~/.mq/moodle_cookie")
	string_s = StringIO.StringIO()
	connection = pycurl.Curl()
	connection.setopt(pycurl.FOLLOWLOCATION, False)
	connection.setopt(pycurl.SSL_VERIFYPEER, 1)
	connection.setopt(pycurl.SSL_VERIFYHOST, 2)
	connection.setopt(pycurl.WRITEFUNCTION, string_s.write)
	connection.setopt(pycurl.COOKIEFILE, cookie_loc )
	connection.setopt(pycurl.COOKIEJAR, cookie_loc )
	connection.setopt(pycurl.POSTFIELDS, submit_data_t)
	connection.setopt(pycurl.URL, url_login)
	connection.perform()

	#now get the page we want
	string_s = StringIO.StringIO()
	connection.setopt(pycurl.WRITEFUNCTION, string_s.write)
	connection.setopt(pycurl.URL, url_target)
	connection.setopt(pycurl.FOLLOWLOCATION, True)
	connection.perform()

	the_page = str(string_s.getvalue())
	return the_page, connection


def create_tmp_dir(dir_path):
	try:
		create_directory(dir_path)
	except Exception, e:
		print e

def download_resources_using_connection_from_resource_page(the_page, connection, dir_path="/tmp/moodle_dl"):
	resources = get_resources_from_resource_page(the_page)
	create_directory(dir_path)
	for name, link in resources.items():
		new_s = StringIO.StringIO()
		connection.setopt(pycurl.FOLLOWLOCATION, True)
		connection.setopt(pycurl.WRITEFUNCTION, new_s.write)
		connection.setopt(pycurl.URL, link)
		connection.perform()
		temp_file = str(new_s.getvalue())
		real_url = connection.getinfo(pycurl.EFFECTIVE_URL)
		if "https://moodle.comp.mq.edu.au/mod/resource/view.php?id=" in real_url:
			new_s = StringIO.StringIO()
			actual_res_loc = get_alt_resource_link(temp_file)
			if actual_res_loc is None:
				continue
			connection.setopt(pycurl.FOLLOWLOCATION, False)
			connection.setopt(pycurl.WRITEFUNCTION, new_s.write)
			connection.setopt(pycurl.URL, actual_res_loc)
			connection.perform()
			temp_file = str(new_s.getvalue())
			real_url = connection.getinfo(pycurl.EFFECTIVE_URL)
		print real_url

		full_file_loc = dir_path + "/" + replace_f_name_with_safer_version(name)
		assert os.path.realpath(full_file_loc).startswith(dir_path + "/"), " assert that we are only going to write the file to the temp dir"
		write_to_a_file(temp_file, full_file_loc)

def write_to_a_file(data,full_file_loc):
	the_file = open(full_file_loc, 'w')
	the_file.write(data)
	the_file.close()

def read_from_a_file(full_file_loc,return_type ):
	the_file = open(full_file_loc, 'r')
	if return_type == "read":
		return_type = the_file.read()
	if return_type == "readlines":
		return_type = the_file.readlines()
	the_file.close()
	return return_type

def save_credentials_to_accounts_file(username,password,file_loc):
	assert username != ""
	assert password != ""
	write_to_a_file("username="+username +"\n" +"password="+password+"\n", file_loc)

def get_credentials_from_accounts_file(conn_details):
	account_file_loc = os.path.expanduser("~/.mq/moodle_ics_account")
	username = ""
	password = ""
	the_file = read_from_a_file(account_file_loc, "readlines")
	for line in the_file:
		if "username=" in line:
			index = line.find("=")
			assert index +1 < len(line)
			username = line[index+1:-1]
		if "password=" in line:
			index = line.find("=")
			assert index +1 < len(line)
			password = line[index+1:-1]
	conn_details["username"] = username
	conn_details["password"] = password
	return conn_details

def delete_cookie(folder_loc):
	try:
		os.remove(folder_loc+"/moodle_cookie")
	except Exception, e:
		print e

def get_auth_information(conn_details):
	try:
		conn_details = get_credentials_from_accounts_file(conn_details)
	except Exception, e:
		print e
		create_directory(os.path.expanduser("~/.mq"))
		conn_details = get_user_credentials_from_user_input(conn_details)

		save_credentials_to_accounts_file(conn_details["username"], conn_details["password"], os.path.expanduser("~/.mq/moodle_ics_account") )
	return conn_details

def main():
	conn_details = {}
	url_login = "https://moodle.comp.mq.edu.au/login/index.php"
	url_events = "https://moodle.comp.mq.edu.au/my/index.php"
	url_course = "https://moodle.comp.mq.edu.au/mod/resource/index.php?id=68"

	conn_details = get_auth_information(conn_details)

	print "enter dl for downloading course material otherwise press s for due dates etc."
	choice = get_input()
	if "dl" in choice:
		print return_red("NOTE: the default course url is for COMP332 and will not work for other courses!")
		print return_red("files will be downloaded to /tmp/moodle_dl/")
		target_url = url_course
	elif "s" in  choice:
		target_url = url_events

	the_page, connection = get_moodle(url_login, target_url, conn_details)
	if target_url == url_events:
		events = get_events(the_page)
		for i in events:
			print i
	else:
		download_resources_using_connection_from_resource_page(the_page, connection)

	connection.close()
	delete_cookie(os.path.expanduser("~/.mq/") )

if __name__=='__main__':
	main()
