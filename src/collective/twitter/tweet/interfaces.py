# -*- coding: utf-8 -*-

from zope import schema

from zope.component import getUtility

from zope.interface import Interface
from zope.interface import alsoProvides

from zope.schema.interfaces import IContextSourceBinder

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from plone.registry.interfaces import IRegistry

from collective.twitter.tweet import _


def ValidAccounts(context):
    registry = getUtility(IRegistry)
    accounts = registry.get('collective.twitter.accounts', None)
    
    terms = [ SimpleTerm(value='first-valid-account', 
                         token='first-valid-account', 
                         title=_('First Valid Account')) ]

    if accounts:
        terms += [ SimpleTerm(value=key, token=key, title=key) 
                                                for key in accounts.keys()]


    return SimpleVocabulary(terms)

alsoProvides(ValidAccounts, IContextSourceBinder)

class ITweetContent(Interface):
    """ Content tweet config """

   # url_shortener_vocabulary = SimpleVocabulary(["bitly", "tinyURL"])
   # url_shortener = schema.Choice(title=_(u'URL Shortener service'),
   #                               description=_(u"Choose the service used to "
   #                                              "shorten the URL"),
   #                               required=False,
   #                               vocabulary=url_shortener_vocabulary)
                            
    tw_account = schema.Choice(title=_(u'Twitter account'),
                               description=_(u"Choose a twitter account to "
                                              "use."),
                               required=True,
                               source=ValidAccounts)

    different_host = schema.TextLine(title=_(u'Separate host'),
                         description=_(u"Specify here a different host to "
                                        "use for the link. (make sure to "
                                        "include the protocol. ie. http://, "
                                        "https://, etc.)"),
                         required=False,)
