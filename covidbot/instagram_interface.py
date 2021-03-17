import logging
import os
import shutil
import urllib.parse
from typing import List, Optional, Iterable

import requests

from covidbot.covid_data import CovidData, Visualization
from covidbot.single_command_interface import SingleCommandInterface, SingleArgumentRequest
from covidbot.user_manager import UserManager


class InstagramInterface(SingleCommandInterface):
    log = logging.getLogger(__name__)

    access_token: str
    account_id: str
    web_dir: str
    url: str

    def __init__(self, account_id: str, access_token: str, web_dir: str, url: str, user_manager: UserManager,
                 covid_data: CovidData,
                 visualization: Visualization, no_write: bool = False):
        super().__init__(user_manager, covid_data, visualization, 0, no_write)
        self.account_id = account_id
        self.access_token = access_token
        self.web_dir = web_dir
        self.url = url

    def write_message(self, message: str, media_files: Optional[List[str]] = None,
                      reply_obj: Optional[object] = None) -> bool:
        if not media_files:
            raise ValueError("Instagram Interface can just post a single media file with caption")

        media_files = [media_files[0]]

        filename = os.path.basename(shutil.copy2(media_files[0], self.web_dir))

        url = self.url + filename
        message += "\n\nUnser Covidbot versorgt Dich einmal am Tag mit den aktuellen Infektions-, Todes- und " \
                   "Impfzahlen der von Dir ausgewählten Orte. Abonniere ihn einfach auf Telegram, Threema oder " \
                   "Signal. Den Link dazu findest du in unserer Bio!"

        if len(message) > 2200:
            raise ValueError(f"Caption too long: {len(message)} characters")
        message = urllib.parse.quote_plus(message)
        media_response = requests.request("POST", f"https://graph.facebook.com/{self.account_id}/media?"
                                                  f"caption={message}&image_url={url}&access_token={self.access_token}")
        self.log.debug(media_response)
        if media_response.status_code != 200:
            self.log.error(f"Instagram API returned {media_response.status_code}: {media_response.text}")
            return False

        image_id = media_response.json()['id']
        if not image_id:
            self.log.error("Instagram API did not return an image id")
            return False

        post_response = requests.request("POST", f"https://graph.facebook.com/{self.account_id}/media_publish?"
                                                 f"creation_id={image_id}&access_token={self.access_token}")
        self.log.debug(post_response)
        if post_response.status_code != 200:
            self.log.error(f"Instagram API returned {post_response.status_code}: {post_response.text}")
            return False

        return True

    def get_mentions(self) -> Iterable[SingleArgumentRequest]:
        raise NotImplementedError("InstagramInterface does not support individual queries")