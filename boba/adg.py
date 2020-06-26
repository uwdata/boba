
class ADG:
    """ For creating ADG. """
    def __init__(self):
        self.nodes = set()
        self.edges = {}
        self.proc_edges = {}

        self._graph_nodes = set()
        self._graph_edges = {}
        self._links = []    # linked decisions
        self._constraint_proc = set()  # procedural deps from constraints
        self._decs = set()  # all decisions

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
            # print(nd, set(cur))
            gp = self._merge_one(nd, set(cur))

            # if the child node is already in groups, give it a different id
            for g in gp.copy():
                val = gp[g]
                key = '{}-{}'.format(g, i) if g in groups else g
                i += 1 if g in groups else 0
                del gp[g]
                gp[key] = val

            # update the loop
            groups.update(gp)
            nds.extend(gp.keys())

        # print(self.nodes, self.edges)

    def _prune_recur(self, node, nodes, edges):
        """ Recursive helper for prune. Make sure the graph has no cycles! """
        # leaf node
        if node not in self.edges:
            return [node] if node in self._decs else None

        clean = []
        # recursively prune children
        for nd in self.edges[node]:
            ret = self._prune_recur(nd, nodes, edges)
            if ret:
                clean.extend(ret)
            elif len(self.edges[node]) > 1:  # preserve branches
                clean.append(nd)

        # skip if not decision, else add to edges
        if node in self._decs:
            nodes.update(clean)
            nodes.add(node)
            for nd in clean:
                ADG._add_edge(edges, node, nd)
            return [node]
        else:
            return clean

    def _prune(self):
        """ Remove non-decision nodes """
        edges = {}
        nodes = set()
        src = ADG._get_source(self.nodes, self.edges)
        for s in src:
            self._prune_recur(s, nodes, edges)

        # replace nodes and edges
        self.nodes = nodes
        self.edges = edges

    def _get_linked_vars(self, blocks):
        """ Get linked placeholders """
        bd = set([blocks[b].parameter for b in blocks if blocks[b].parameter])
        res = set()
        for l in self._links:
            bls = [b for b in l if b in bd]
            if len(bls):
                # skip all vars if they are linked with blocks
                res.update(set(l).difference(set(bls)))
            else:
                # otherwise, skip all vars except the first
                res.update(l[1:])
        return res

    def set_graph(self, nodes, edges):
        """ Set code graph """
        self._graph_nodes = nodes
        self._graph_edges = ADG._convert_edges(edges)

    def set_constraints(self, links, proc):
        """ Save the intermediate data from constraint parser """
        self._constraint_proc = proc
        self._links = links

    def create(self, blocks):
        """ Create the ADG """
        # abort if ADG has already been created
        if len(self.nodes):
            return

        # add placeholder vars to the code graph
        decs = []
        for bl in blocks:
            # get the variables associated with a block
            vs = [chunk.variable for chunk in blocks[bl].chunks
                  if chunk.variable != '']
            decs.extend(vs)

            # remove linked vars
            linked = self._get_linked_vars(blocks)
            vs = [v for v in vs if v not in linked]

            # remove duplicates within this block
            tmp = []
            [tmp.append(v) for v in vs if v not in tmp]
            vs = tmp

            # skip variables that have appeared in previous blocks
            # fixme
            gp = ADG._group_by(self._graph_nodes, ADG._bn)
            vs = [v for v in vs if v not in gp
                  or gp[v][0].split('-')[1].split(':')[0] == ADG._bn(bl)]

            # name the placeholders differently as distinct nodes for now
            vs = ['{}-{}'.format(v, bl) for v in vs]
            self._graph_nodes.update(vs)

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

        # save all decisions, including placeholders and decision blocks
        bd = set([blocks[b].parameter for b in blocks if blocks[b].parameter])
        self._decs = set(decs).union(bd)

        # infer ADG from the graph
        self._merge()
        self._prune()

        # any branch should be a procedural branch
        for s in self.edges:
            t = self.edges[s]
            if len(t) > 1:
                self.proc_edges[s] = t
        # add the procedural deps from constraint
        for proc in self._constraint_proc:
            s = proc.split('-')[0]
            e = proc.split('-')[1]
            ADG._add_edge(self.proc_edges, s, e)

        # todo: remove linked blocks if they don't have procedural branches

    def get_used_decs(self):
        """ Get the decisions that are used in the ADG """
        return [n for n in self.nodes if n in self._decs]

    def output(self):
        """ Output the graph object in server JSON """
        nodes = []
        edges = []

        # nodes
        i = 0
        lookup = {}
        for n in self.nodes:
            nodes.append({"id": i, "name": n})
            lookup[n] = i
            i += 1

        # first add procedural edges
        done = set()
        for s in self.proc_edges:
            ts = self.edges[s]
            for t in ts:
                done.add('{}->{}'.format(s, t))
                edges.append({"source": lookup[s], "target": lookup[t],
                              "type": "procedural"})

        # add order edges, skip those already added
        for s in self.edges:
            ts = self.edges[s]
            for t in ts:
                if '{}->{}'.format(s, t) not in done:
                    edges.append({"source": lookup[s], "target": lookup[t],
                                  "type": "order"})

        return {"graph": {"nodes": nodes, "edges": edges}}
