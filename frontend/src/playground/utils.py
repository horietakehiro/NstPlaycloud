from django.conf import settings
import boto3

def get_masking_api_url():
    try:
        endpoint = settings.AWS_APIGW_ENDPOINT_URL
        # get rest_api_id
        client = boto3.client("apigateway", endpoint_url=endpoint, region_name=settings.AWS_REGION)
        res = client.get_rest_apis()
        for item in res["items"]:
            if item["name"] == settings.AWS_APIGW_RESTAPI_NAME:
                rest_api_id = item["id"]
                break

        # create url for prod
        # AWS_APIGW_URL4PROD="https://{rest_api_id}.execute-api.{region}.amazonaws.com/default/{path_name}"
        # AWS_APIGW_URL4TEST="http://{endpoint}restapis/{restapi_id}/default/_user_request_/{path_name}"
        if endpoint is None:
            url = settings.AWS_APIGW_URL4PROD
            url = url.format(
                rest_api_id=rest_api_id,
                region=settings.AWS_REGION,
                path_name="masking",
            )
        else:
            url = settings.AWS_APIGW_URL4TEST
            url = url.format(
                endpoint=endpoint, 
                rest_api_id=rest_api_id,
                path_name="masking"
            )

        return url
    except:
        return None