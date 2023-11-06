from flask_appbuilder import ModelRestApi
from flask_appbuilder.api import BaseApi, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.models.filters import BaseFilter
from sqlalchemy import or_

from . import appbuilder, db
from marshmallow import fields, Schema





class GreetingsResponseSchema(Schema):
    message = fields.String()


