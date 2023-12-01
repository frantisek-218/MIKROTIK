from flask_appbuilder import ModelRestApi
from flask_appbuilder.api import BaseApi, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.models.filters import BaseFilter
from sqlalchemy import or_

from . import appbuilder, db
from .models import Machine, Blacklist, Whitelist,GlobalBlackList,GlobalWhiteList
from marshmallow import fields, Schema


db.create_all()

# Schéma pro odpověď s pozdravem
class GreetingsResponseSchema(Schema):
    message = fields.String()


# API pro pozdrav
class GreetingApi(BaseApi):
    resource_name = "greeting"
    openapi_spec_component_schemas = (GreetingsResponseSchema,)

    openapi_spec_methods = {
        "greeting": {"get": {"description": "Override description"}}
    }

    @expose("/")
    def greeting(self):
        """Send a greeting
        ---
        get:
          responses:
            200:
              description: Greet the user
              content:
                application/json:
                  schema:
                    type: object
                    $ref: '#/components/schemas/GreetingsResponseSchema'
        """
        return self.response(200, message="Hello")


appbuilder.add_api(GreetingApi)


# Vlastní filtr pro vyhledávání v seznamu
class CustomFilter(BaseFilter):
    name = "Custom Filter"
    arg_name = "opr"

    def apply(self, query, value):
        return query.filter(
            or_(
                Machine.name.like(value + "%"),
                Machine.comment.like(value + "%"),
                Blacklist.ip.like(value + "%"),
                Whitelist.ip.like(value + "%"),
                GlobalWhiteList.name.like(value + "%"),
                GlobalBlackList.name.like(value + "%"),
            )
        )

# API pro model Machine
class MachineModelApi(ModelRestApi):
    resource_name = "machine"
    datamodel = SQLAInterface(Machine)
    allow_browser_login = True

    search_filters = {"name": [CustomFilter]}




# API pro model Blacklist
class BlacklistModelApi(ModelRestApi):
    resource_name = "blacklist"
    datamodel = SQLAInterface(Blacklist)
    allow_browser_login = True
    search_filters = {"ip": [CustomFilter]}




# API pro model Whitelist
class WhitelistModelApi(ModelRestApi):
    resource_name = "whitelist"
    datamodel = SQLAInterface(Whitelist)
    allow_browser_login = True
    search_filters = {"ip": [CustomFilter]}




# API pro model GlobalWhiteList
class GlobalWhiteListModelApi(ModelRestApi):
    resource_name = "globalwhitelist"
    datamodel = SQLAInterface(GlobalWhiteList)
    allow_browser_login = True
    search_filters = {"name": [CustomFilter]}




# API pro model GlobalBlackList
class GlobalBlackListModelApi(ModelRestApi):
    resource_name = "globalblacklist"
    datamodel = SQLAInterface(GlobalBlackList)
    allow_browser_login = True
    search_filters = {"name": [CustomFilter]}



appbuilder.add_api(MachineModelApi)
appbuilder.add_api(GlobalWhiteListModelApi)
appbuilder.add_api(WhitelistModelApi)
appbuilder.add_api(BlacklistModelApi)
appbuilder.add_api(MachineModelApi)
appbuilder.add_api(GreetingApi)
