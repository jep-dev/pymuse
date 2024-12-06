import math
from src.core.types import infer_type

class Component:
    def __init__(self, name, op, bufsize=1024, cparams=None, vparams=None):
        self.name = name
        self.op = op
        self.cparams = cparams or []
        self.vparams = vparams or []
        self.inputs = []
        self.outputs = []
        self.buffers = []
        self.bufsize = bufsize
    def add_output(self):
        buffer = [None] * self.bufsize
        result = len(self.buffers)
        self.buffers.append(buffer)
        return result
    def push_to_buffer(self, i, value):
        buffer = self.buffers[i]
        next_pos = (len(buffer)-1) % len(buffer)
        buffer[next_pos] = value
    #def op(self, i, *args):
        #return NotImplementedError("Operator op not defined")
    def process(self):
        for i in range(len(self.outputs)):
            result = self.op(i, self.inputs, self.cparams, self.vparams)
            if result is not None:
                self.push_to_buffer(i, result)

class Node(Component):
    def __init__(self, name, op, bufsize=1024, cparams=None, vparams=None):
        super().__init__(name, op, bufsize, cparams, vparams)
    def map_reduce(self):
        for i in range(len(self.outputs)):
            mapped_values = [inp.op(i, *inp.cparams.values()) for inp in self.inputs]
            reduced_values = sum(mapped_values) / len(mapped_values)

class Edge(Component):
    def __init__(self, name, src, dest, op, bufsize=1024, cparams=None):
        super().__init__(name, op, bufsize, cparams)
        self.inputs = [src]
        self.outputs = [dest]
    def transfer(self):
        for i in range(len(self.outputs)):
            value = self.inputs[0].op(i, *self.cparams.values())
            if value is not None:
                self.push_to_buffer(i, value)

class Mod(Component):
    def __init__(self, name, target_component, op, bufsize, cparams=None):
        super().__init__(name, op, bufsize, cparams)
    def apply_mod(self):
        for k,v in self.cparams.items():
            self.target_component.cparams[k] = self.op(0, value)

class Graph:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_mods = []
        self.edge_mods = []
    def add_node(self, node):
        self.nodes.append(node)
    def add_edge(self, edge):
        self.edges.append(edge)
    def add_node_mod(self, node_mod):
        self.node_mods.append(node_mod)
    def add_edge_mod(self, edge_mod):
        self.edge_mods.append(edge_mod)
