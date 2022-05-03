import logging
import os
import urllib
from time import sleep

import requests
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(format="%(asctime)s - %(message)s", datefmt="%y-%m-%d %H:%M:%S")

AZCAPTCHA_API_KEY = os.environ["AZCAPTCHA_API_KEY"]


class CaptchaSolver:
    def __init__(self, browser: Chrome, api_key: str = AZCAPTCHA_API_KEY):
        self.browser = browser
        self.sitekey = self.find_sitekey()
        self.api_key = api_key

    def find_sitekey(self):
        try:
            self.browser.refresh()
            sitekey_elem = WebDriverWait(self.browser, 30).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#gs_captcha_c iframe")
                )
            )
            return urllib.parse.parse_qs(sitekey_elem.get_attribute("src"))["k"][0]
        except TimeoutException:
            raise Exception(f"No sitekey found")

    def solve_captcha(self):
        post_resp = self.post_request()
        logging.warning(f"{post_resp}")
        assert post_resp["status"] == 1
        request_id = post_resp["request"]
        logging.warning(f"Captcha token send: {request_id}")
        sleep(20)
        while True:
            get_resp = self.get_request(request_id)
            if get_resp["request"] == "CAPCHA_NOT_READY":
                logging.warning(f"Captcha not ready, waiting ...")
                sleep(5)
            elif get_resp["request"] == "ERROR_CAPTCHA_UNSOLVABLE":
                logging.warning(f"Captcha is unsolvable, reloading ...")
                self.browser.refresh()
                self.solve_captcha()
            else:
                break

        assert get_resp["status"] == 1
        logging.warning(f"Captcha is solved")
        self._submit(get_resp["request"])

    def post_request(self):
        return requests.get(
            "http://azcaptcha.com/in.php",
            params={
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": self.sitekey,
                "pageurl": self.browser.current_url,
                "invisible": "1",
                "json": "1",
            },
        ).json()

    def get_request(self, id: int):
        return requests.get(
            "http://azcaptcha.com/res.php",
            params={"key": self.api_key, "action": "get", "id": id, "json": 1},
        ).json()

    def _submit(self, answer_token: str):
        self.browser.execute_script(
            f'document.getElementById("g-recaptcha-response").innerHTML="{answer_token}";'
        )
        self.browser.find_element(By.ID, "gs_captcha_f").submit()
        WebDriverWait(self.browser, 30).until_not(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#gs_captcha_ccl,#recaptcha")
            )
        )
