from browser import window
import javascript

from components.lib.epochdate import epochargs2datetime

import json
from components.main.reactive import consume, Model, registered_models, execute_block
from components.main.controller import BaseController

WebSocket = javascript.JSConstructor(window.WebSocket)


def on_message(evt):
    try:
        result = evt.data
        print('raw', result)
        data = json.loads(result)
        data = epochargs2datetime(data)
        collection = data.pop('__collection__')
        filter_name = data.pop('__filter__')
        raw = data.copy()
        #data.pop('__skip__')
        klass = registered_models[collection]
        print('buscamos si ya tenemos el objeto con id', data['id'])
        try:
            model = klass.objects[data['id']]
            print('encontrado')
            with execute_block():
                for k, v in data.items():
                    if k in ('id', '__deleted__'):
                        continue
                    setattr(model, '_'+k, v)
        except KeyError:
            print('nuevo')
            data_ = {}
            for k, v in data.items():
                if not k.startswith('_') and k != 'id':
                    data_['_'+k] = v
                else:
                    data_[k] = v
            model = klass(**data_)

        print('test all controllers')
        r = []
        for c in BaseController.controllers.values():
            if c.filter_full_name == filter_name:
                r.append(c.test(model, raw))
        if all(r):
            del klass.objects[model.id]
    except Exception as e:
        print ('******************** error', e)


def init():
    print('iniciando socket')
    ws = WebSocket("ws://127.0.0.1:8888/ws")
    Model.ws = ws
    BaseController.ws = ws

    ws.bind('message', on_message)
