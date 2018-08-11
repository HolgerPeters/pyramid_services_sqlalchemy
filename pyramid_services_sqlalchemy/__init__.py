# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from collections import namedtuple
from pyramid.settings import aslist
from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData
from sqlalchemy.orm import configure_mappers, sessionmaker
from zope.interface import Attribute, Interface, implementer
from zope.sqlalchemy import register


__version__ = '0.1.1'


# Interfaces

class IDBEngine(Interface):
    """
    marker for `sqlalchemy.engine.base.Engine`
    """


class IDBNames(Interface):
    """
    marker for dbnames
    """


class IDBSession(Interface):
    """
    marker for `sqlalchemy.orm.session.Session`
    """


class IDBSessionCreated(Interface):
    """
    db session created event

    :type name: str
    :type session: sqlalchemy.session.session
    """
    name = Attribute("created db session's name")
    session = Attribute("created db session")


class IDBSessionFactory(Interface):
    """
    marker for `sqlalchemy.orm.session.sessionmaker`
    """


# Implementations

DBSessionCreated = implementer(IDBSessionCreated)(
    namedtuple('DBSessionCreated', ['name', 'session'])
)


def base_factory():
    """
    :rtype: sqlalchemy.ext.declarative.DeclarativeMeta
    """
    metadata = MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s',
    })
    base = declarative_base(metadata=metadata)
    return base


def get_engine(request_or_config, name=''):
    """
    shortcut for find service

    :type request_or_config: \
        Union[pyramid.request.Request, pyramid.config.Configurator]
    :type name: str
    :rtype: sqlalchemy.engine.base.Engine
    """
    dummy_factory = request_or_config.find_service_factory(IDBEngine,
                                                           name=name)
    return dummy_factory(None, None)


def get_session_factory(request_or_config, name=''):
    """
    shortcut for find service

    :type request_or_config: \
        Union[pyramid.request.Request, pyramid.config.Configurator]
    :type name: str
    :rtype: sqlalchemy.orm.session.sessionmaker
    """
    dummy_factory = request_or_config.find_service_factory(IDBSessionFactory,
                                                           name=name)
    return dummy_factory(None, None)


def get_tm_session(request, name=''):
    """
    shortcut for find service

    :type request: pyramid.request.Request
    :type name: str
    :rtype: sqlalchemy.orm.session.Session
    """
    return request.find_service(IDBSession, name=name)


def create_unmanaged_session(request_or_config, name=''):
    factory = get_session_factory(request_or_config, name)
    session = factory()
    event = DBSessionCreated(session=session, name=name)
    request_or_config.registry.notify(event)
    return session


class DBSessionFactory(object):

    __slots__ = ['factory', 'name']

    def __init__(self, factory, name=''):
        """
        :type factory: sqlalchemy.orm.session.sessionmaker
        :type name: str
        """
        self.factory = factory
        self.name = name

    def __call__(self, context, request):
        """
        :type context: Any
        :type request: pyramid.request.Request
        :rtype: sqlalchemy.orm.session.Session
        """
        session = self.factory()
        event = DBSessionCreated(session=session, name=self.name)
        request.registry.notify(event)
        register(session, transaction_manager=request.tm)
        return session


def includeme(config):
    """
    :type config: pyramid.config.Configurator
    """
    settings = config.get_settings()
    settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'

    config.include('pyramid_services')
    config.include('pyramid_tm')

    prefix = settings.get('pyramid_services_sqlalchemy.prefix', 'sqlalchemy.')

    names = aslist(settings.get(prefix + 'names', ''))
    if names:
        for name in names:
            engine = engine_from_config(settings, prefix=prefix + name + '.')
            factory = sessionmaker(bind=engine)
            config.register_service(engine, IDBEngine, name=name)
            config.register_service(factory, IDBSessionFactory, name=name)
            config.register_service_factory(DBSessionFactory(factory, name),
                                            IDBSession, name=name)
        config.register_service(tuple(names), IDBNames)
    else:
        engine = engine_from_config(settings, prefix=prefix)
        factory = sessionmaker(bind=engine)
        config.register_service(engine, IDBEngine)
        config.register_service(factory, IDBSessionFactory)
        config.register_service_factory(DBSessionFactory(factory), IDBSession)
        config.register_service(('',), IDBNames)

    config.action(None, configure_mappers)
