import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import requests
from bs4 import BeautifulSoup as bs
import re
from time import sleep

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

page_token = None

df = pd.DataFrame(columns=['title', 'video count', 'date', 'total views', 'url'])

#enter all the searches
search_query_list = ['sample one', 'sample two']

search_query = '|'.join(search_query_list)

while True:
    request = youtube.search().list(
            part="snippet",
            q=search_query,
            type="channel",
            maxResults=50,
            pageToken=page_token
        )

    response = request.execute()
    
    items = response['items']

    for item in items:
        try:
            channel_id = item['id']['channelId']

            about_url = f'https://www.youtube.com/channel/{channel_id}/about'
            req = requests.get(about_url)
            text = req.text

            #account date
            date = ''
            try:
                date_expression =  re.findall(r'"joinedDateText":{"runs":\[{"text":"Joined "},{"text":".*?"}\]}', text)
                date = date_expression[0].replace('"joinedDateText":{"runs":[{"text":"Joined "},{"text":"','')
                date = date.replace('"}]}','')
            except:
                pass

            #video count
            video_count=''
            try:
                video_count_expression = re.findall(r'"videosCountText":{"runs":\[{"text":".*?video', text)
                video_count = video_count_expression[0].replace('"videosCountText":{"runs":[{"text":"','')
                video_count = video_count.replace('"},{"text":" video','')
                video_count = video_count.replace(' video','')
            except:
                pass

            #channel title
            title = ''
            try:
                title_expression = re.findall(r'"channelMetadataRenderer":{"title":".*?"', text)
                title = title_expression[0].replace('"channelMetadataRenderer":{"title":"','')
                title = title.replace('"','')
            except:
                pass

            # print(title)

            total_views = ''
            try:
                total_view_expression = re.findall(r'viewCountText":{"simpleText":.*?views', text)
                total_views = total_view_expression[0].replace('viewCountText":{"simpleText":"','')
                total_views = total_views.replace('views','')
            except:
                pass

            # print(total_views)

            dic = {
                'title':title,
                'video count':video_count,
                'date':date, 
                'total views':total_views,
                'url':about_url}
            
            df = df.append(dic,ignore_index=True)
        except Exception as e:
            print(e)

    if 'nextPageToken' in response:
        page_token = response['nextPageToken']
    else:
        break

    sleep(2)

df.to_csv('output.csv')

print()