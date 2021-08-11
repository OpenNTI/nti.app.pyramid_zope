=========
 Changes
=========


0.0.3 (unreleased)
==================

- Require ``zope.principalregistry`` and configure it from
  ``configure.zcml``. This packge needs the unauthenticated principal
  utility it provides.

- Require ``zope.publisher`` and configure it from ``configure.zcml``.
  This is needed for language negotiation based on requests.

- Add support for I18N.

- Add support for Python 3.9. 3.10 is expected to work once zodbpickle
  is released with support for 3.10.

0.0.2 (2020-01-02)
==================

- Add ``nti.app.pyramid_zope.traversal.ZopeResourceTreeTraverser``, a
  Pyramid ``ITraverser`` that uses the ``zope.traversing`` machinery,
  including path adapters and namespaces.

- Make ``configure.zcml`` register the standard traversing adapters
  which accept a Pyramid ``IRequest`` object. This goes hand-in-hand
  with using the ``ZopeResourceTreeTraverser``. These are the same
  namespaces that would be registered by ``zope.traversing`` for the
  Zope request (with the exception of the ``attribute`` namespace).


0.0.1 (2020-01-01)
==================

- Initial release.
