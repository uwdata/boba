
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
        if start in res:
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

    @staticmethod
    def _dn(name):
        """ Get the placeholder decision name """
        return name.split('-')[0]

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
        done = set()
        i = 0
        while len(nds) and i < 100: #fixme
            nd = nds.pop()

            # skip already processed nodes
            # fixme
            # we do not handle the case when a block is used multiple times
            # or when a placeholder appear in multiple blocks
            if nd in done:
                continue

            cur = [self._graph_edges[n] for n in groups[nd] if n in self._graph_edges]
            # find procedural edges
            if len(cur):
                tmp = [set([ADG._dn(n) for n in l]) for l in cur]
                diff = set.union(*tmp) - set.intersection(*tmp)
                if len(diff):
                    gp = ADG._group_by(diff, ADG._bn)
                    for k in gp.keys():
                        ADG._add_edge(self.proc_edges, nd, k)

            # flatten
            cur = [item for sublist in cur for item in sublist]
            print(nd, set(cur))
            gp = self._merge_one(nd, set(cur))

            # update the loop
            groups.update(gp)
            nds.extend(gp.keys())
            done.add(nd)
            i += 1
        print(self.nodes, self.edges, self.proc_edges)

    def set_graph(self, nodes, edges):
        """ Set code graph """
        self._graph_nodes = nodes
        self._graph_edges = ADG._convert_edges(edges)

    def create(self, blocks):
        """ Create the ADG """
        print(self._graph_edges)
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
        print(self._graph_edges)
        self._merge()
