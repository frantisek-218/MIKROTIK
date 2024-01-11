from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy_utils import IPAddressType


machine_blacklist_association = Table(
    'machine_blacklist_association',
    Model.metadata,
    Column('machine_id', Integer, ForeignKey('machine.id')),
    Column('blacklist_id', Integer, ForeignKey('blacklist.id'))
)
machine_whitelist_association = Table(
    'machine_whitelist_association',
    Model.metadata,
    Column('machine_id', Integer, ForeignKey('machine.id')),
    Column('whitelist_id', Integer, ForeignKey('whitelist.id'))
)
class Machine(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    comment = Column(String(50), nullable=True)
    blackList = relationship("Blacklist", secondary=machine_blacklist_association)
    whiteList = relationship("Whitelist", secondary=machine_whitelist_association)

    def __repr__(self):
        return self.name

class Blacklist(Model):
    id = Column(Integer, primary_key=True)
    ip = Column(IPAddressType, nullable=False, unique=True)

    def __repr__(self):
        return str(self.ip)

class Whitelist(Model):
    id = Column(Integer, primary_key=True)
    ip = Column(IPAddressType, nullable=False, unique=True)

    def __repr__(self):
        return str(self.ip)

class GlobalWhiteList(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True)
    ip = Column(IPAddressType, nullable=False, unique=True)

    def __repr__(self):
        return str(self.ip)

class GlobalBlackList(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True)
    ip = Column(IPAddressType, nullable=False, unique=True)

    def __repr__(self):
        return str(self.ip)