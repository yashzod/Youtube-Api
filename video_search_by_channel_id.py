import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
import re
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# create and download OAuth 2.0 Client IDs credentials json file from "https://console.cloud.google.com/apis/credentials"
credentials_file = 'cred.json'
token_file = 'token.json'

creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
if os.path.exists(token_file):
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(token_file, 'w') as token:
        token.write(creds.to_json())


api_service_name = "youtube"
api_version = "v3"

youtube = build(
        api_service_name, api_version, credentials=creds)

# enter channel ids here.
ch_ids = ['U_sample_channel_id']

end = len(ch_ids)

df = pd.DataFrame()

repeat_df = pd.DataFrame()

counter = 0


ch = 0
page_token=None

while True:
    ch_id=ch_ids[ch]
    request = youtube.activities().list(
        part="contentDetails,snippet",
        channelId=ch_id,
        maxResults=50,
        pageToken=page_token
    )
    response = request.execute()

    items = response['items']
    print(counter,len(items),response['pageInfo']['totalResults'],ch_id)
    counter+=1

    if response['pageInfo']['totalResults']>=110:
        d = {'ch_id':ch_id}
        repeat_df = repeat_df.append(d, ignore_index=True)
        print(ch_id,'added')
        ch+=1
        continue

    for item in items:
        channel_name = item['snippet']['channelTitle']

        if 'upload' in item['contentDetails']:
            video_id = item['contentDetails']['upload']['videoId']
        else:
            continue

        url = f'https://www.youtube.com/watch?v={video_id}'
        req = requests.get(url)
        text = req.text

        #length
        video_length = ''
        try:
            video_length_expression = re.findall(r'"lengthSeconds":".*?"', text)
            video_length = video_length_expression[0].replace('"lengthSeconds":"','')
            video_length = video_length.replace('"','')
        except:
            pass

        #title
        title_expression=''
        try:
            title_expression = re.findall(r'"title":{"simpleText":".*?"}', text)
            title = title_expression[0].replace('"title":{"simpleText":"','')
            title = title.replace('"}','')
        except:
            pass

        views = ''
        try:
            views_expression = re.findall(r'"viewCount":{"videoViewCountRenderer":{"viewCount":{"simpleText":".*? views"}', text)
            views = views_expression[0].replace('"viewCount":{"videoViewCountRenderer":{"viewCount":{"simpleText":"','')
            views = views.replace(' views"}','')
            if len(views)>30:
                views='1'
        except:
            pass

        #publish date
        publish_date=''
        try:
            publish_date_expression = re.findall(r'"publishDate":{"simpleText":".*?"}', text)
            publish_date = publish_date_expression[0].replace('"publishDate":{"simpleText":"','')
            publish_date = publish_date.replace('"}','')
        except:
            pass

        #owner
        owner=''
        try:
            owner_expression =  re.findall(r'"ownerProfileUrl":"http://www.youtube.com/.*?"', text)
            owner = owner_expression[0].replace('"ownerProfileUrl":"http://www.youtube.com/','')
            owner = owner.replace('"','')
        except:
            pass

        dic = {
            'channel id':ch_id,
            'channel owner': owner,
            'Account name': channel_name,
            'Name of video': title,
            'views':views,
            'publish date': publish_date,
            'video length':video_length,
            'url':url 
        }

        df = df.append(dic, ignore_index=True)
    
    if 'nextPageToken' in response:
        page_token = response['nextPageToken']
    else:
        ch+=1
        page_token=None
    
    if ch>=end:
        break
    

df.to_csv('videos_output.csv')

repeat_df.to_csv('repeat_test1.csv')

print()