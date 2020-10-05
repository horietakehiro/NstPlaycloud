from ..common.base import BaseTestCase
from unittest.mock import patch, Mock

from django.conf import settings
from playground import utils

class UtilsTestCase(BaseTestCase):

    def test_get_masking_api_url_1(self):
        """
        test_get_masking_api_url_1 : if during test,
        return the url for test env
        """
        url = utils.get_masking_api_url()

        self.assertEqual(
            url, self.lambda_url_ok
        )
        

    @patch("playground.utils.boto3")
    # @patch("playground.utils.settings.AWS_APIGW_ENDPOINT_URL")
    def test_get_masking_api_ur_2(self, boto_mock):
        """
        test_get_masking_api_ur_2 : if during prod,
        return the url for prod env
        """
        # tempolariry overwrite apigateway's endpoint url
        endpoint_back = settings.AWS_APIGW_ENDPOINT_URL
        settings.AWS_APIGW_ENDPOINT_URL = None

        client_mock = Mock(**{
            "get_rest_apis.return_value" : {"items" : [
                {"id" : self.rest_api_id, "name" : settings.AWS_APIGW_RESTAPI_NAME}
            ]}
        })

        boto_mock.client.return_value = client_mock

        prod_url = "https://{rest_api_id}.execute-api.{region}.amazonaws.com/Prod/{path_name}".format(
            rest_api_id=self.rest_api_id,
            region=settings.AWS_REGION,
            path_name="masking"
        )
        url = utils.get_masking_api_url()

        settings.AWS_APIGW_ENDPOINT_URL = endpoint_back

        self.assertEqual(
            url, prod_url,
        )



    @patch("playground.utils.boto3")
    def test_get_masking_api_ur_3(self, boto_mock):
        """
        test_get_masking_api_ur_3 : if cannot connect to apigateway,
        return None
        """

        client_mock = Mock(**{
            "get_rest_apis.side_effect" : Exception
        })

        boto_mock.client.return_value = client_mock

        url = utils.get_masking_api_url()

        self.assertIsNone(url)