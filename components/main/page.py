import re
from components.main.reactive import Model, reactive
from components.lib.utils import index_by_id, compare, index_in_list


def is_alive(node):
    return jq.contains(document, node[0])


def if_function(controller, if_, node, html):
    print('if function', if_, node)
    if is_alive(node):
        val = getattr(controller, if_)
        if callable(val):
            val = val()
        if not val:
            for ch in node.find('[r]'):
                ch = jq(ch)
                if ch.data('helper'):
                    for c, h in ch.data('helper'):
                        c.reset(h)
            node.children().remove()
        else:
            if len(node.children()) == 0:
                children = jq(html)
                node.append(children)
                for ch in children:
                    parse(controller, jq(ch))
            elif len(node.children()) == 1:
                parse(controller, node.children())


def render(model, node, template):
    #print('render:', template)
    if template is None:
        return
    if is_alive(node):
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', template)
        dct = {}
        for attr in attrs:
            attr = attr[1:-1]
            dct[attr] = getattr(model, attr)

        node.html(template.format(**dct))
        print('>', node)


def set_events(controller, node, attrs):
    on_click = attrs.get('on-click')
    if on_click:
        on_click = on_click[1:-1]
        print(attrs, on_click)
        method = getattr(controller, on_click)
        node.click(method)
    integer_value = attrs.get('integer-value')
    if integer_value:
        integer_value = integer_value[1:-1]

        def set_integer_value(event=None):
            try:
                val = int(node.val())
            except ValueError:
                val = node.val()
            setattr(controller, integer_value, val)
        node.keyup(set_integer_value)


def set_attributes(controller, node, attrs):
    mapping = {}
    for key, value in attrs.items():
        if key == 'r':
            continue
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', value)
        for attr in attrs:
            attr = attr[1:-1]
            v = getattr(controller, attr)
            if callable(v) and key != 'on-click':
                v = v()
            if key == 'integer-value':
                node.val(str(v))

            mapping[attr] = v
        if key not in ('on-click', 'integer-value'):
            node.attr(key, value.format(**mapping))


def parse(controller, node):
    print('parse', node)
    if_ = node.attr('if')
    if if_:
        if_ = if_[1:-1]
        helper = reactive(if_function, controller, if_, node, node.html())
        node.data('helper', [(controller, helper)])
    else:
        if node.attr('r') == '':
            try:
                dct = {}
                for attr in node[0].attributes:
                    dct[attr.name] = attr.value
            except AttributeError:
                dct = {}
                for k, v in node[0].attrib.items():
                    dct[k] = v

            helper = reactive(set_attributes, controller, node, dct)
            node.data('helper', [(controller, helper)])
            set_events(controller, node, dct)
        if len(node.children()) == 0:
            if node.attr('r') == '':
                helper = reactive(render, controller, node, node.html())
                lista = node.data('helper')
                if lista:
                    lista.append((controller, helper))
                else:
                    node.data('helper', [(controller, helper)])
        else:
            if node.hasClass('template'):
                controller.register(node)
            else:
                for ch in node.children():
                    print ('a)', ch)
                    ch = jq(ch)
                    print ('b)', ch)
                    parse(controller, ch)


class Query(object):
    def __init__(self, id, sort, skip, limit, **kw):
        self.id = id
        self.full_name = str((self.__class__.__name__, tuple(sorted([('__collection__', self._collection),
                                                                     ('__sort__', sort), ('__skip__', skip)] +
                                                                    list(kw.items()) + [('__limit__', limit)]))))
        self.sort = sort
        self.skip = skip
        self.limit = limit
        for k,v in kw.items():
            setattr(self, k, v)
        self.models = []
        self.nodes = []


class Controller(Model):
    objects = {}
    queries = {}



    def register(self, node):
        name = node.attr('query-id')
        html = node.html()
        node.children().remove()

        self.queries[name].nodes.append((node, html))
        for a in self.queries[name].models:
            n_ = jq(html)
            n_.attr('reactive_id', a.id)
            node.append(n_)
            parse(a, n_)

    def subscribe(self, q):
        name = q.id
        previous = Controller.queries.get(name)
        if previous:
            print('stop subscription')
            q.nodes = previous.nodes
            for node, _ in q.nodes:
                if node.data('helper'):
                    for c, h in node.data('helper'):
                        c.reset(h)
                node.children().remove()
        Controller.queries[name] = q

    def test(self, model, raw, query_full_name):
        for query in self.queries.values():
            if query.full_name == query_full_name:
                if '__new__' in raw.keys():
                    self.new(model, raw, query)
                elif '__out__' in raw.keys():
                    self.out(model, query)
                else:
                    self.modify(model, query)

    def modify(self, model, query):
        index = self.index_by_id(model.id, query.models)
        print(model.id, query.models, index)
        del query.models[index]
        tupla = self.index_in_DOM(model)

        if index == tupla[0]:
            print('ocupa misma posicion')
        else:
            print('move to ', model, tupla)
            for node, html in query.nodes:
                n_ = node.children("[reactive_id='"+str(model.id)+"']")
                ref = node.children("[reactive_id='"+str(tupla[2])+"']")
                action = tupla[1]
                if action == 'before':
                    ref.before(n_)
                else:
                    ref.after(n_)
                parse(model, n_)

        query.models.insert(tupla[0], model)

    def index_by_id(self, id, models):
        return index_by_id(models, id)

    def out(self, model, query):
        index = self.index_by_id(model.id, query.models)
        del query.models[index]
        for node, html in query.nodes:
            node.children("[reactive_id='"+str(model.id)+"']").remove()

    def new(self, model, raw, query):
        tupla = self.index_in_DOM(model, query)
        index = tupla[0]
        query.models.insert(index, model)

        action = tupla[1]
        if action == 'append':
            for node, html in query.nodes:
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                node.append(n_)
                parse(model, n_)
        elif action == 'before':
            for node, html in query.nodes:
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                ref = node.children("[reactive_id='"+str(tupla[2])+"']")
                ref.before(n_)
                parse(model, n_)
        elif action == 'after':
            for node, html in query.nodes:
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                ref = node.children("[reactive_id='"+str(tupla[2])+"']")
                ref.after(n_)
                parse(model, n_)

        if len(query.models) > query.limit:
            if raw['__skip__'] != query.models[0].id:
                self.out(query.models[0])
            else:
                self.out(query.models[-1])

    @staticmethod
    def compare(a, b, key, order=1):
        return compare(a, b, key, order)

    def index_in_DOM(self, model, query):
        ret = index_in_list(query.models, query.sort, model)
        if ret == 0 and len(query.models) == 0:
            return (0, 'append')
        if ret == 0:
            return (0, 'before', query.models[0].id)
        else:
            return (ret, 'after', query.models[ret-1].id)
