import json
import boto3
import os
import sys
import uuid
import time
from requests_aws4auth import AWS4Auth
import requests




def voice_trans(query):
		transcribe = boto3.client('transcribe')
		name = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()).replace(":", "-").replace(" ", "")
		
		transcribe.start_transcription_job(
		    TranscriptionJobName=time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()).replace(":", "-").replace(" ", ""),
		    Media={'MediaFileUri': "https://s3.amazonaws.com/hw2photo2/trans.mp3"},
		    MediaFormat='mp3',
		    LanguageCode='en-US'
		)
		while True:
		    status = transcribe.get_transcription_job(TranscriptionJobName=name)
		    if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
		        break
		    time.sleep(5)
	
		text = requests.get(status['TranscriptionJob']['Transcript']['TranscriptFileUri']).json()
		
		print("Transcripts: ", text)
	
		
		s3client = boto3.client('s3')
		response = s3client.delete_object(
		    Bucket='hw2photo2',
		    Key='trans.mp3'
		)
		
		s3client.put_object(Body=text["results"]['transcripts'][0]['transcript'], Bucket='hw2photo2', Key='trans.txt')
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Origin": "*"
			},
			'body': "transcribe done"
		} 
		
def voice_res():
		s3client = boto3.client('s3')
		data = s3client.get_object(Bucket='hw2photo2', Key='trans.txt')
		query = data.get('Body').read().decode('utf-8')
		print("Voice query: ", query)
		s3client.delete_object(
			Bucket='hw2photo2',
			Key='trans.txt'
		)
		return query
		
def get_image(image_list,slots):
	host ='https://search-photo-y2qgl4up2qpzkueddc3zmwsc34.us-east-1.es.amazonaws.com'
	headers = { "Content-Type": "application/json" }
	credentials = boto3.Session(region_name='us-east-1', aws_access_key_id='AKIAUWJUJTWY6PLDUMOT',aws_secret_access_key='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').get_credentials()
	awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', 'es',session_token=credentials.token)
	for i, tag in slots.items():
		if tag:
				url = host + '/' + 'photos'+ '/_search?q=' + tag.strip('.') 
				print("ES URL --- {}".format(url))
				es_response =requests.get(url, auth=awsauth, headers=headers).json()
				es_src = es_response['hits']['hits']
				print("ES HITS --- {}".format(json.dumps(es_src)))
				for photo in es_src:
					labels = [word.lower() for word in photo['_source']['labels']]
					if tag.strip('.') in labels:
						oKey = photo['_source']['objectKey']
						image_list.append('https://s3.amazonaws.com/hw2photo1/' + oKey)

	

def lambda_handler(event, context):
	# recieve from API Gateway
	print("EVENT --- {}".format(json.dumps(event)))
	
	headers = { "Content-Type": "application/json" }
	lex = boto3.client('lex-runtime')

	query = event["queryStringParameters"]["q"]
	print(query)
	if query == "voiceSearch":
		return voice_trans(query)
	
	if query == "voiceResult":
		query=voice_res()
	

	lex_response = lex.post_text(
		botName='Hwbot',
		botAlias='xuhn',
		userId='vincent',
		inputText=query
	)
	
	print("LEX RESPONSE --- {}".format(json.dumps(lex_response)))

	slots = lex_response['slots']
	img_list = []
	get_image(img_list,slots)
	
	print(img_list)
	if img_list:
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Origin": "*",
				'Content-Type': 'application/json'
			},
			'body': json.dumps(img_list)
		}
	else:
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Origin": "*",
				'Content-Type': 'application/json'
			},
			'body': json.dumps("No such photos.")
		}