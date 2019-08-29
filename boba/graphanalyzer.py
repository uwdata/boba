# -*- coding: utf-8 -*-


class InvalidGraphError(NameError):
    pass


class GraphAnalyzer:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = GraphAnalyzer._convert_edges(edges)
        self.paths = []

    @staticmethod
    def _convert_edges(edges):
        d = {}
        for e in edges:
            if e.start in d:
                d[e.start].append(e.end)
            else:
                d[e.start] = [e.end]
        return d

    def _throw(self, msg):
        msg = 'In analyzing graph structure:\n\t' + msg
        raise InvalidGraphError(msg)

    def _all_ending_nodes(self):
        """ nodes that have at least one incoming edge(s) """
        flat = [item for lst in self.edges.values() for item in lst]
        return set(flat)

    def _get_source(self):
        """ nodes that have no incoming edges """
        return self.nodes.difference(self._all_ending_nodes())

    def _get_target(self):
        """ nodes that have no outgoing edges """
        return self.nodes.difference(set(self.edges.keys()))

    def _all_paths_recur(self, a, b, visited, path):
        """ a recursive func to get all paths from a to b"""
        # mark the current node as visited and add to path
        visited.add(a)
        path.append(a)

        # if current node is the same as target, the path is done
        if a == b:
            self.paths.append([nd for nd in path])
        else:
            if a in self.edges:
                for n in self.edges[a]:
                    if n not in visited:
                        self._all_paths_recur(n, b, visited, path)

        # remove current node from path and mark it as unvisited
        path.pop()
        visited.discard(a)

    def _all_paths(self, s, t):
        """ get all paths from s to t """
        visited = set()
        path = []
        self._all_paths_recur(s, t, visited, path)

    def _construct_paths(self):
        ss = self._get_source()
        ts = self._get_target()

        if len(ss) == 0:
            self._throw('Cannot find any starting node')
        if len(ts) == 0:
            self._throw('Cannot find any ending node')

        for s in ss:
            for t in ts:
                self._all_paths(s, t)

    def analyze(self):
        if len(self.nodes) == 0:
            return []

        self._construct_paths()
        return self.paths
