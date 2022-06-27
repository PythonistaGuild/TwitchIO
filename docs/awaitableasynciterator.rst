:orphan:

.. _aai:

The Awaitable Async Iterator
=============================

.. versionadded:: 3.0

The Awaitable Async Iterator (referred to as AAI), is a new method of returning paginatable endpoint data.
When you see this object returned by an API call, it means the endpoint could return too much data for one request,
so multiple requests need to be made in order to fetch all the info.

If you're curious why we've introduced this object, keep reading.
If you're just looking for info on how to use it, jump down to :ref:`aai_usage`.

Why change?
------------

Previously, the library would make all these requests implicitly, so you never saw these extra requests being made.
However, there is a downside to this, in that you might not *need* all of those extra requests.
Say you're going through a list of 800 followers to find a single person, who's number 190 in the list of 800.
At 100 users per request, that's 6 extra requests that were made by the lib which didn't have to be made.
The AAI gives you precise control over when to stop making API requests, so that once you find that 190th person,
you can cut off the lib before it requests more users, thus saving 6 requests.

Why not a plain Async Iterator?
--------------------------------

When designing the new HTTP system for 3.0, it became clear that precise control over pagination was not something
everyone wanted, or in most cases, needed. So to accomadate for everyone who didn't want/need it, we wanted to add
the option to ``await`` the API calls as well, which would make it easier to retrieve items the old way. The solution?
Add both, by creating the AAI. Now, developers who just want one API call's worth of items can get that via ``await``,
without getting in the way of developers who want fine grain control over when to stop paginating.

.. _aai_usage:

Usage
------

The AAI can be used in two ways: an awaitable object, or an async iterator.
All of the examples shown below include an implicit :class:`twitchio.Client` as ``client`, and :class:`twitchio.PartialUser` as ``user``.
They also assume you have a valid token with the correct scope(s) to make the calls. For more information on handling tokens, see :ref:`tokens`.

Usage as an awaitable object
+++++++++++++++++++++++++++++

.. code-block:: python

    data = await user.fetch_followers()

.. code-block:: python

    data = await user.fetch_subscribers()


Usage as an async iterator
+++++++++++++++++++++++++++

Basic usage:

.. code-block:: python

    data = []
    async for follower in user.fetch_followers():
        data.append(follower)

    # or, in one line

    data = [follower async for follower in user.fetch_followers()]

Filtering out names:

.. code-block:: python

    data = []
    async for follower in user.fetch_followers():
        if follower.name.lower() != "chillymosh":
            data.append(follower)

    # or, in one line

    data = [follower async for follower in user.fetch_followers() if follower.name != "chillymosh"]

Stopping iteration after a name is found:

.. code-block:: python

    chilly = await client.fetch_user("chillymosh")
    found_chilly = False

    async for follower in user.fetch_followers():
        if follower == chilly:
            found_chilly = True
            break

    if found_chilly:
        print("Chillymosh is following!")
    else:
        print("Chillymosh isn't following :(")

