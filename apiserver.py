#######################################
## Author:			Jennifer Ryan    ##
## 								     ##
## Date:			19/02/16         ##
#######################################
from flask import Flask, Response, request, jsonify
from flask_restful import reqparse
from collections import namedtuple
from collection_json import Collection, Item, Template, Link, Data
import DBcm
import simplejson as json


app = Flask(__name__)
app.config.update(
    DEBUG=True,
    SECRET_KEY="youwillneverguess",
    DB_CONFIG={'host': '127.0.0.1',
               'user': 'gamesadmin',
               'password': 'gamesadminpasswd',
               'database': 'GamesDB'}
)


# Create a Named Tuple for each Table
players = namedtuple('players', 'id, handle, first, last, email, passwd')
games = namedtuple('games', 'id, name, description')
scores = namedtuple('scores', 'game_id, player_id, score, ts, id')


# Create a Collection+JSON object representation
collection = Collection(href='http://127.0.0.1:5000/api')


@app.route('/api/', methods=['GET'])
def default():
    return Response(json.dumps(collection.to_dict(), indent=4, sort_keys=True),
                    status=200, mimetype='application/vnd.collection+json')


@app.route('/api/table/list', methods=['GET'])
def list_tables():
    with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
        cursor.execute("""SHOW TABLES """)
        result = cursor.fetchall()

    if len(result) is not 0:
        for table in result:
            table_name = table[0]
            i = Item(data=[Data(name='table', value=table_name)],
                     links=[Link(href='/api/table/post?name=' + table_name, rel='GET')])
            collection.items.append(i)
        i.href = '/api/table/list'

        return Response(json.dumps(collection.to_dict(), indent=4, sort_keys=True),
                        status=200, mimetype='application/vnd.collection+json')
    else:            # if no result found, send 400 "Bad Request
        return Response(status=404, mimetype='application/vnd.collection+json')


@app.route('/api/table/showall', methods=['GET'])
def show_table():
        # Parse the argument
        parser = reqparse.RequestParser()
        parser.add_argument('name', help='Name of the Table')
        args = parser.parse_args()
        table_name = args['name']

        if table_name is None:              # if no argument found, return 400, "Bad Request"
            return Response(status=400, mimetype='application/vnd.collection+json')

        else:
            if table_name == "games":
                with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
                    sql = "SELECT * FROM %s" % table_name
                    cursor.execute(sql)
                    result = [games(*row) for row in cursor.fetchall()]

                    if len(result) is not 0:   # check table is not empty
                        for row in result:
                            i = Item(href='/api/table/showall?name=games',
                                     data=[Data(name='id', value=row.id),
                                           Data(name='name', value=row.name),
                                           Data(name='description', value=row.description)],
                                     links=[Link(href='/api/table/showone?name=games&row=' + str(row.id),
                                                 rel='GET')])
                            collection.items.append(i)
                    else:                                        # if table is empty, return 404, "Not Found"
                        return Response(status=404, mimetype='application/vnd.collection+json')

            elif table_name == "players":
                with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
                    sql = "SELECT * FROM %s" % table_name
                    cursor.execute(sql)
                    result = [players(*row) for row in cursor.fetchall()]

                    if len(result) is not 0:   # check table is not empty
                        for row in result:
                            i = Item(href='/api/table/showall?name=players',
                                     data=[Data(name='id', value=row.id),
                                           Data(name='handle', value=row.handle),
                                           Data(name='first', value=row.first),
                                           Data(name='last', value=row.last),
                                           Data(name='first', value=row.first),
                                           Data(name='password', value=row.passwd)],
                                     links=[Link(href='/api/table/showone?name=players&row=' + str(row.id),
                                                 rel='GET')])
                            collection.items.append(i)
                    else:                                        # if table is empty, return 404, "Not Found"
                        return Response(status=404, mimetype='application/vnd.collection+json')

            elif table_name == "scores":
                with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
                    sql = "SELECT * FROM %s" % table_name
                    cursor.execute(sql)
                    result = [scores(*row) for row in cursor.fetchall()]

                    if len(result) is not 0:   # check table is not empty
                        for row in result:
                            i = Item(href='/api/table/showall?name=scores',
                                     data=[Data(name='id', value=row.id),
                                           Data(name='game id', value=row.game_id),
                                           Data(name='player id', value=row.player_id),
                                           Data(name='score', value=row.score),
                                           Data(name='timestamp', value=str(row.ts))],
                                     links=[Link(href='/api/table/showone?name=scores&row=' + str(row.id),
                                                 rel='GET')])
                            collection.items.append(i)
                    else:                                        # if table is empty, return 404, "Not Found"
                        return Response(status=404, mimetype='application/vnd.collection+json')

            return Response(json.dumps(collection.to_dict(), indent=4, sort_keys=True),
                            status=200, mimetype='application/vnd.collection+json')


@app.route('/api/table/post', methods=['POST', 'GET'])
def post_table():
    if request.method == 'POST':                    # If a template has been received
        template_data = request.get_json(force=True)
        template_to_str = json.dumps(template_data)

        template = Template.from_json(template_to_str)
        table_name = template.table.value

        if table_name == "games":
            name = template.name.value
            description = template.description.value
            with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
                _SQL = "INSERT INTO games (name, description) VALUES (%s, %s)"
                cursor.execute(_SQL, (name, description,))
                row_id = cursor.lastrowid       # return the id of the row inserted

        elif table_name == "players":
                handle = template.handle.value
                first = template.first.value
                last = template.last.value
                email = template.email.value
                password = template.password.value

                with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
                    _SQL = "INSERT INTO players (handle, first, last, email, passwd) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(_SQL, (handle, first, last, email, password,))
                    row_id = cursor.lastrowid

        elif table_name == "scores":
            game_id = template.game_id.value
            player_id = template.player_id.value
            score = template.score.value

            with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
                _SQL = "INSERT INTO scores (game_id, player_id, score) VALUES (%s, %s, %s)"
                cursor.execute(_SQL, (game_id, player_id,  score,))
                row_id = cursor.lastrowid

        collection.links = [Link(href='/api/table/showall?name=' + str(table_name), rel='GET'),
                            Link(href='/api/table/showone?name=' + str(table_name)+'&row=' + str(row_id),
                                 rel='GET')]

        return Response(json.dumps(collection.to_dict(), indent=4, sort_keys=True),
                        status=201, mimetype='application/vnd.collection+json')

    elif request.method == 'GET':                   # else send back a Template for the requested table
        parser = reqparse.RequestParser()
        parser.add_argument('name', help='Name of the Table')
        args = parser.parse_args()
        table_name = args['name']

        if table_name is None:                      # if no argument found, return 400, "Bad Request"
            return Response(status=400, mimetype='application/vnd.collection+json')

        else:
            if table_name == "games":
                collection.template = Template(data=[Data(name='table', value='games'),
                                                     Data(name='name', value=''),
                                                     Data(name='description', value='')])
            elif table_name == "players":
                collection.template = Template(data=[Data(name='table', value='players'),
                                                     Data(name='handle', value=''),
                                                     Data(name='first', value=''),
                                                     Data(name='last', value=''),
                                                     Data(name='email', value=''),
                                                     Data(name='password', value='')])
            elif table_name == "scores":
                collection.template = Template(data=[Data(name='table', value='scores'),
                                                     Data(name='game_id', value=''),
                                                     Data(name='player_id', value=''),
                                                     Data(name='score', value='')])
        return Response(json.dumps(collection.to_dict(), indent=4, sort_keys=True),
                        status=200, mimetype='application/vnd.collection+json')
    else:
        return 'Unsupported HTTP method: {}.'.format(request.method)


@app.route('/api/table/showone', methods=['GET'])
def show_one():
    # Parse the arguments
    parser = reqparse.RequestParser()
    parser.add_argument('name', help='Name of the Table')
    parser.add_argument('row', help='The "id" of the Row, eg. 1')
    args = parser.parse_args()
    table_name = args['name']
    row_id = args['row']

    if table_name and row_id is not None:
        if table_name == "games":
            with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
                sql = "SELECT * FROM %s WHERE id=%s" % (table_name,  row_id)
                cursor.execute(sql)
                result = [games(*row) for row in cursor.fetchall()]

                if len(result) is not 0:   # check if result found
                    for row in result:
                        i = Item(href='/api/table/showone?name=games&row=' + row_id,
                                 data=[Data(name='id', value=row.id),
                                       Data(name='name', value=row.name),
                                       Data(name='description', value=row.description)],
                                 links=[])
                        collection.items.append(i)

                    collection.template = Template(data=[Data(name='table', value='games'),
                                                         Data(name='name', value=''),
                                                         Data(name='description', value='')])
                else:            # if no result found, send 400 "Bad Request
                    return Response(status=404, mimetype='application/vnd.collection+json')

        elif table_name == "players":
            with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
                sql = "SELECT * FROM %s WHERE id=%s" % (table_name,  row_id)
                cursor.execute(sql)
                result = [players(*row) for row in cursor.fetchall()]

                if len(result) is not 0:   # check if result found
                    for row in result:
                        i = Item(href='/api/table/showone?name=players&row=' + row_id,
                                 data=[Data(name='id', value=row.id),
                                       Data(name='handle', value=row.handle),
                                       Data(name='first', value=row.first),
                                       Data(name='last', value=row.last),
                                       Data(name='first', value=row.first),
                                       Data(name='password', value=row.passwd)],
                                 links=[])
                        collection.items.append(i)

                    collection.template = Template(data=[Data(name='table', value='players'),
                                                         Data(name='handle', value=''),
                                                         Data(name='first', value=''),
                                                         Data(name='last', value=''),
                                                         Data(name='email', value=''),
                                                         Data(name='password', value='')])
                else:            # if no result found, send 400 "Bad Request
                    return Response(status=404, mimetype='application/vnd.collection+json')

        elif table_name == "scores":
            with DBcm.UseDatabase(app.config["DB_CONFIG"]) as cursor:
                sql = "SELECT * FROM %s WHERE id=%s" % (table_name,  row_id)
                cursor.execute(sql)
                result = [scores(*row) for row in cursor.fetchall()]

                if len(result) is not 0:   # check if result found
                    for row in result:
                        i = Item(href='/api/table/showone?name=scores&row=' + row_id,
                                 data=[Data(name='game id', value=row.game_id),
                                       Data(name='player id', value=row.player_id),
                                       Data(name='score', value=row.score),
                                       Data(name='id', value=row.id),
                                       Data(name='timestamp', value=str(row.ts))],
                                 links=[])
                        collection.items.append(i)

                    collection.template = Template(data=[Data(name='table', value='scores'),
                                                         Data(name='game_id', value=''),
                                                         Data(name='player_id', value=''),
                                                         Data(name='score', value='')])
                else:            # if no result found, send 400 "Bad Request
                    return Response(status=404, mimetype='application/vnd.collection+json')

        collection.links = [Link(href='/api/table/showall?name=' + str(table_name), rel='GET'),
                            Link(href='/api/table/showone?name=' + str(table_name) + '&row=' + str(row_id), rel='GET'),
                            Link(href='/api/table/post?name=' + str(table_name), rel='GET')]

        return Response(json.dumps(collection.to_dict(), indent=4, sort_keys=True),
                        status=200, mimetype='application/vnd.collection+json')
    else:
        return Response(status=400, mimetype='application/vnd.collection+json')  # if no arguments found


@app.errorhandler(404)
def not_found(error):
    message = {
            'status': 404,
            'message': 'Not Found: ' + request.url,
    }
    response = jsonify(message)
    response.status_code = 404

    return response


@app.errorhandler(400)
def bad_request(error):
    message = {
            'status': 400,
            'message': 'Bad Request: ' + request.url,
    }
    response = jsonify(message)
    response.status_code = 400

    return response


@app.errorhandler(500)
def internal_error(error):
    message = {
            'error': 'AttributeError',
            'status': 500,
            'message': 'Incorrect data received: ' + request.url,
    }
    response = jsonify(message)
    response.status_code = 500

    return response


app.error_handler_spec[None][404] = not_found
app.error_handler_spec[None][400] = bad_request
app.error_handler_spec[None][400] = internal_error

app.run(debug=True)
