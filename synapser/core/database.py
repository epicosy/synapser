import base64
import json
import contextlib

from typing import Union, Tuple

from sqlalchemy.orm import declarative_base, Session
from sqlalchemy import Column, Integer, String, create_engine, inspect, DateTime
from sqlalchemy.sql import func

Base = declarative_base()


class Signal(Base):
    __tablename__ = 'signal'

    id = Column(Integer, primary_key=True)
    arg = Column('arg', String, nullable=False)
    url = Column('url', String, nullable=False)
    data = Column('data', String, nullable=False)
    placeholders = Column('placeholders', String, nullable=False)

    def decoded(self) -> Tuple[dict, dict]:
        return json.loads(base64.b64decode(self.data).decode()), json.loads(base64.b64decode(self.placeholders).decode())

    def __str__(self):
        return f"{self.id} {self.arg} {self.url}"


class Instance(Base):
    __tablename__ = 'instance'

    id = Column(Integer, primary_key=True)
    name = Column('name', String(255), nullable=False)
    status = Column('status', String(255), nullable=False)
    path = Column('path', String, nullable=False)
    target = Column('target', String, nullable=False)
    socket = Column('socket', Integer, nullable=True)
    start = Column('start', DateTime(timezone=True), server_default=func.now())
    end = Column('end', DateTime(timezone=True), nullable=True)

    def jsonify(self):
        return {'id': self.id, 'name': self.name, 'status': self.status, 'path': self.path, 'target': self.target,
                'socket': self.socket, 'start': self.start, 'end': self.end}


class Database:
    def __init__(self, dialect: str, username: str, password: str, host: str, port: int, database: str,
                 debug: bool = False):
        self.engine = create_engine(f"{dialect}://{username}:{password}@{host}:{port}/{database}", echo=debug)
        Base.metadata.create_all(bind=self.engine)

    def refresh(self, entity: Base):
        with Session(self.engine) as session, session.begin():
            session.refresh(entity)

        return entity

    def add(self, entity: Base):
        with Session(self.engine) as session, session.begin():
            session.add(entity)
            session.flush()
            session.refresh(entity)
            session.expunge_all()

            if hasattr(entity, 'id'):
                return entity.id

    def destroy(self):
        with contextlib.closing(self.engine.connect()) as con:
            trans = con.begin()
            Base.metadata.drop_all(bind=self.engine)
            trans.commit()

    def delete(self, entity: Base, entity_id: Union[int, str]):
        with Session(self.engine) as session, session.begin():
            return session.query(entity).filter(entity.id == entity_id).delete(synchronize_session='evaluate')

    def has_table(self, name: str):
        inspector = inspect(self.engine)
        return inspector.reflect_table(name, None)

    def query(self, entity: Base, entity_id: Union[int, str] = None):
        with Session(self.engine) as session, session.begin():
            if entity_id and hasattr(entity, 'id'):
                results = session.query(entity).filter(entity.id == entity_id).first()
            else:
                results = session.query(entity).all()

            session.expunge_all()
            return results

    def update(self, entity: Base, entity_id: int, attr: str, value):
        with Session(self.engine) as session, session.begin():
            if hasattr(entity, 'id') and hasattr(entity, attr):
                session.query(entity).filter(entity.id == entity_id).update({attr: value})
            else:
                raise ValueError(f"Could not update {type(entity)} {attr} with value {value}")
