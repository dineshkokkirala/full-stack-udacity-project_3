import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES


@app.route('/drinks')
def get_drinks():
    try:
        drinks = Drink.query.all()

        drinks = [drink.short() for drink in drinks]

        return ({
            'success': True,
            'drinks': drinks
        })

    except Exception as e:
        print(e)
        abort(500)


@app.route('/drinks-detail')
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail(payload):
    try:
        drinks = Drink.query.all()

        drinks = [drink.long() for drink in drinks]

        return ({
            'success': True,
            'drinks': drinks
        })

    except Exception as e:
        # print(e)
        abort(500)


@app.route('/drinks', methods=["POST"])
@requires_auth(permission='post:drinks')
def post_drink(payload):
    body = request.json

    if not all([x in body for x in ['title', 'recipe']]):
        abort(422)

    drink_title = body['title']
    drink_recipe = body['recipe']

    if not isinstance(drink_recipe, list):
        abort(422)

    for ingredient in drink_recipe:
        if not all([x in ingredient for x in ['name', 'color', 'parts']]):
            abort(422)

    drink_recipe = json.dumps(drink_recipe)

    try:
        drink = Drink(title=drink_title, recipe=drink_recipe)
        drink.insert()
    except Exception as e:
        print(f'Exception in post_drink(): {e}')
        abort(422)

    return jsonify({
        "success": True,
        "drinks": [drink.long()]
    })


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def edit_drink(payload, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)

    body = request.json

    if not any([x in body for x in ['title', 'recipe']]):
        abort(422)

    if 'title' in body:
        drink.title = body['title']
    if 'recipe' in body:
        drink_recipe = body['recipe']

        if not isinstance(drink_recipe, list):
            abort(422)

        for ingredient in drink_recipe:
            if not all([x in ingredient for x in ['name', 'color', 'parts']]):
                abort(422)

        drink_recipe = json.dumps(drink_recipe)
        drink.recipe = drink_recipe

    try:
        drink.update()
    except Exception as e:
        print(f'Exception in edit_drink(): {e}')
        abort(422)

    return jsonify({
        "success": True,
        "drinks": [drink.long()]
    })


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)

    try:
        drink.delete()
    except Exception as e:
        print(f'Exception in delete_drink(): {e}')
        abort(422)

    return jsonify({
        "success": True,
        "delete": id
    })


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "forbidden"
    }), 403


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "method not allowed"
    }), 405


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404


@app.errorhandler(AuthError)
def auth_error(excpt):
    response = jsonify(excpt.error)
    response.status_code = excpt.status_code
    return response
