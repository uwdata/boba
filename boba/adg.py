
class ADG:
    """ For creating ADG. """
    def __init__(self):
        self.nodes = set()
        self.edges = {}
        self.proc_edges = {}

        self._graph_nodes = set()
        self._graph_edges = {}
        self._decs = set()  # all placeholder variables

    @staticmethod
    def _convert_edges(edges):
        d = {}
        for e in edges:
            ADG._add_edge(d, e.start, e.end)
        return d

    @staticmethod
    def _add_edge(res, start, end):
        if start in res and end not in res[start]:
            res[start].append(end)
        else:
            res[start] = [end]

    @staticmethod
    def _all_ending_nodes(edges):
        """ nodes that have at least one incoming edge(s) """
        flat = [item for lst in edges.values() for item in lst]
        return set(flat)

    @staticmethod
    def _get_source(nodes, edges):
        """ nodes that have no incoming edges """
        return nodes.difference(ADG._all_ending_nodes(edges))

    @staticmethod
    def _get_target(nodes, edges):
        """ nodes that have no outgoing edges """
        return nodes.difference(set(edges.keys()))

    @staticmethod
    def _group_by(lst, func):
        res = {}
        for item in lst:
            k = func(item)
            ADG._add_edge(res, k, item)
        return res

    @staticmethod
    def _bn(name):
        """ Get the block decision name """
        return name.split('-')[0].split(':')[0]

    def _merge_one(self, prev, cur):
        groups = ADG._group_by(cur, ADG._bn)
        if prev:
            self.nodes.add(prev)
            for k in groups.keys():
                ADG._add_edge(self.edges, prev, k)
                self.nodes.add(k)
        return groups

    def _merge(self):
        """ Merge alternatives """
        src = ADG._get_source(self._graph_nodes, self._graph_edges)
        groups = self._merge_one(None, src)
        nds = list(groups.keys())
        i = 0
        while len(nds):
            nd = nds.pop()

            # look up the alternatives, then restore the correct node id
            alts = groups[nd]
            nd = nd.split('-')[0]

            # find the children of all alts of this node and perform merge
            cur = [self._graph_edges[n] for n in alts if n in self._graph_edges]
            cur = [item for sublist in cur for item in sublist]
            print(nd, set(cur))
            gp = self._merge_one(nd, set(cur))

            # if the child node is already in groups, give it a different id
            for g in gp:
                val = gp[g]
                key = '{}-{}'.format(g, i) if g in groups else g
                i += 1 if g in groups else 0
                del gp[g]
                gp[key] = val

            # update the loop
            groups.update(gp)
            nds.extend(gp.keys())

        # any branch should be a procedural branch
        for s in self.edges:
            t = self.edges[s]
            if len(t) > 1:
                self.proc_edges[s] = t

    def set_graph(self, nodes, edges):
        """ Set code graph """
        self._graph_nodes = nodes
        self._graph_edges = ADG._convert_edges(edges)

    def create(self, blocks):
        """ Create the ADG """
        # add placeholder vars to the code graph
        decs = []
        for bl in blocks:
            # get the variables associated with a block
            vs = [chunk.variable for chunk in blocks[bl].chunks
                  if chunk.variable != '']
            decs.extend(vs)

            # name the placeholders differently as distinct nodes for now
            vs = ['{}-{}'.format(v, bl) for v in vs]

            # move children of block to the last var
            vs = [bl] + vs
            last = vs[len(vs) - 1]
            if bl in self._graph_edges:
                temp = self._graph_edges[bl]
                self._graph_edges[bl] = []
                self._graph_edges[last] = temp

            # add edges between vars
            for i in range(len(vs) - 1):
                ADG._add_edge(self._graph_edges, vs[i], vs[i + 1])

        self._decs = set(decs)
        self._merge()
