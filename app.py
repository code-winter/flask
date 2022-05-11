import flask
import pydantic
from flask import Flask, request
from flask.views import MethodView
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
import re
from hashlib import md5

app = Flask('app')
engine = create_engine(os.getenv("PG_DSN"))
Base = declarative_base()
Session = sessionmaker(bind=engine)


class HttpError(Exception):

    def __init__(self, status_code, msg):
        self.status_code = status_code
        self.msg = msg


@app.errorhandler(HttpError)
def http_error_handler(error):
    response = flask.jsonify({'Error': error.msg})
    response.status_code = error.status_code
    return response


class CreateUserValidator(pydantic.BaseModel):
    username: str
    password: str
    email: str

    @pydantic.validator('password')
    def pass_length(cls, password):
        if len(password) < 8:
            raise ValueError('Password is too short!')
        return password

    @pydantic.validator('email')
    def validate_email(cls, email):
        email_regex = re.compile(r"(\w+|)@(\w+\.\w+)")
        if re.search(email_regex, email) is None:
            raise HttpError(400, 'This is not a valid email')
        return email


class CreateAdValidator(pydantic.BaseModel):
    title: str
    description: str
    owner_id: int


class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())


class AdModel(Base):
    __tablename__ = 'ads'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    owner_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
        }


class UserView(MethodView):

    def post(self):
        try:
            validated_data = CreateUserValidator(**request.json).dict()
        except pydantic.ValidationError as error:
            raise HttpError(400, error.errors())
        validated_data['password'] = str(md5(validated_data['password'].encode()).hexdigest())
        with Session() as session:
            username = validated_data['username']
            email = validated_data['email']
            if session.query(UserModel).filter(UserModel.username == username).first():
                raise HttpError(400, 'User with that name already exists')
            if session.query(UserModel).filter(UserModel.email == email).first():
                raise HttpError(400, 'That email already in use')
            new_user = UserModel(**validated_data)
            session.add(new_user)
            session.commit()
            return flask.jsonify({
                'status': 'OK',
                'id': new_user.id,
                'username': new_user.username
            })


class AdView(MethodView):
    def get(self, ads_id):
        with Session() as session:
            query = session.query(AdModel).filter(AdModel.id == ads_id).first()
            if not query:
                raise HttpError(404, 'There is no such ad')
            return flask.jsonify(query.to_dict())

    def post(self):
        try:
            validated_data = CreateAdValidator(**request.json).dict()
        except pydantic.ValidationError as error:
            raise HttpError(400, error.errors())
        with Session() as session:
            try:
                new_ad = AdModel(**validated_data)
                session.add(new_ad)
                session.commit()
            except IntegrityError:
                raise HttpError(400, 'This user does not exists')
            return flask.jsonify({
                'status': 'OK',
                'id': new_ad.id,
                'owner': new_ad.owner_id
            })

    def patch(self, ads_id):
        data = request.json
        if data.get('owner'):
            raise HttpError(400, 'You cannot change the owner')
        title = data.get('title')
        description = data.get('description')
        if title is None and description is None:
            raise HttpError(400, 'You need to supply data to change the ad')
        payload = dict()
        if title:
            payload.setdefault('title', title)
        if description:
            payload.setdefault('description', description)
        with Session() as session:
            session.query(AdModel).filter(AdModel.id == ads_id).update(payload)
            session.commit()
            changed_ad = session.query(AdModel).filter(AdModel.id == ads_id).first()
            return flask.jsonify(
                {
                    'id': ads_id,
                    'title': changed_ad.title,
                    'description': changed_ad.description
                }
            )

    def delete(self, ads_id):
        with Session() as session:
            query = session.query(AdModel).filter(AdModel.id == ads_id).first()
            if not query:
                raise HttpError(404, 'There is no such ad')
            session.delete(query)
            session.commit()
            return flask.jsonify({
                'Status': 'deletion successful'
            })


app.add_url_rule('/users/', view_func=UserView.as_view('create_user'), methods=['POST'])
app.add_url_rule('/ads/', view_func=AdView.as_view('post_ads'), methods=['POST'])
app.add_url_rule('/ads/<int:ads_id>/', view_func=AdView.as_view('view_or_edit_ad'), methods=['GET', 'PATCH', 'DELETE'])

Base.metadata.create_all(engine)
