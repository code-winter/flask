import os

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask('app')
engine = create_engine(os.getenv("PG_DSN"))
Base = declarative_base()
Session = sessionmaker(bind=engine)

from views import UserView, AdView

app.add_url_rule('/users/', view_func=UserView.as_view('create_user'), methods=['POST'])
app.add_url_rule('/ads/', view_func=AdView.as_view('post_ads'), methods=['POST'])
app.add_url_rule('/ads/<int:ads_id>/', view_func=AdView.as_view('view_or_edit_ad'), methods=['GET', 'PATCH', 'DELETE'])

Base.metadata.create_all(engine)
