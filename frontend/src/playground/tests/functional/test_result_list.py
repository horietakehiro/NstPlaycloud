from ..common.base import BaseTestCase
from django.conf import settings

import os

from playground import messages

class ResultListTestCase(BaseTestCase):

    def test_result_list_1(self):
        """
        open result_list page.
        by default display all result list
        """
        self.setUp_driver()

        # create two transfer images
        self.exec_transfer(self.content, self.style)
        content = os.path.join(os.path.dirname(self.content), "content_2.png")
        style = os.path.join(os.path.dirname(self.style), "style_2.png")
        self.exec_transfer(content, style)

        result_list = self.get_element("class_name", "ImageName", single=False)
        self.assertEqual(len(result_list), 6)

        # open the result_list page by default
        self.driver.get(self.live_server_url + "/result_list/0/")
        h2 = self.get_element("tag_name", "h2")
        self.assertEqual(h2.text, "ResultList")

        result_list = self.get_element("class_name", "TransferName", single=False)
        self.assertEqual(len(result_list), 2)


    def test_result_list_2(self):
        """
        open result_list page.
        specifying result image_id, display result list only related the image
        """
        self.setUp_driver()

        # create two transfer images
        content = os.path.join(os.path.dirname(self.content), "content_2.png")
        style = os.path.join(os.path.dirname(self.style), "style_2.png")
        self.exec_transfer(self.content, self.style)
        self.exec_transfer(content, style)

        # open the result_list page with specifying image_id
        related_result = self.get_element("id", "related_relsut_link")
        related_result.click()
        h2 = self.get_element("tag_name", "h2")
        self.assertEqual(h2.text, "ResultList")

        result_list = self.get_element("class_name", "TransferName", single=False)
        self.assertEqual(len(result_list), 1)



    def test_result_list_13(self):
        """
        can transit to image_list page from result_list page
        """
        self.setUp_driver()

        self.driver.get(self.live_server_url + "/result_list/0/")
        h2 = self.get_element("tag_name" ,"h2")
        self.assertEqual(h2.text, "ResultList")
        
        link = self.get_element("id", "image_list_link")
        link.click()
        h2 = self.get_element("tag_name" ,"h2")
        self.assertEqual(h2.text, "ImageList")
