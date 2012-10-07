# -*- coding: utf-8 -*-

import twitter

from urllib import urlencode
from urllib2 import urlopen, HTTPError, URLError

from Acquisition import aq_inner

from OFS.SimpleItem import SimpleItem

from zope.interface import Interface
from zope.interface import implements

from zope.component import adapts

from zope.formlib import form

from zope.component import getUtility

from zope.component.interfaces import IObjectEvent

from plone.app.contentrules.browser.formhelper import AddForm
from plone.app.contentrules.browser.formhelper import EditForm

from plone.app.uuid.utils import uuidToObject

from plone.contentrules.rule.interfaces import IExecutable 
from plone.contentrules.rule.interfaces import IRuleElementData

from plone.registry.interfaces import IRegistry

from plone.uuid.interfaces import IUUID

from Products.CMFCore.utils import getToolByName

from Products.statusmessages.interfaces import IStatusMessage

from collective.twitter.tweet.interfaces import ITweetContent
from collective.twitter.tweet import _


def getTinyURL(url):
    """ returns shotened url or None """  
    TINYURL = 'http://tinyurl.com/api-create.php'
    linkdata = urlencode(dict(url=url))
    link = None
    index = 0
    while not link and index < 10:
        # If the request fail, retry up to 10 times.
        try:
            link = urlopen( TINYURL, data=linkdata ).read().strip()
        except URLError:
            # there was an error
            link = None
            index += 1
    return link
                         

class Action(SimpleItem):
    """ 
    The actual persistent implementation of the action element.
    """
    
    implements(ITweetContent, IRuleElementData)
    
#    url_shortener = ""
    tw_account = ""   
    different_host = ""

    element = "collective.twitter.tweet.TweetContent"

    @property
    def summary(self):
        return _(u"Twitter account: ${tw_account}", mapping=dict(tw_account=self.tw_account))


class ActionExecutor(object):
    """ 
    The executor for this action
    """
    implements(IExecutable)
    adapts(Interface, ITweetContent, IObjectEvent)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        obj = aq_inner(self.event.object)

        uuid = IUUID(obj, None)
        # In a case where a previous action modified the object in any way
        if uuid:
            context = uuidToObject(uuid)
        else:
            # This should never happen, but just in case...
            context = obj

        request = context.REQUEST

        registry = getUtility(IRegistry)
        accounts = registry.get('collective.twitter.accounts', {})

        account = None
        key = self.element.tw_account

        if accounts:        
            if self.element.tw_account == 'first-valid-account':
                keys = accounts.keys()
                if keys:
                    key = keys[0]
                    account = accounts.get(key, {}) 
            else:
                account = accounts.get(key, {})

        if account:
            tw =  twitter.Api(
                    consumer_key = account.get('consumer_key'),
                    consumer_secret = account.get('consumer_secret'),
                    access_token_key = account.get('oauth_token'), 
                    access_token_secret = account.get('oauth_token_secret'),)
                              
            title = context.Title()

            url = None
            if self.element.different_host:
                if not self.element.different_host.endswith('/'):
                    self.element.different_host += '/'

                try:
                    portal_path = context.portal_url.getPortalObject().getPhysicalPath()
                    location = '/'.join(context.getPhysicalPath()[len(portal_path):])
                    url = self.element.different_host + location
                except:
                    return False

            else:
                url = context.absolute_url()

            # shortener = SHORTENER[self.element.url_shortener]
            url = getTinyURL(url)
            if url is None:
                return False
            
            text = "%s\n%s" % ( title[:140-(len(url)+2)], url )
    
            try:
                status = tw.PostUpdate(text)
                msg = _("Tweet sent: ${tweet}", mapping=dict(tweet=text))

            except (twitter.TwitterError, HTTPError, URLError), e:
                msg = _("There was an error while sending the tweet: "
                        "${error}", mapping=dict(error=str(e)))

            IStatusMessage(request).addStatusMessage(msg, "info")

            request.response.redirect(context.absolute_url())
            
        else:
            msg = _("Could not publish to twitter, seems the account "
                    "${account} was removed from the list of authorized "
                    "accounts for this site.", mapping=dict(account=key))

            IStatusMessage(request).addStatusMessage(msg, "info")

            request.response.redirect(context.absolute_url())
  
        return True

class ActionAddForm(AddForm):
    """
    The action's add form
    """

    form_fields = form.FormFields(ITweetContent)
    label = _(u"Tweet new content's title and url.")
    description = _(u"Send a tweet containing the content's title and a "
                     "shortened URL to it.")
    form_name = _(u"Select account")

    def create(self, data):
        c = Action()
        form.applyChanges(c, self.form_fields, data)
        return c
    
class ActionEditForm(EditForm):
    """An edit form for portal type conditions
    """

    form_fields = form.FormFields(ITweetContent)
    label = _(u"Tweet new content's title and url.")
    description = _(u"Send a tweet containing the content's title and a "
                     "shortened URL to it.")
    form_name = _(u"Select account")
 
