.. -*- coding: utf-8 -*-

===========================
pyramid_services_sqlalchemy
===========================

SQLAlchemy factories for `pyramid_services`.


This module provides removing `SQLAlchemy`'s boiler plates
from your `pyramid` application codes.


In your ``pastedeploy.ini``::

  sqlalchemy.url = ENGINE://DBUSER:PASSWORD@DBHOST/DBNAME


In your application factory::

  config.include('pyramid_services_sqlalchemy')


In your views::

  from pyramid_services_sqlalchemy import get_tm_session

  def aview(request):
      db = get_tm_session(request)


or you can use ``request.find_service``::

  from pyramid_services_sqlalchemy import IDBSession

  def aview(request):
      db = request.find_service(IDBSession)


If you want to use multiple connections, ``pastedeploy.ini``::

  sqlalchemy.names = readonly readwrite
  sqlalchemy.readonly.url = ENGINE://READ_DBUSER:PASSWORD@DBHOST/DBNAME
  sqlalchemy.readwrite.url = ENGINE://WRITE_DBUSER:PASSWORD@DBHOST/DBNAME


and in your views::

  from pyramid_services_sqlalchemy import get_tm_session

  def aview(request):
      db = get_tm_session(request, name='readonly')

  def a_write_view(request):
      db = get_tm_session(request, name='readwrite')
