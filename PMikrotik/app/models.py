from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import IPAddressType


"""

You can use the extra Flask-AppBuilder fields and Mixin's

AuditMixin will add automatic timestamp of created and modified by who


"""
class Machine(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    comment = Column(String(50), nullable=True)
    Blist_id = Column(Integer, ForeignKey("BlackList.id"), nullable=False)
    blackList = relationship("BlackList", lazy="joined")
    White_id = Column(Integer, ForeignKey("WhiteList.id"), nullable=False)
    whiteList = relationship("WhiteList", lazy="joined")
    GBlist_id = Column(Integer, ForeignKey("GlobalBlackList.id"), nullable=False)
    globalBlackList = relationship("GlobalBlackList", lazy="joined")
    GWlist_id = Column(Integer, ForeignKey("GlobalWhiteList.id"), nullable=False)
    globalWhiteList = relationship("GlobalWhiteList", lazy="joined")
    def __repr__(self):
            return self.name

class BlackList(Model):
    id = Column(Integer, primary_key=True)
    ip = Column(IPAddressType, nullable=False)
    def __repr__(self):
            return self.ip
class WhiteList(Model):
    id = Column(Integer, primary_key=True)
    ip = Column(IPAddressType, nullable=False)
    def __repr__(self):
            return self.ip

class GlobalWhiteList(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True)
    ip = Column(IPAddressType, nullable=False)
    def __repr__(self):
            return self.name

class GlobalBlackList(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True)
    ip = Column(IPAddressType, nullable=False)
    def __repr__(self):
            return self.name
