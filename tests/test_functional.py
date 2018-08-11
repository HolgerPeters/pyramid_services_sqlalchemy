# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import unittest
from pyramid.config import Configurator
from pyramid.request import Request
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.session import Session
from zope.interface.verify import verifyObject


class FunctionalTestCase(unittest.TestCase):

    def test_single(self):
        from pyramid_services_sqlalchemy import (
            IDBSessionCreated,
            create_unmanaged_session,
            get_engine,
            get_tm_session,
        )

        config = Configurator(settings={
            'sqlalchemy.url': 'sqlite://',
        })
        config.include('pyramid_services_sqlalchemy')

        def aview(request):
            db = get_tm_session(request)
            self.assertIsInstance(db, Session)
            return 'OK'

        def handle_db_session_created(event):
            verifyObject(IDBSessionCreated, event)
            self.assertIsInstance(event.session, Session)
            self.assertEqual(event.name, '')

        def touch_engine():
            engine = get_engine(config)
            self.assertIsInstance(engine, Engine)

        config.add_route('root', pattern='/')
        config.add_view(aview, route_name='root', renderer='json')
        config.add_subscriber(handle_db_session_created, IDBSessionCreated)
        config.action(None, touch_engine)
        app = config.make_wsgi_app()

        c_db = create_unmanaged_session(config)
        self.assertIsInstance(c_db, Session)

        resp = Request.blank('/').get_response(app)
        self.assertEqual(resp.status_code, 200)

    def test_multiple(self):
        from pyramid_services_sqlalchemy import (
            IDBSessionCreated,
            create_unmanaged_session,
            get_engine,
            get_tm_session,
        )

        config = Configurator(settings={
            'sqlalchemy.names': 'a b',
            'sqlalchemy.a.url': 'sqlite://',
            'sqlalchemy.b.url': 'sqlite://',
        })
        config.include('pyramid_services_sqlalchemy')

        def aview(request):
            db_a = get_tm_session(request, name='a')
            db_b = get_tm_session(request, name='b')
            self.assertIsInstance(db_a, Session)
            self.assertIsInstance(db_b, Session)
            self.assertIsNot(db_a, db_b)
            return 'OK'

        def handle_db_session_created(event):
            verifyObject(IDBSessionCreated, event)
            self.assertIsInstance(event.session, Session)
            self.assertIn(event.name, {'a', 'b'})

        def touch_engine():
            engine_a = get_engine(config, 'a')
            engine_b = get_engine(config, 'b')
            self.assertIsInstance(engine_a, Engine)
            self.assertIsInstance(engine_b, Engine)
            self.assertIsNot(engine_a, engine_b)

        config.add_route('root', pattern='/')
        config.add_view(aview, route_name='root', renderer='json')
        config.add_subscriber(handle_db_session_created, IDBSessionCreated)
        config.action(None, touch_engine)
        app = config.make_wsgi_app()

        c_db_a = create_unmanaged_session(config, name='a')
        c_db_b = create_unmanaged_session(config, name='b')
        self.assertIsInstance(c_db_a, Session)
        self.assertIsInstance(c_db_b, Session)

        resp = Request.blank('/').get_response(app)
        self.assertEqual(resp.status_code, 200)

    def test_declarative(self):
        import sqlalchemy as sa
        from pyramid_services_sqlalchemy import (
            base_factory,
            get_engine,
            get_tm_session,
        )
        Base = base_factory()

        def default_value(execution_context):
            return execution_context.engine.my_value

        class Some(Base):
            __tablename__ = 'some'
            id = sa.Column(sa.INTEGER, primary_key=True)
            s = sa.Column(sa.VARCHAR(255), nullable=False,
                          default=default_value, onupdate=default_value)

        config = Configurator(settings={
            'sqlalchemy.url': 'sqlite://',
        })
        config.include('pyramid_services_sqlalchemy')

        def aview(request):
            db = get_tm_session(request)
            db.add(Some())
            db.flush()
            v = db.query(Some).first()
            self.assertEqual(v.s, '__my_value__')
            return 'OK'

        def touch_engine():
            engine = get_engine(config)
            engine.my_value = '__my_value__'

        config.add_route('root', pattern='/')
        config.add_view(aview, route_name='root', renderer='json')
        config.action(None, touch_engine)
        app = config.make_wsgi_app()

        Base.metadata.create_all(bind=get_engine(config))

        resp = Request.blank('/').get_response(app)
        self.assertEqual(resp.status_code, 200)
