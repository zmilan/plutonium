import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()

from components.main.controller import render_ex
from bs4 import BeautifulSoup
from components.main.reactive import Model

helpers = {}

class A(Model):
    objects = {}

    def __init__(self, id, **kw):
        super(A, self).__init__(id, **kw)


class Attribute(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Node(object):
    def __init__(self, html, parent=None):
        self.parent = parent
        self._html = html
        self.soup = BeautifulSoup(html, 'html.parser').div or BeautifulSoup(html, 'html.parser').span
        self.attributes = []
        for k, v in self.soup.attrs.items():
            self.attributes.append(Attribute(k, v))
        self._children = [Node(str(x), self) for x in self.soup.children if x.name in ('div', 'span')]

    def __getitem__(self, item):
        return self

    def data(self, key, value=None):
        if value:
            helpers[self.soup.attrs['id']] = value
        else:
            try:
                return helpers[self.soup.attrs['id']]
            except KeyError:
                return None

    def find(self, attr):
        if attr == '[r]':
            return [x for x in self._children if x.attr('r')]
            #return [Node(str(x), self) for x in self.soup.find_all() if x.name in ('div', 'span') and x.has_attr('r')]
            #return self.soup.find_all(r="")
        return []

    def remove(self):
        self.parent.soup.clear()
        self.parent._children = []

    def first(self):
        try:
            return self._children[0]
        except IndexError:
            return None

    def append(self, nodes):
        node = nodes[0]
        self._children.append(node)
        node = BeautifulSoup(node._html, 'html.parser').div or BeautifulSoup(node._html, 'html.parser').span
        self.soup.append(node)

    def html(self, value=None):
        if value is None:
            return self._html
        self._html = value

    def children(self):
        return self._children
        #return [Node(str(x), self) for x in self.soup.children if x.name in ('div', 'span')]

    def attr(self, attr, value=None):
        if value is None:
            try:
                return self.soup.attrs[attr]
            except KeyError:
                return None
        else:
            for item in self.attributes:
                if item.name == attr:
                    item.value = value
                    self.soup.attrs[attr] = value

    def outerHTML(self):
        return self._html

    def removeAttr(self, attr):
        self.attributes = [x for x in self.attributes if x.name != attr]
        if attr in self.soup.attrs:
            del self.soup.attrs[attr]


def test_basic_render_ex():
    node = Node("<div if='{z}'><span id='0' template=true><span id='1' r>{x}</span><span id='2' r>{y}</span></span></div>")
    m = A(id=None, x=8, y=9, z=False)
    render_ex(node, m)
    assert node.children() == []
    m.y = 900
    assert node.children() == []
    m.y = 901
    assert node.children() == []
    m.z = True
    assert len(node.children()) == 1
    assert node.children()[0].attr('id') == '0'
    assert node.first().attr('template') is None
    m.z = False
    assert node.children() == []
    m.x = 1000
    assert node.children() == []
    m.z = True
    assert len(node.children()) == 1
    assert node.children()[0].attr('id') == '0'
    #assert False