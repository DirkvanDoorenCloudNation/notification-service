import boto3
import urllib3
import os
from bs4 import BeautifulSoup
# Define URL
url = 'https://www.rivm.nl/nieuws/actuele-informatie-over-coronavirus'                                          #your url of choice
# Set up http request maker thing
http = urllib3.PoolManager()
# S3 object to store the last call
BUCKET_NAME = os.environ['BUCKET_NAME']
TOPIC_ARN = os.environ["TOPIC_ARN"]

file_name = 'current-webpage.txt'
object_s3 = boto3.resource('s3') \
                 .Bucket(BUCKET_NAME) \
                 .Object(file_name)

# Connect to AWS Simple Notification Service
sns_client = boto3.client('sns')

def find_latest_post(page):
    soup = BeautifulSoup(page, features="html.parser")
    articles = soup.find("div", class_="container container-spacer-sm content nobg clearfix")                                   #hardcoded examples.
    dates = articles.find("span", class_="content-date-created")
    content_header = dates.parent.next_sibling.next_sibling.text
    content_header2 = articles.find_all("h2")
    print(content_header)
    print(content_header2[2].text)
    if content_header == content_header2[2].text:
        return content_header
    else:
        raise ValueError("Something is wrong with the page formatting")

def handler(event, context):
    # Ping website
    resp = http.request('POST',url)
    new_page = resp.data
    new_post_title = find_latest_post(new_page)

    # read in old results
    old_page = object_s3.get().get('Body').read()
    old_post_title = find_latest_post(old_page)

    if new_page == old_page:
        print("No new updates.")
    else:
        print("-- New Update --")

        try:
            # Try to send a text message
            sns_client.publish(
                TopicArn=TOPIC_ARN,
                Message= f'Nieuwe RIVM COVID19 update beschikbaar: "{new_post_title}".\nBekijk het bericht op {url}',
                Subject="RIVM COVID19 Update",
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                      'DataType': 'String',
                      'StringValue': 'CVD19Update'
                    }}
            )
            print(f"Successfuly sent to SNS")
        except Exception as e:
            print(f"FAILED TO SEND TO SNS due to error: {e}")

        # Write new data to S3
        object_s3.put(Body = new_page)
        print("Successfully wrote new data to S3")

    print("done")
    return None
