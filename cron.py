import requests
from bs4 import BeautifulSoup
import time
import json
import os
import datetime
from pathlib import Path

ENABLE_LOG = False
LOGFILE = Path("log.txt")
CREDENTIAL_FILE = Path("credential.json")


class Logger(object):

    """Docstring for Logger. """

    def __init__(self, logfile):
        self._enabled = False
        self._logfile = logfile
        self._index = 0
        if not os.path.exists(logfile):
            with open(logfile, "w"):
                pass

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def wipe(self):
        if self._enabled:
            with open(self._logfile, "w"):
                pass

    def _generate_timestamp(self):
        return datetime.datetime.now().strftime("%D %T.%f")

    def _generate_stamp(self, caption=""):
        return ""
        #  def tab(strn):
        #      return "    " + str(strn) if strn != "" else ""
        #
        #  dt = datetime.datetime.now()
        #  strn = f"""\ {'='*70} {tab(caption)} {tab(self._index)} {tab(dt)} {'_'*70}\n """
        #  self._index += 1
        #  return strn

    def prepend(self, strn, caption="", pad=0):
        timestamp = self._generate_timestamp()
        if self._enabled:
            with open(self._logfile, "r", encoding="utf8") as f:
                data = timestamp + " ::: " + strn + "\n" * (int(pad) + 1)
                data += f.read()

            with open(self._logfile, "w", encoding="utf8") as f:
                f.write(data)


class Cron(object):

    """Docstring for Cron. """

    REQUIRED_FORM_FIELDS = (
        "login",
        "sid",
        "redirect",
        "creation_time",
        "form_token",
    )
    URL_LOGIN_EXTRA = "ucp.php?mode=login"
    URL_CRON_EXTRA = "app.php/snahp/cron/hourly/"

    class LoginFailError(Exception):
        def __init__(self, username):
            self.username = username

        def __str__(self):
            return "Could not loging with the credentials."
            #  return f"""\ ##################################### Could not login with username: {self.username}"""

    def __init__(self):
        self.client = requests.session()
        self.soup = None

    def _get(self, url):
        self.response = self.client.get(url)
        return self.response

    def _post(self, url, data):
        self.response = self.client.post(url, data=data)
        return self.response

    def _get_input_value(self, soup, name):
        return soup.find("input", {"name": name})["value"]

    def _get_login_form(self):
        return self._get(self.host_url)

    def _post_login_form(self, data):
        time.sleep(1)  # Required because of phpbb anti-spam
        return self._post(self.login_url, data)

    def _parse_login_form_response(self, resp):
        soup = BeautifulSoup(resp.text, "html.parser")
        form_data = {
            name: self._get_input_value(soup, name)
            for name in Cron.REQUIRED_FORM_FIELDS
        }
        private_data = {
            "username": self.username,
            "password": self.password,
        }
        form_data.update(private_data)
        return form_data

    def _set_account_info(self, host_url, username, password):
        self._set_host_url(host_url)
        self.username = username
        self.password = password

    def _verify_login(self, resp):
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.find("li", {"id": "username_logged_in"}) is not None

    def _verify_cron_success(self, resp):
        return resp.find("<p>Following hourly") > -1

    def _set_host_url(self, host_url):
        self.host_url = host_url
        self.login_url = host_url + Cron.URL_LOGIN_EXTRA
        self.cron_url = host_url + Cron.URL_CRON_EXTRA

    def login(self):
        print("Signing in to {} as {} ...".format(self.host_url, self.username))
        resp = self._get_login_form()
        self.logger.prepend("Logging In", caption="login")
        form_data = self._parse_login_form_response(resp)
        resp = self._post_login_form(form_data)
        if not self._verify_login(resp):
            raise Cron.LoginFailError(self.username)
        print("    Success")
        self.logger.prepend("Success", caption="login")

    def trigger_cron(self):
        print("Triggering Cron Jobs ...")
        resp = self._get(self.cron_url)
        self.logger.prepend("Triggering Cron", caption="trigger_cron")
        success = self._verify_cron_success(resp.text)
        if success:
            print("    Success")
            self.logger.prepend("Success", caption="trigger_cron")
        else:
            print("    Failure")
            self.logger.prepend("Failure", caption="trigger_cron")

    def login_with_credential_file(self, filepath):
        print("\n\n")
        print("Using credential {} ...".format(filepath))
        with open(filepath, "r", encoding="utf8") as f:
            data = json.loads(f.read())
        self._set_account_info(data["host_url"], data["username"], data["password"])
        self.login()

    def attach_logger(self, logfile):
        self.logger = Logger(logfile)


def main():
    cron = Cron()
    cron.attach_logger(LOGFILE)
    cron.logger.disable()
    if ENABLE_LOG:
        cron.logger.enable()
        #  cron.logger.wipe()
    cron.login_with_credential_file(CREDENTIAL_FILE)
    cron.trigger_cron()


if __name__ == "__main__":
    main()
