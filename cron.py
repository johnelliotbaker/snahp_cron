import requests
from bs4 import BeautifulSoup
import time
import json
from logger import logger


print_debug = logger.debug


CREDENTIAL_FILE = "credential.json"


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

    class LoginError(Exception):
        def __init__(self, username):
            self.username = username
            logger.error(str(self))

        def __str__(self):
            return 'Could not login as "{}"'.format(self.username)

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
        print_debug("Signing in to {} as {} ...".format(self.host_url, self.username))
        resp = self._get_login_form()
        form_data = self._parse_login_form_response(resp)
        resp = self._post_login_form(form_data)
        if not self._verify_login(resp):
            raise Cron.LoginError(self.username)
        print_debug("Success")

    def trigger_cron(self):
        print_debug("Triggering Cron Jobs ...")
        resp = self._get(self.cron_url)
        success = self._verify_cron_success(resp.text)
        if success:
            print_debug("Success")
        else:
            logger.error("Failure")

    def login_with_credential_file(self, filepath):
        print("\n\n")
        logger.info("Attempting login with {} ...".format(filepath))
        with open(filepath, "r", encoding="utf8") as f:
            data = json.loads(f.read())
        self._set_account_info(data["host_url"], data["username"], data["password"])
        self.login()


def main():
    cron = Cron()
    cron.login_with_credential_file(CREDENTIAL_FILE)
    cron.trigger_cron()


if __name__ == "__main__":
    main()
