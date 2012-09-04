========================
collective.twitter.tweet
========================

.. contents:: Table of Contents

Overview
--------

This product provides a twitter action to be used with content rules.

Prerequisites
-------------

This product depends on `collective.twitter.accounts`_.

Usage
-----

Just add this product to your buildout, and you should get the action to be used in the content rules.
Optionaly, you can specify a separate URL to be used as the beginning of the link.

Example
-------

 - Go to the content rules, and add the "Tweet new content's title and url".
 - Select the account you want to use, or just choose "First valid account"
 - If you have a separate site for your public site, you can specify it in the "separate host" field.
   example: your public site is http://my-site.com/ and your editing one is
            http://another-host:8080/Plone and you want tweets to use the public host, specify it here.


.. _`collective.twitter.accounts`: http://pypi.python.org/pypi/collective.twitter.accounts
