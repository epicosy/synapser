import codecs
import contextlib
import pickle

from typing import Union
from cement import Handler

from sqlalchemy.orm import declarative_base, Session, relationship
from sqlalchemy import Column, Integer, String, create_engine, inspect, ForeignKey

from synapser.core.interfaces import HandlersInterface

Base = declarative_base()


class Signal(Base):
    __tablename__ = 'synapse'

    id = Column(Integer, primary_key=True)
    url = Column('url', String, nullable=False)
    args = Column('args', String, nullable=False)

    def decoded(self) -> dict:
        return pickle.loads(codecs.decode(self.data.encode(), 'base64'))


class SignalHandler(HandlersInterface, Handler):
    class Meta:
        label = 'signal'

    def save(self, endpoint: str, args: dict) -> int:
        encoded = codecs.decode(pickle.dumps(args), 'base64').decode()
        signal = Signal(endpoint=endpoint, args=encoded)

        return self.app.db.add(Signal, signal)

    def load(self, sid: str) -> Signal:
        return self.app.db.query(Signal, sid)


class Instance(Base):
    __tablename__ = 'instance'

    id = Column(Integer, primary_key=True)
    pid = Column('pid', Integer, nullable=False)
    name = Column('name', String(255), nullable=False)
    status = Column('status', String(255), nullable=False)


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
