from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi
from . import appbuilder, db 
from .models import Machine, Blacklist, Whitelist
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
class AdressModelView(ModelView):
    datamodel = SQLAInterface(Machine)
    label_columns = {'Name':'name'}
    list_columns = ['comment']

class BlackListModelView(ModelView):
    datamodel = SQLAInterface(Blacklist)
    label_columns = {'Address':'Adresses'}
    list_columns = ['ip']

class WhiteListModelView(ModelView):
    datamodel = SQLAInterface(Whitelist)
    label_columns = {'Address':'Adresses'}
    list_columns = ['ip']

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
    WhiteListModelView, "White list", icon="fa-folder-open-o", category="mikrodick"
)
appbuilder.add_view(
    BlackListModelView, "Black list", icon="fa-folder-open-o", category="mikrodick"
)
appbuilder.add_view(
    AdressModelView, "Sentinel", icon="fa-folder-open-o", category="mikrodick"
)
