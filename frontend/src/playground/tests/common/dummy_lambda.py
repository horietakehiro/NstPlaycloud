def lambda_handler_ok(event, context):

    return {"statusCode" : 200, "body" : "\"{\"ok\" : 0}\""}

def lambda_handler_ng(event, context):

    return {"statusCode" : 404, "body" : "\"{\"ng\" : 1}\""}

