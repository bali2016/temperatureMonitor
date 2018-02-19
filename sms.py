#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import urllib
import httplib
import socket
import ssl
from twilio.rest import Client


def xinShi_sms(content, mobile):
    smsClient = None
    try:
        params = urllib.urlencode({
                'name': '18951518810',
                'pwd': '3ED2E4BCE3AC0D70511D823F877C',
                'content': content,
                'mobile': mobile,
                'stime': '',
                'sign': '',
                'type': 'pt',
                'extno': ''
            })
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
        smsClient = httplib.HTTPConnection('web.1xinxi.cn', 80, timeout=10)
        smsClient.request('POST', '/asmx/smsservice.aspx', params, headers)
        response = smsClient.getresponse()
        print response.status
        print response.reason
        print response.read()
        print response.getheaders()
    except Exception, e:
        print e
    finally:
        if smsClient:
            smsClient.close()

def xinShi_sms2(content, mobile):
    httpsConn = None
    try:
        params = urllib.urlencode({
                'name': '18951518810',
                'pwd': '3ED2E4BCE3AC0D70511D823F877C',
                'content': content,
                'mobile': mobile,
                'stime': '',
                'sign': '',
                'type': 'pt',
                'extno': ''
            })
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
        httpsConn = httplib.HTTPSConnection('web.1xinxi.cn', timeout=10)
        httpsConn.request('POST', '/asmx/smsservice.aspx', params, headers)
        response = httpsConn.getresponse()
        print response.status
        print response.reason
        print response.read()
        print response.getheaders()
    except Exception, e:
        print e
    finally:
        if httpsConn:
            httpsConn.close()


def twilio_sms(content, mobile):
    # Your Account SID from twilio.com/console
    account_sid = "AC8ed478f605387c1841ca38faf369a22f"
    # Your Auth Token from twilio.com/console
    auth_token = "97b36bcbab591cbebc9225af0f239753"

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        to="+86"+mobile,
        from_="+19083865264",
        body=content)

    print(message.sid)

if __name__ == '__main__':
    SMSContext = '亲爱的爸爸，本宝宝现在尿了，快来换尿布。【涵涵】'
    SMSTargets = '18951518810'
    xinShi_sms2(content=SMSContext, mobile=SMSTargets)
    # twilio_sms(content=SMSContext, mobile=SMSTargets)