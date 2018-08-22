# 8/15/18 - burnsca@amazon.com
# A lambda function to respond to  a Box (box.com) skill event and kick off a SageMaker training process
# A sample event payload from Box is at end of this .py file

from __future__ import print_function
import boxsdk
import requests
import boto3
import logging
import json
import io
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    logger.info("Extracting BoxSkill payload-parameters from the event object")
    skill = event['skill']['id']
    if skill is None:
        logger.error("Skill-Id not found in the parameters")
        skill = "not_found"  # Not a fatal error

    write_token = event['token']['write']['access_token']
    if write_token is None:
        logger.error("Write access token not found in the parameters")
        write_token = "not_found" # Not a fatal error

    read_token = event['token']['read']['access_token']
    if read_token is None:
        logger.error("Read access token not found in the parameters - Fatal Error")
        read_token = "not_found"  # Fatal error - no way to stream the box file to s3 without this.
        # TODO exit gracefully

    file_id = event['source']['id']
    if file_id is None:
        logger.error("File ID not found in the parameters - Fatal Error")
        file_id = "not_found"  # Fatal error - no way to stream the box file to s3 without this.
        # TODO - exit gracefully

    file_name = event['source']['name']
    if file_name is None:
        logger.error("File Name not found in the parameters - Fatal Error")
        file_name = "not_found"  # Fatal error - no way to stream the box file to s2 without this.
        # TODO - exit gracefully

    # Get the file info so we can see if this Lambda function has sufficient time to download it
    url = 'https://api.box.com/2.0/files/' + file_id + '?access_token=' + read_token
    r = requests.get(url)
    json_ = json.loads(r.content)
    file_Size = json_['size']
    logger.info('Filesize = ' + str(file_Size) + ' bytes')

    # TODO
    # Write some code to determine if the file can be streamed to S3 within 4+ minutes - if not, move to chunky upload

    start = time.time()
    # Stream the newly found file on Box to S3
    logger.info("Streaming target file(" + file_name + ") from api.box.com")
    url = 'https://api.box.com/2.0/files/' + file_id + '/content?access_token=' + read_token
    r = requests.get(url)

    buffer = io.BytesIO()
    buffer.write(r.content)
    # reset memory stream back to the beginning of the file
    buffer.seek(0)

    # upload the file from box to S3
    logger.info("Writing file stream to S3...")
    s3 = boto3.resource('s3')

    try:
        s3.Object('box2sagemaker', "train/" + file_name).upload_fileobj(buffer)
        buffer.close()

    except Exception as err:
        logger.error("Unable to stream from Box to S3! " + err)

    stop = time.time()
    # log a few details from the transfer

    xferTime = stop - start # in seconds
    mb = file_Size / 1000000  # convert file size to MB
    xferRate = mb / float(xferTime)

    logger.info("FileStreamTime: {}".format(xferTime))
    logger.info("TransferRate: {} (mb/sec)".format(xferRate))

    parse_result = '{"skill-id": ' + skill + ', "write_token": ' + write_token + ', \
                    "read_token": ' + read_token + ', "file_id": ' + file_id + ', "file_name": ' + file_name + ', \
                    "StreamTransferTime": ' + str(xferTime) + ', "StreamTransferRate": ' + str(xferRate) + '}'

    # NOTE!!!!  This writes Write and Read tokens to CloudWatch - don't do this!!!  This is only for development
    # Read the above ^^ note ^^ that you probably skipped over!!
    logger.info("Event parsed. Results = " + parse_result)

    # Return a response suitable for the API Gateway
    return parse_result


# Sample Box event payload
#  {
#    "type":"skill_invocation",
#    "skill":{
#       "type":"app",
#       "id":"32066",
#       "name":"Manish Test Skill",
#       "client_id":"dgsn72unoymjhy8xqluherhimo2tw1hk"
#    },
#    "token":{
#       "write":{
#          "access_token":"REDACTED",
#          "expires_in":1519256994,
#          "restricted_to":"[{\"scope\":\"gcm\"},{\"scope\":\"item_upload\",\"object_id\":6399767106,\"object_type\":\"file\"}]",
#          "token_type":"bearer"
#       },
#       "read":{
#          "access_token":"REDACTED",
#          "expires_in":1519256994,
#          "restricted_to":"[{\"scope\":\"gcm\"},{\"scope\":\"item_read\",\"object_id\":6399767106,\"object_type\":\"file\"}]",
#          "token_type":"bearer"
#       }
#    },
#    "id":"11111111-2222-442f-9961-d056f0b68594",
#    "created_at":"2017-12-27T19:19:34-08:00",
#    "trigger":"FILE_CONTENT",
#    "enterprise":{
#       "type":"enterprise",
#       "id":"1635603",
#       "name":"Enterprise for Skill Tester"
#    },
#    "source":{
#       "type":"file",
#       "id":"6399767106",
#       "sequence_id":"1",
#       "name":"test_manish.png",
#       "file_version":{
#          "id":"25583725616"
#       },
#       "parent":{
#          "type":"folder",
#          "id":"6471024962",
#          "sequence_id":null,
#          "etag":null,
#          "name":"Manish Test"
#       },
#       "owner_enterprise_id":"1635603"
#    },
#    "event":{
#       "event_id":"11111111-2222-442f-9961-d056f0b68594",
#       "event_type":"ITEM_UPLOAD",
#       "created_at":"2017-12-27T19:19:34-08:00",
#       "created_by":{
#          "type":"user",
#          "id":"4295234688"
#       },
#       "source":{
#          "type":"file",
#          "id":"6399767106",
#          "sequence_id":"1",
#          "name":"test_manish.png",
#          "file_version":{
#             "id":"25583725616"
#          },
#          "parent":{
#             "type":"folder",
#             "id":"6471024962",
#             "sequence_id":null,
#             "etag":null,
#             "name":"Manish Test"
#          },
#          "owner_enterprise_id":"1635603"
#       }
#    },
#    "parameters":{
#
#    }
# }
