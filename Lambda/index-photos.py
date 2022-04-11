import json
import boto3
import time
import urllib3
from requests_aws4auth import AWS4Auth
import requests

def detect(bucket,file):
    client = boto3.client('rekognition')
    res = client.detect_labels(
        Image={
            'S3Object': {
                'Bucket': str(bucket),
                'Name': str(file)
            }
        },
        MaxLabels=10
    )
    print('Detected labels for ' + file)
    return res
    
def upload(image_obj):
    credentials = boto3.Session(region_name='us-east-1', aws_access_key_id='AKIAUWJUJTWY6PLDUMOT',
                                aws_secret_access_key='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').get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', 'es',
                       session_token=credentials.token)
    host ='https://search-photo-y2qgl4up2qpzkueddc3zmwsc34.us-east-1.es.amazonaws.com'
    headers = { "Content-Type": "application/json" }
    url = host + '/' + 'photos' + '/' + 'photo'
    return requests.post(url,auth=awsauth,data=json.dumps(image_obj), headers=headers)
    

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    print(event)
    label_list=[]
    
    for record in event['Records']:
        BUCKET = record['s3']['bucket']['name']
        FILE = record['s3']['object']['key']

    print('reading image: {} from s3 bucket {}'.format(FILE, BUCKET))
   
    response=detect(BUCKET,FILE)
    print('Detected labels for ' + FILE)
    
    for label in response['Labels']:
        label_list.append(label['Name'])
    
    ts = time.gmtime()
    created_time = time.strftime("%Y-%m-%dT%H:%M:%S", ts)
    
    image_obj = {
        'objectKey':FILE,
        'bucket':BUCKET,
        'createdTimestamp':created_time,
        'labels':label_list
    }
    
    req = upload(image_obj)
   
    print("Success: ", req.json())
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*",
            'Content-Type': 'application/json'
        },
        'body': json.dumps("Image labels have been successfully detected!")
    }

