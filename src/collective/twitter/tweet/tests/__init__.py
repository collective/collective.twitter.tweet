# -*- coding:utf-8 -*-

import twitter
from urllib2 import HTTPError, URLError

class PersistentTwitter(object):
    """
    This is basically a persistent object that we will use
    to store and get which account was used, and what messages
    were sent, in order to be able to test it
    """

    def __init__(self):
        self.consumer_key = ""
        self.consumer_secret = ""
        self.oauth_token = ""
        self.oauth_token_secret = ""
        self.message = ""

    def storeCredentials(self,
                         consumer_key, 
                         consumer_secret,
                         access_token_key,
                         access_token_secret):

        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.oauth_token = access_token_key
        self.oauth_token_secret = access_token_secret

    def storeMessage(self, text):
        self.message = text

    def getCredentials(self):
        return (self.consumer_key, 
                self.consumer_secret, 
                self.oauth_token, 
                self.oauth_token_secret)

    def getMessage(self):
        return self.message

    def resetCredentials(self):        
        self.consumer_key = ""
        self.consumer_secret = ""
        self.oauth_token = ""
        self.oauth_token_secret = ""

    def resetMessage(self):
        self.message = ""



persistentTwitter = PersistentTwitter()


class Api(object):

    def __init__(self, 
                 consumer_key, 
                 consumer_secret,
                 access_token_key,
                 access_token_secret):

        persistentTwitter.storeCredentials(consumer_key, 
                                           consumer_secret,
                                           access_token_key,
                                           access_token_secret)

        

    def PostUpdate(self, text):

        if 'URLError' in text:
            raise URLError("URL Error")

        if 'Timeout' in text:
            raise HTTPError("http://none.com", 408, "Timeout", {}, None)

        elif 'Error' in text:
            raise twitter.TwitterError("Internal Error")

        else:
            persistentTwitter.storeMessage(text)


twitter.Api = Api
