#! /usr/bin/python
import urllib
import urllib2
import re
import pycurl
import StringIO
import sys
import os
import getpass

__author__ = "dave bl. db@d1b.org"
__version__= "0.1"
__license__= "gpl v2"
__program__ = "FOS moodle schedule info / file downloader"

def return_red(text):
	return "\033[0;41m" +text+ "\033[m"

def return_blue(text):
	return "\033[0;44m" +text+ "\033[m"

def return_green(text):
	return "\033[01;42m" +text+ "\033[m"

def strip_tags(value):
	return re.sub(r'<[^>]*?>', '', value)

def get_resource_pdf_links(the_page):
	""" returns a list of pdf resource urls """
	resource_list = []
	data = the_page.split("\n")
	for i in data:
		if "/resource" in i and "PDF" in i:
			index_offset = i.find("href=")
			index_end = i.find('"><img src')
			res = i[index_offset+6:index_end]
			resource_list.append(res)
	return resource_list

def get_events(page):
	""" XXX: fix this up to get the actual description instead of the description for the event following the due date """
	data = page.split("\n")
	data.sort()
	events = [j +"\n" for i in data for j in i.split("Due") if "2010" in j and "forum" not in j]
	submited = []
	not_submited = []
	graded = []
	for i in events:
		i = i.replace("PM","PM ")
		i = i.replace("AM", "AM ")
		i = i.strip()
		i = i +"\n"
		if "not submitted" in i.lower():
			 not_submited.append(return_red(i))
		elif "graded" in i.lower() and "not graded" not in i.lower():
			graded.append(return_green(i))
		elif "submitted," in i.lower():
			submited.append(return_blue(i))
	result = graded + submited + not_submited

	return result

def create_directory(dir_loc):
	if os.path.exists(dir_loc) == False:
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

	connection.setopt(pycurl.WRITEFUNCTION, string_s.write)
	connection.setopt(pycurl.URL, url_target)
	connection.perform()
	the_page = str(string_s.getvalue())

	#follow resource PDF links should they exist (for a course)
	if "course/" in url_target:
		resource_list = get_resource_pdf_links(the_page)
		try:
			create_directory("/tmp/PDF")
		except Exception, e:
			print e

		for i in resource_list:
			new_s = StringIO.StringIO()
			connection.setopt(pycurl.FOLLOWLOCATION, True)
			connection.setopt(pycurl.WRITEFUNCTION, new_s.write)
			connection.setopt(pycurl.URL, i)
			connection.perform()
			temp_file = str(new_s.getvalue())
			real_url =  connection.getinfo(pycurl.EFFECTIVE_URL)
			new_s = StringIO.StringIO()
			print real_url
			name_from_last_url = real_url.rfind("/")
			res_name = real_url[name_from_last_url+1:]
			write_to_a_file(temp_file, "/tmp/PDF/"+res_name)
		connection.close()
		return None
	connection.close()
	the_page = strip_tags(the_page)

	return the_page

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

def main():
	conn_details = {}
	url_login = "https://moodle.comp.mq.edu.au/login/index.php"
	url_events = "https://moodle.comp.mq.edu.au/my/index.php"
	url_course = "https://moodle.comp.mq.edu.au/course/view.php?id=52&week=0#section-1"

	try:
		get_credentials_from_accounts_file(conn_details)
	except Exception, e:
		print e
		create_directory(os.path.expanduser("~/.mq"))
		get_user_credentials_from_user_input(conn_details)

		save_credentials_to_accounts_file(conn_details["username"], conn_details["password"], os.path.expanduser("~/.mq/moodle_ics_account") )

	print "enter dl for downloading course material otherwise press s for due dates etc."
	choice = get_input()
	if "dl" in choice:
		print return_red("NOTE: the default course url is for COMP348 and will not work for other courses!")
		print return_red("files will be downloaded to /tmp/PDF/")
		target_url = url_course
	elif "s" in  choice:
		target_url = url_events

	page = get_moodle(url_login, target_url, conn_details)

	if page != None:
		events = get_events(page)
		for i in events:
			print i

	delete_cookie(os.path.expanduser("~/.mq/") )

if __name__=='__main__':
	main()

