# -*- coding:utf-8 -*-

import unittest2 as unittest

from zope.component import getMultiAdapter
from zope.component import getUtility

from zope.component.interfaces import IObjectEvent

from zope.interface import implements

from plone.app.contentrules.rule import Rule

from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles

from plone.contentrules.engine.interfaces import IRuleStorage

from plone.contentrules.rule.interfaces import IRuleAction
from plone.contentrules.rule.interfaces import IExecutable

from plone.registry.interfaces import IRegistry

from Products.statusmessages.interfaces import IStatusMessage

from collective.twitter.tweet.content import Action
from collective.twitter.tweet.content import ActionAddForm
from collective.twitter.tweet.content import ActionEditForm

from collective.twitter.tweet.interfaces import ValidAccounts

from collective.twitter.tweet.testing import INTEGRATION_TESTING

from collective.twitter.tweet.tests import persistentTwitter


class DummyEvent(object):
    implements(IObjectEvent)

    def __init__(self, object):
        self.object = object


class TestTweetAction(unittest.TestCase):

    layer = INTEGRATION_TESTING

    def _loadAccounts(self, number=1):

        # Let's load two accounts to the accounts list
        accounts = {}
        for i in range(number):
            accounts['account%s'%i] = {
                'consumer_key': 'consumer_key%s'%i, 
                'consumer_secret': 'consumer_secret%s'%i,
                'oauth_token': 'access_token_key%s'%i,
                'oauth_token_secret': 'access_token_secret%s'%i,
            }

        registry = getUtility(IRegistry)
        registry['collective.twitter.accounts'] = accounts

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.invokeFactory('Folder', 'folder')
        self.folder = self.portal['folder']
        self.folder.invokeFactory('Document', 'doc1', title="Doc 1")
        self.folder.invokeFactory('Document', 'longtitle', title="A"*200)
        self.folder.invokeFactory('Document', 'timeout', title="Timeout")
        self.folder.invokeFactory('Document', 'error', title="Error")
        self.folder.invokeFactory('Document', 'urlerror', title="URLError")

        persistentTwitter.resetCredentials()
        persistentTwitter.resetMessage()


    def testRegistered(self):
        element = getUtility(IRuleAction,
                             name='collective.twitter.tweet.TweetContent')
        self.assertEquals('collective.twitter.tweet.TweetContent',
                          element.addview)
        self.assertEquals('edit', element.editview)
        self.assertEquals(None, element.for_)
        self.assertEquals(IObjectEvent, element.event)

    def testInvokeAddView(self):
        self._loadAccounts(2)
        element = getUtility(IRuleAction,
                             name='collective.twitter.tweet.TweetContent')
        storage = getUtility(IRuleStorage)
        storage[u'tweet'] = Rule()

        rule = self.portal.restrictedTraverse('++rule++tweet')

        adding = getMultiAdapter((rule, self.request), name='+action')
        addview = getMultiAdapter((adding, self.request), name=element.addview)

        addview.createAndAdd(data={'tw_account': 'first-valid-account'})

        e = rule.actions[0]
        self.failUnless(isinstance(e, Action))
        self.assertEquals(e.tw_account, 'first-valid-account')
        self.assertEquals(e.different_host, '')

        # XXX: Figure out how to render the view
        #action=collective.twitter.tweet.TweetContent&form.button.AddAction=Agregar
        # import pdb;pdb.set_trace()
        # self.request.form['action'] = "collective.twitter.tweet.TweetContent"
        # self.request.form['form.button.AddAction'] = "Add"
        # addview()

    def testInvokeEditView(self):
        element = getUtility(IRuleAction,
                             name='collective.twitter.tweet.TweetContent')
        e = Action()
        editview = getMultiAdapter((e, self.request), name=element.editview)
        self.failUnless(isinstance(editview, ActionEditForm))
        # import pdb;pdb.set_trace()
        # editview()

    def testExecute(self):
        e = Action()
        e.tw_account = 'first-valid-account'
        executor = getMultiAdapter((self.folder, e, DummyEvent(self.folder.doc1)),
                             IExecutable)
        self.assertEquals(True, executor())

    def testFirstValidAccount(self):
        self._loadAccounts(2)
        e = Action()
        e.tw_account = 'first-valid-account'
        executor = getMultiAdapter((self.folder, e, DummyEvent(self.folder.doc1)),
                                   IExecutable)

        self.assertEquals(True, executor())
        self.assertEquals(persistentTwitter.getCredentials(),
                          ('consumer_key1', 
                           'consumer_secret1', 
                           'access_token_key1', 
                           'access_token_secret1'))

        self.assertTrue('Doc 1\n' in persistentTwitter.getMessage())

        status_msg = IStatusMessage(self.request).showStatusMessages()[0].message
        self.assertTrue(u'Tweet sent: Doc 1\n' in status_msg)

    def testSpecificAccount(self):
        self._loadAccounts(2)
        e = Action()
        e.tw_account = 'account0'
        executor = getMultiAdapter((self.folder, e, DummyEvent(self.folder.doc1)),
                                   IExecutable)

        self.assertEquals(True, executor())

        self.assertEquals(persistentTwitter.getCredentials(),
                          ('consumer_key0', 
                           'consumer_secret0', 
                           'access_token_key0', 
                           'access_token_secret0'))

        self.assertTrue('Doc 1\n' in persistentTwitter.getMessage())

        status_msg = IStatusMessage(self.request).showStatusMessages()[0].message
        self.assertTrue(u'Tweet sent: Doc 1\n' in status_msg)

    def testLongTitle(self):
        self._loadAccounts(2)
        e = Action()
        e.tw_account = 'first-valid-account'
        executor = getMultiAdapter((self.folder, e, DummyEvent(self.folder.longtitle)),
                                   IExecutable)

        self.assertEquals(True, executor())
        self.assertTrue(len(persistentTwitter.getMessage()) < 140)

        status_msg = IStatusMessage(self.request).showStatusMessages()[0].message
        self.assertTrue(u'Tweet sent: ' in status_msg)

    def testTimeout(self):
        self._loadAccounts(2)
        e = Action()
        e.tw_account = 'first-valid-account'
        executor = getMultiAdapter((self.folder, e, DummyEvent(self.folder.timeout)),
                                   IExecutable)

        self.assertEquals(True, executor())

        status_msg = IStatusMessage(self.request).showStatusMessages()[0].message
        self.assertEquals(status_msg,
                          (u'There was an error while sending the tweet: '
                            'HTTP Error 408: Timeout'))

    def testError(self):
        self._loadAccounts(2)
        e = Action()
        e.tw_account = 'first-valid-account'
        executor = getMultiAdapter((self.folder, e, DummyEvent(self.folder.error)),
                                   IExecutable)

        self.assertEquals(True, executor())

        status_msg = IStatusMessage(self.request).showStatusMessages()[0].message
        self.assertEquals(status_msg,
                          (u'There was an error while sending the tweet: '
                            'Internal Error'))

    def testURLError(self):
        self._loadAccounts(2)
        e = Action()
        e.tw_account = 'first-valid-account'
        executor = getMultiAdapter((self.folder, e, DummyEvent(self.folder.urlerror)),
                                   IExecutable)

        self.assertEquals(True, executor())

        status_msg = IStatusMessage(self.request).showStatusMessages()[0].message
        self.assertEquals(status_msg,
                          (u'There was an error while sending the tweet: '
                            '<urlopen error URL Error>'))

    def testInvalidAccount(self):
        e = Action()
        e.tw_account = 'account'
        executor = getMultiAdapter((self.folder, e, DummyEvent(self.folder.error)),
                                   IExecutable)

        self.assertEquals(True, executor())

        self.assertEquals(persistentTwitter.getCredentials(),
                          ('', '', '', ''))

        self.assertTrue('' in persistentTwitter.getMessage())

        status_msg = IStatusMessage(self.request).showStatusMessages()[0].message
        self.assertEquals(status_msg,
                          (u"Could not publish to twitter, seems the account "
                            "account was removed from the list of authorized "
                            "accounts for this site."))

    def testDifferentHost(self):
        self._loadAccounts(2)
        e = Action()
        e.tw_account = 'first-valid-account'
        e.different_host = 'http://www.google.com'

        executor = getMultiAdapter((self.folder, e, DummyEvent(self.folder.doc1)),
                                   IExecutable)

        self.assertEquals(True, executor())

        status_msg = IStatusMessage(self.request).showStatusMessages()[0].message
        self.assertTrue(u'Tweet sent: Doc 1\n' in status_msg)

    def testAccountsVocabulary(self):
        self._loadAccounts(2)
        accounts = ValidAccounts(self.portal)

        self.assertEquals([i.token for i in accounts._terms], 
                          ['first-valid-account', 'account1', 'account0'])

        
def test_suite():
     return unittest.defaultTestLoader.loadTestsFromName(__name__)
