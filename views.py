from hashlib import md5

import pydantic
from flask import request, jsonify
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError

from app import Session
from error_handlers import HttpError
from models import UserModel, AdModel
from validators import CreateAdValidator, CreateUserValidator


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
            return jsonify({
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
            return jsonify(query.to_dict())

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
            return jsonify({
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
            return jsonify(
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
            return jsonify({
                'Status': 'deletion successful'
            })
