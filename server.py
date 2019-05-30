#!/usr/bin/python
# -*- coding: utf-8 -*-

import flask
import json
import requests
import argparse
import requests

from logic_db import *
from collections import Counter

app = flask.Flask('FoodCounterApp')
app.myfood = MyFood()
app.all_params = all_params

default_text = "<html><body><pre> {{ arg }} </pre></body></html>"

@app.route('/actual_intake', methods=['GET'])
def actual_intake():
    return json.dumps(app.myfood.actual_intake()) + '\n'


@app.route('/get_foodlist', methods=['GET'])
def get_foodlist():
    return json.dumps(app.myfood.get_foodlist()) + '\n'


@app.route('/add_new_food', methods=['POST'])
def add_new_food():
    if 'name' in flask.request.form and 'params' in flask.request.form:
        params = eval(flask.request.form['params'])
        app.myfood.add_new_food(Food(flask.request.form['name'], params))
        return 'OK Addnew'
    else:
        flask.abort(400)


@app.route('/add_to_my_food', methods=['POST'])
def add_to_my_food():
    if 'name' in flask.request.form and 'weight' in flask.request.form:
        res = app.myfood.add_to_my_food(flask.request.form['name'],
                                        flask.request.form['weight'])
        return json.dumps(res)
    else:
        flask.abort(400)


@app.route('/print_my_food', methods=['GET'])
def print_my_food():
    return json.dumps(app.myfood.print_my_food()) + '\n'


@app.route('/get_all_params', methods=['GET'])
def get_all_params():
    return json.dumps(app.all_params) + '\n'


@app.route('/search_food', methods=['GET'])
def search_food():
    if 'name' in flask.request.args:
        param = flask.request.args['name']
        return json.dumps(app.myfood.search_food(param)) + '\n'
    else:
        flask.abort(400)


@app.route('/delete_last', methods=['POST'])
def delete_last():
    return json.dumps(app.myfood.delete_last()) + '\n'


@app.route('/watch', methods=['GET'])
def watch():
    return str(app.myfood.watch())


@app.route('/print_my_food_button', methods=['GET'])
def print_my_food_button():
    return flask.redirect('{}/print_my_food_site'.format(address))


@app.route('/add_to_my_food_button', methods=['POST'])
def add_to_my_food_button():
    nm = flask.request.form['name']
    wt = flask.request.form['weight']
    print('BUTTON nm={} wt={}'.format(nm, wt))
    requests.post(address + '/add_to_my_food', {'name': nm, 'weight': wt})
    return flask.redirect(address)


@app.route('/search_food_button', methods=['GET'])
def search_food_button():
    name = flask.request.args['name']
    print('BUTTON name={}', name)
    return flask.redirect('{}/search_food_site?name={}'.format(address, name))


@app.route('/get_foodlist_button', methods=['GET'])
def get_foodlist_button():
    return flask.redirect('{}/get_foodlist_site'.format(address))


@app.route('/actual_intake_button', methods=['GET'])
def actual_intake_button():
    return flask.redirect('{}/actual_intake_site'.format(address))


@app.route('/delete_last_button', methods=['POST'])
def delete_last_button():
    requests.post(address + '/delete_last');
    return flask.redirect(address)


@app.route('/', methods=['GET'])
def show_page():
    return flask.render_template_string(
        """
        <html>
        <head>
            <meta charset="UTF-8">
            <title>FoodCounterApp</title>
        </head>

        <body>
        <h1>FoodCounterApp</h1>

        <form method="get" action="/actual_intake_button">
            <button type="submit">Actual intake</button>
        </form>

        <form method="post" action="add_to_my_food_button">
            <button type="submit"><font color="green">Add to my food</green></button>
            <br> Name&#160; <input required name="name" type="text" size=10>
            <br> Weight <input required name="weight" type="text" size=10>
            <br>
        </form>
        <br>

        <form method="get" action="/print_my_food_button">
            <button type="submit">Print my food</button>
        </form>

        <form method="get" action="/search_food_button">
            <button type="submit">Search food</button>
            <input required name="name" type="text" size=10>
        </form>

        <form method="get" action="/get_foodlist_button">
            <button type="submit">Get foodlist</button>
        </form>

        <form method="post" action="/delete_last_button">
            <button type="submit">Delete last food</button>
        </form>

        </body>
        </html>
        """,
        **app.myfood.watch()
    )


@app.route('/print_my_food_site', methods=['GET'])
def show_page2():
    return flask.render_template_string(
        default_text,
        arg=app.myfood.print_my_food()
    )


@app.route('/search_food_site', methods=['GET'])
def show_page3():
    name = flask.request.args['name']
    return flask.render_template_string(
        default_text,
        arg='\n'.join(app.myfood.search_food(name))
    )


@app.route('/get_foodlist_site', methods=['GET'])
def show_page4():
    return flask.render_template_string(
        default_text,
        arg=app.myfood.get_foodlist()
    )


@app.route('/actual_intake_site', methods=['GET'])
def show_page5():
    return flask.render_template_string(
        default_text,
        arg=app.myfood.actual_intake()
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-address', default='127.0.0.1', type=str)
    parser.add_argument('--port', default=80, type=int)
    parser.add_argument('--init-db', default=False,
                        type=bool, const=True, nargs='?')
    parser.add_argument('--mft', default=True,
                        type=bool, const=False, nargs='?')
    args = parser.parse_args()
    if args.init_db:
        init_db(args.mft)
    address = 'http://{}:{}'.format(args.server_address, args.port)
    app.run(args.server_address, args.port, debug=True, threaded=True)
