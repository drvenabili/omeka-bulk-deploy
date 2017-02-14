# this programme installs one to several Omeka instances on a linux webserver. Requires Python (2.7), selenium, pyvirtualdisplay and xvfb.
# Usernames and passwords are stored in datas.db
# More info : shengche@ulb.ac.be - http://hengchen.net
# Original work by Laurent Contzen - https://www.linkedin.com/in/laurent-contzen-2103ba66/


# This programme is supposed to be launched as root from /var/www/html/omeka. If you wish to launch it from somewhere else, adjust the paths :-)

from random import Random
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from pyvirtualdisplay import Display
import MySQLdb
import sys
import sqlite3
import os
import zipfile
import time
import argparse
import getpass

class OmekaInstance:

    def __init__(self, id, args, db_host_passwd):
        self.id = id
        self.db_name = "omeka" + str(self.id)
        self.db_user = "omeka_user_" + str(self.id)
        self.db_passwd = self.generate_password ()
        if (args.prompt):
            self.omeka_user = raw_input("Username : ")
        else:
            self.omeka_user = "groupe" + str(self.id)
        self.folder_name = self.omeka_user
        self.omeka_passwd = self.generate_password ()
        if (args.prompt):
            self.omeka_title = self.omeka_user.capitalize() + "'s Omeka Instance"
        else:
            self.omeka_title = "Omeka Groupe " + str(id)
        self.db_host_passwd = db_host_passwd
        self.args = args
        print "    Passwords generated"

    def generate_password (self):
        rng = Random()
        chars = '789yuiophjknmYUIPHJKLNM23456qwertasdfgzxcvbQWERTASDFGZXCVB'
        passwordLength = 8
        password = ""

        for i in range(passwordLength):
            password = password + rng.choice(chars)

        return password


    def create_db_and_user (self):
        try:
            conn = MySQLdb.connect (host = "localhost",
                                    user = "root",
                                    passwd = self.db_host_passwd)
            cursor = conn.cursor ()
            cursor.execute ("USE mysql;")
            request = "CREATE DATABASE " + self.db_name + \
              " DEFAULT CHARACTER SET 'utf8' DEFAULT COLLATE 'utf8_unicode_ci';"
            cursor.execute (request)
            request = "CREATE USER '" + self.db_user + \
              "'@'localhost' IDENTIFIED BY '" + self.db_passwd + "';"
            cursor.execute (request)
            request = "GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP ON " + \
              self.db_name + ".* TO '" + self.db_user + "'@'localhost';"
            cursor.execute (request)
            cursor.close ()
            conn.close ()
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit (1)

    def save_db_passwd (self):
        try:
            conn = sqlite3.connect('datas.db')
            c = conn.cursor ()
            request = "INSERT INTO db_passwds VALUES (" + str(self.id) + \
              ", \"" + self.db_name + "\", \"" + self.db_passwd + "\");"
            c.execute (request)
            conn.commit ()
            c.close ()
        except sqlite3.Error, e:
            print "An error occurred:", e.args[0]

    def save_omeka_datas (self):
        try:
            conn = sqlite3.connect('datas.db')
            c = conn.cursor ()
            request = "INSERT INTO omeka_datas VALUES (" + str(self.id) + \
              ", \"" + self.omeka_user + "\", \"" + self.omeka_passwd + "\");"
            c.execute (request)
            conn.commit ()
            c.close ()
        except sqlite3.Error, e:
            print "An error occurred:", e.args[0]


    def extract_zip (self):
        z = zipfile.ZipFile ("omeka-2.4.1.zip")
        z.extractall ()
        os.rename ("omeka-2.4.1", self.folder_name)

    def config_db_ini (self):
        file_name = self.folder_name + "/db.ini"
        os.remove(file_name)
        dbini = open (file_name, "w")
        dbini.write ("[database] \n")
        dbini.write ("host     = \"localhost\" \n")
        dbini.write ("username = \"" + self.db_user + "\" \n")
        dbini.write ("password = \"" + self.db_passwd + "\" \n")
        dbini.write ("dbname   = \""+ self.db_name + "\" \n")
        dbini.write ("prefix   = \"omeka_\" \n")
        dbini.write ("charset  = \"utf8\" \n")
        dbini.write (";port     = \"\" \n")
        dbini.close()

    def chmod_archive_folder (self):
        path = self.folder_name + "/files"
        os.system("chmod -R 777 " + path)

    def config_language (self):  # we're changing the locale to French
        configini = open(self.folder_name + "/application/config/config.ini", "r+")
        configini.write(configini.read().replace('locale.name = ""', 'locale.name = "fr"'))
        configini.close()

    def process_install_form (self):
        if (self.args.xvfb):
	    print "Omeka is being installed in: " + self.folder_name
            display = Display(visible=0, size=(800, 600))
            display.start()
        driver = webdriver.Firefox()
        driver.get("http://localhost/omeka/" + self.folder_name + "/install")
        inputElement = driver.find_element_by_name("username")
        inputElement.send_keys(self.omeka_user)
        inputElement = driver.find_element_by_name("password")
        inputElement.send_keys(self.omeka_passwd)
        inputElement = driver.find_element_by_name("password_confirm")
        inputElement.send_keys(self.omeka_passwd)
        inputElement = driver.find_element_by_name("super_email")
        inputElement.send_keys("test@ulb.ac.be")
        inputElement = driver.find_element_by_name("administrator_email")
        inputElement.send_keys("test@ulb.ac.be")
        inputElement = driver.find_element_by_name("site_title")
        inputElement.send_keys(self.omeka_title)
        inputElement.submit()
        try:
            WebDriverWait(driver, 10).until(
                lambda driver : driver.find_element_by_partial_link_text("Tableau"))
        finally:
            driver.quit()

    def delete_install_folder (self):
        os.system("rm -r " + self.folder_name + "/install")

    def deploy (self):
        print "    Starting to create db and user"
        self.create_db_and_user ()
        print "    DB and user created"
        self.save_db_passwd ()
        print "    DB password saved"
        print "    Starting to extract zip file"
        self.extract_zip ()
        print "    Zip file extracted"
        print "    Configuring db.ini file"
        self.config_db_ini ()
        print "    Changing permissions on archive folder"
        self.chmod_archive_folder ()
        print "    Setting language to french"
        self.config_language ()
        print "    Starting install form processing"
        self.process_install_form ()
        print "    Install form processed"
        self.save_omeka_datas ()
        print "    Omeka datas saved"
        self.delete_install_folder ()
        print "    Install folder deleted"


class Deployer:

    def __init__(self):
        self.args = self.parse_args ()
        self.number_of_instances_to_deploy = self.args.count
        self.number_of_existing_instances = self.count_existing_instances ()
        self.db_host_passwd = getpass.getpass("Host database password: ")

        if (self.args.download_zip):
            self.download_zip ()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("count", help="number of instances to deploy",
                            type=int)
        parser.add_argument("--xvfb",
                            help="use xvfb driver to avoid displaying browser",
                            action="store_true")
        parser.add_argument("--download-zip",
                            help="download omeka-2.4.1.zip from omekas's website",
                            action="store_true")
        parser.add_argument("--prompt",
                            help="prompt user for db_name and omeka_username",
                            action="store_true")
        args = parser.parse_args ()

        return args

    def download_zip (self):
        os.system('wget -c http://omeka.org/files/omeka-2.4.1.zip')

    def count_existing_instances (self):
        if (os.path.exists('datas.db')):
            try:
                conn = sqlite3.connect('datas.db')
                c = conn.cursor ()
                c.execute ("SELECT COUNT(*) FROM db_passwds;")
                count = c.fetchone ()[0]
                c.close()
            except sqlite3.Error, e:
                print "An error occured:", e.args[0]
            return count
        else:
            return 0

    def init_datas (self):
        if (os.path.exists('datas.db') == False):
            try:
                conn = sqlite3.connect('datas.db')
                c = conn.cursor ()
                c.execute ('''CREATE TABLE db_passwds
                (group_id integer, db_name text, passwd text);''')
                c.execute ('''CREATE TABLE omeka_datas
                (group_id integer, username text, passwd text);''')
                conn.commit ()
                c.close ()
            except sqlite3.Error, e:
                print "An error occurred:", e.args[0]

    def deploy_instance (self, id):
        print "Starting deployment of instance #" + str(id)
        instance = OmekaInstance (id, self.args, self.db_host_passwd)
        instance.deploy()
        print "Instance #" + str(id) + " is deployed."
        print ""

    def start (self):
        for i in xrange(self.number_of_instances_to_deploy):
            self.deploy_instance (self.number_of_existing_instances + i + 1)


def main ():
    deployer = Deployer ()
    deployer.init_datas ()
    deployer.start ()

if __name__ == '__main__':
    main()
