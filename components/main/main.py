import sys
sys.path.insert(0, 'http://localhost:8888/components')
sys.path.insert(0, 'http://localhost:8888/main/src/Lib')

from browser import window
jq = window.jQuery.noConflict(True)

window.jq = jq

import random
print('Iniciando aplicación')
from components.main.models.A import A
from components.main.init import init, set_page_controller

from components.main.reactive import reactive
from components.main.page import PageController, parse
from components.main.queries.my_query import MyQuery


class MyController(PageController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        set_page_controller(self)
        @reactive
        def f():
            self.q = self.subscribe(id='my_query', klass=MyQuery, name='MyQuery',
                                    sort=(('x', 1),), skip=0, limit=1, a=self.a, b=self.b)

    def x(self):
        return False

def main():
    print('main')
    page_controller = MyController(id='my controller', a=-1, b=10)
    parse(page_controller, jq('.page'))

init(main)
"""
button_send = jq('#button')
sent_initial_data = False

def send_data():
    global sent_initial_data
    if not sent_initial_data:
        BaseController.subscribe_all()
        sent_initial_data = True


button_send.bind('click', send_data)
"""


