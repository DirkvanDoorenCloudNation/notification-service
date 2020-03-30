import json
import boto3
import re
import urllib.parse
import os
client = boto3.client('sns')

TOPIC_ARN = os.environ["TOPIC_ARN"]                                                                                             #SNS Topic ARN

def correct_format(phone):
    print(" TEST ")
    print(phone[0:4])
    if(len(phone) > 9):
        # in case of 0612345678 and 0031612345678
        if(phone[0:2] == "06" and len(phone) == 10):
            phone = "+31{}".format(phone[1:])
        if(phone[0:4] == "0031" and len(phone) == 13):
            phone = "+{}".format(phone[2:])
    print ( phone)
    return phone
    
def lambda_handler(event, context):
    print(event['body'])
    print(event)
    if("pwd" in event['queryStringParameters']):
        pwd = event['queryStringParameters']['pwd']
        if(pwd != "#CHOOSE1SECUREPASSWORDHERE!"):
            return {
                'statusCode': 200,
                'body': json.dumps('incorrect request')
            }
        try:
            body = event['body']
            out = urllib.parse.unquote(body)                                                                                    #Parse body
            fields = out.split("&")
            fields_obj = {}
            for field in fields:                                                                                
                tmp = field.split("=")
                fields_obj[tmp[0]] = tmp[1]                                                                                     #Create a map
            print("this is out {}".format(out))
            item = {}
            if fields_obj['fields[email][value]'] and not re.match(r"[^@]+@[^@]+\.[^@]+", fields_obj['fields[email][value]']):  #Check if email is valid
                return "invalid email"
            
            item['email'] = fields_obj['fields[email][value]']                                                                  #use mapped values to retrieve email and phone number 
            item['phone'] = fields_obj['fields[phone][value]']
            item['phone'] = correct_format(item['phone'])
            if item['email']:
                response_email = client.subscribe(
                    TopicArn= TOPIC_ARN,
                    Protocol='email',
                    Endpoint=item['email'],
                    ReturnSubscriptionArn=False
                )
            if item['phone']:    
                response_phone = client.subscribe(
                    TopicArn=TOPIC_ARN,
                    Protocol='sms',
                    Endpoint=item['phone'],
                    ReturnSubscriptionArn=False
                )
                try:
                    client.publish(
                        PhoneNumber=item['phone'],
                        Message= f'Bedankt voor het subscriben',
                        MessageAttributes={
                        'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'CVD19Update'
                        }}                )
                    print(f"Successfuly sent to {item['phone']}")
                except:
                    print(f"FAILED TO SEND TO {item['phone']}")
            return {
                'statusCode': 200,
                'body': json.dumps('you have been subscribed')
            }
        except Exception as e:
            print(e)
            return {
                'statusCode': 200,
                'body': json.dumps('subscription was not succesful')
            }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('incorrect')
        }