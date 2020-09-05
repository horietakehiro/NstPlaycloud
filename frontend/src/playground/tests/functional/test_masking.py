from ..common.base import BaseTestCase

from playground import messages

import requests

class MaskingTestCase(BaseTestCase):

    def test_masking_1(self):
        """
        test_masking_1 : select the transfer image on result_list page,
        and move to masking page, where display 5 masking images
        """
        self.setUp_driver()

        # register one transfer result
        self.exec_transfer(self.content, self.style)
        self.driver.get(self.live_server_url + "/result_list/0/")

        masking = self.get_element("class_name", "Masking")
        masking.click()


        h2 = self.get_element("tag_name", "h2")
        self.assertEqual(h2.text, "Masking")

        trasnfer_list = self.get_element("class_name", "TransferData", single=False)
        self.assertEqual(len(trasnfer_list), 2)


    def test_masking_2(self):
        """
        test_masking_2 : if result data has deleted,
        redirect to image_list page with error message
        """
        self.setUp_driver()

        # register one transfer result
        self.exec_transfer(self.content, self.style)
        self.driver.get(self.live_server_url + "/result_list/0/")

        # create tmp driver and delete content image
        driver = self.create_tmp_driver()
        driver.get(self.live_server_url)
        delete = self.get_element("class_name", "Delete", driver=driver)
        delete.click()
        driver.quit()

        # request masking
        masking = self.get_element("class_name", "Masking")
        action = self.get_element("id", "masking")
        result_id = action.get_attribute("action").split("/")[-1]
        masking.click()

        # redirect to image_list with error message
        h2 = self.get_element("tag_name", "h2")
        self.assertEqual(h2.text, "ImageList")

        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.MASKING_FAIL_DATA_NOTFOUND.format(result_id),
            [m.text for m in message_list],
        )



    def test_masking_3(self):
        """
        test_masking_3 : if masking request to api gateway fails,
        redirect to image_list page with error message
        """
        self.setUp_driver()

        # register one transfer result
        self.exec_transfer(self.content, self.style)
        self.driver.get(self.live_server_url + "/result_list/0/")

        # temporarily delete lambda function associated with apigateway
        self.aws_lambda_client.delete_function(FunctionName=self.lambda_ok)

        # request masking
        masking = self.get_element("class_name", "Masking")
        action = self.get_element("id", "masking")
        result_id = action.get_attribute("action").split("/")[-1]
        masking.click()

        # recreate lambda function
        with open(self.lambda_zipcode, "rb") as code:
            data = code.read()
            # ok
            self.aws_lambda_client.create_function(
                FunctionName=self.lambda_ok,
                Runtime="python3.6",
                Role="dummy",
                Handler="dummy_lambda.lambda_handler_ok",
                Code={"ZipFile" : data}
            )

        # redirect to image_list with error message
        h2 = self.get_element("tag_name", "h2")
        self.assertEqual(h2.text, "ImageList")

        message_list = self.get_element("class_name", "messages", single=False)
        self.assertIn(
            messages.MASKING_FAIL_CANNOT_REQUEST.format(self.lambda_url_ok),
            [m.text for m in message_list],
        )

        

    def test_masking_4(self):
        """
        test_masking_4 : select the transfer image on result_list page,
        and move to masking page.
        once back to image_list page and again move to masking page,
        no need to call apigateway
        """
        self.setUp_driver()

        # register one transfer result
        self.exec_transfer(self.content, self.style)
        self.driver.get(self.live_server_url + "/result_list/0/")

        masking = self.get_element("class_name", "Masking")
        masking.click()


        h2 = self.get_element("tag_name", "h2")
        self.assertEqual(h2.text, "Masking")

        trasnfer_list = self.get_element("class_name", "TransferData", single=False)
        self.assertEqual(len(trasnfer_list), 2)

        # back to image_list page
        self.driver.get(self.live_server_url + "/result_list/0/")
        h2 = self.get_element("tag_name", "h2")
        self.assertEqual(h2.text, "ResultList")


        # temporarily delete lambda function associated with apigateway
        self.aws_lambda_client.delete_function(FunctionName=self.lambda_ok)

        # request masking
        masking = self.get_element("class_name", "Masking")
        action = self.get_element("id", "masking")
        result_id = action.get_attribute("action").split("/")[-1]
        masking.click()

        # recreate lambda function
        with open(self.lambda_zipcode, "rb") as code:
            data = code.read()
            # ok
            self.aws_lambda_client.create_function(
                FunctionName=self.lambda_ok,
                Runtime="python3.6",
                Role="dummy",
                Handler="dummy_lambda.lambda_handler_ok",
                Code={"ZipFile" : data}
            )

        # if the masking page has been already visited,
        # no need to call masking api.
        h2 = self.get_element("tag_name", "h2")
        self.assertEqual(h2.text, "Masking")

        trasnfer_list = self.get_element("class_name", "TransferData", single=False)
        self.assertEqual(len(trasnfer_list), 2)
