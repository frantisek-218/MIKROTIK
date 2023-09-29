from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import IPAddressType


"""

You can use the extra Flask-AppBuilder fields and Mixin's

AuditMixin will add automatic timestamp of created and modified by who


"""
class Address(Model):
    id = Column(Integer, primary_key=True)
    ip = Column(IPAddressType, nullable=False)
    def __repr__(self):
            return self.ip

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