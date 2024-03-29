from flask import render_template,flash
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi, SimpleFormView
from . import appbuilder, db 
from .models import Machine, Blacklist, Whitelist,GlobalBlackList,GlobalWhiteList
from sqlalchemy.orm import relationship
"""
    Create your Model based REST API::

    class MyModelApi(ModelRestApi):
        datamodel = SQLAInterface(MyModel)

    appbuilder.add_api(MyModelApi)


    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(
        MyModelView,
        "My View",
        icon="fa-folder-open-o",
        category="My Category",
        category_icon='fa-envelope'
    )
"""

"""
    Application wide 404 error handler
"""
class MachineModelView(ModelView):
    datamodel = SQLAInterface(Machine)
    label_columns = {'Name':'Name'}
    list_columns = ['name','comment']

class BlackListModelView(ModelView):
    datamodel = SQLAInterface(Blacklist)
    label_columns = {'Address':'Adresses'}
    list_columns = ['id','ip']

class WhiteListModelView(ModelView):
    datamodel = SQLAInterface(Whitelist)
    label_columns = {'Address':'Adresses'}
    list_columns = ['id','ip']
class GlobalWhiteListModelView(ModelView):
    datamodel = SQLAInterface(GlobalWhiteList)
    label_columns = {'Address':'Adresses'}
    list_columns = ['id','ip']
class GlobalBlackListModelView(ModelView):
    datamodel = SQLAInterface(GlobalBlackList)
    label_columns = {'Address':'Adresses'}
    list_columns = ['id','ip']



@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


db.create_all()
appbuilder.add_view(
    WhiteListModelView, "White list", icon="fa-folder-open-o", category="Lists"
)
appbuilder.add_view(
    BlackListModelView, "Black list", icon="fa-folder-open-o", category="Lists"
)
appbuilder.add_view(
    MachineModelView, "Machine list", icon="fa-folder-open-o", category="Lists"
)
appbuilder.add_view(
    GlobalWhiteListModelView, "Global white list", icon="fa-folder-open-o", category="Lists"
)
appbuilder.add_view(
    GlobalBlackListModelView, "Global black list", icon="fa-folder-open-o", category="Lists"
)