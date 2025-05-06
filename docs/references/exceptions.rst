.. currentmodule:: twitchio


Exceptions
----------

.. autoclass:: twitchio.TwitchioException()

.. autoclass:: twitchio.HTTPException()
    :members:

.. autoclass:: twitchio.InvalidTokenException()
    :members:

.. autoclass:: twitchio.MessageRejectedError()
    :members:

.. autoclass:: twitchio.MissingConduit()
    :members:


Exception Hierarchy
~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`TwitchioException`
        - :exc:`HTTPException`
            - :exc:`InvalidTokenException`
        - :exc:`MessageRejectedError`
        - :exc:`MissingConduit`