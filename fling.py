#!/usr/bin/env python

#
# M. Cadiz (michael.cadiz AT gmail)
# Sat Apr 21 21:08:12 PDT 2012
#

#     0    1    2    3    4    5    6
#  +----+----+----+----+----+----+----+
# 0|  0 |    |    |    |    |  5 |    |
#  +----+----+----+----+----+----+----+
# 1|    |    |    |    |    |    |    |
#  +----+----+----+----+----+----+----+
# 2|    |    |    |    |    |    |    |
#  +----+----+----+----+----+----+----+
# 3|    |    |    |    |    | 26 |    |
#  +----+----+----+----+----+----+----+
# 4|    |    |    | 31 | 32 |    |    |
#  +----+----+----+----+----+----+----+
# 5|    | 36 |    |    | 39 |    | 41 |
#  +----+----+----+----+----+----+----+
# 6|    | 43 | 44 |    |    |    |    |
#  +----+----+----+----+----+----+----+
# 7| 49 | 50 | 51 |    |    |    |    |
#  +----+----+----+----+----+----+----+

import copy
import json
import sqlite3
import logging
import time


logging.basicConfig(filename='/tmp/fling.log',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class PuzzleTooExpensiveError(Exception):
    pass


class Status:
    FAILURE = 0
    SUCCESS = 1
    NO_SOLUTION = "NO_SOLUTION"
    TOO_EXPENSIVE = "TOO_EXPENSIVE"


class Stats:
    def __init__(self):
        self.edges_discovered = 0
        self.edges_searched = 0
        self.solution_depth = 0
        self.backtrack_depth = 0

    def print_stats(self):
        print """Edges discovered : %d
Edges searched   : %d
Solution depth   : %d
Backtrack depth  : %d""" % (self.edges_discovered, self.edges_searched,
                            self.solution_depth, self.backtrack_depth)


class FlingDatabase():
    def __init__(self):
        self.conn = sqlite3.connect('/tmp/fling.db')
        self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()

        c.execute("""create table if not exists fling
                    (id integer primary key asc,
                     puzzle text,
                     graph text,
                     solution text)""")

        self.conn.commit()
        c.close()

    def get_solution(self, V):
        # Sort V in order to lookup correct key
        p = json.dumps(sorted(V), cls=VertexEncoder, separators=(',', ':'))
        c = self.conn.cursor()

        c.execute("select * from fling where puzzle = ? limit 1", (p,))
        r = c.fetchone()
        c.close()

        if r:
            if r['solution'] == Status.NO_SOLUTION:
                return [], Status.NO_SOLUTION
            else:
                return (json.loads(r['graph'], object_hook=Vertex.json_hook),
                        json.loads(r['solution'], object_hook=Vertex.json_hook))
        else:
            return [], []

    def put_solution(self, V, G, P):
        # Sort V in order to put correct key
        p, g, s = json.dumps(sorted(V), cls=VertexEncoder, separators=(',', ':')), '', P

        if P != Status.NO_SOLUTION:
            g = json.dumps(G, cls=VertexEncoder, separators=(',', ':'))
            s = json.dumps(P, cls=VertexEncoder, separators=(',', ':'))

        c = self.conn.cursor()
        c.execute("insert into fling (puzzle, graph, solution) values (?, ?, ?)", (p, g, s))
        self.conn.commit()
        c.close()


class Vertex:
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col

    def __ne__(self, other):
        return self.row != other.row or self.col != other.col

    def __cmp__(self, other):
        if self.row < other.row:
            return -1
        elif self.row == other.row:
            if self.col < other.col:
                return -1
            elif self.col == other.col:
                return 0
            else:
                return 1
        else:
            return 1

    def __str__(self):
        return "%2s (%d, %d)" % (self.__hash__(), self.row, self.col)

    def __hash__(self):
        return self.row * 7 + self.col  # 7 columns

    @staticmethod
    def from_hash(h):
        return Vertex(h / 7, h % 7)

    @staticmethod
    def json_hook(v):
        return Vertex(v['r'], v['c'])


class VertexEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Vertex):
            return { 'r': o.row, 'c': o.col }
        else:
            return json.JSONEncoder(self, o)


def cellstr(row, col, V):
    for v in V:
        if v.row == row and v.col == col:
            return "%2s" % (v.__hash__())
    return "  "


def graph_to_json(V):
    return json.dumps(V, cls=VertexEncoder, separators=(',', ':'))


def print_graph(V):
    print "+----+----+----+----+----+----+----+"
    for row in range(8):
        for col in range(7):
            print "| %s" % (cellstr(row, col, V)),
        print "|\n+----+----+----+----+----+----+----+"
    print


def print_solution(G, P):
    for i, p in enumerate(P):
        print "%2s -> %2s\n" % (p[0], p[1])
        print_graph(G[i])


def apply_edge(e, V):
    W = copy.deepcopy(V)
    src = W[W.index(e[0])]
    dest = W[W.index(e[1])]

    if src.row == dest.row:
        rc = ('row', 'col')
    else:
        rc = ('col', 'row')

    F = filter(lambda x: getattr(x, rc[0]) == getattr(src, rc[0]), V)
    F.sort(key=lambda x: getattr(x, rc[1]))

    # right/down
    if getattr(src, rc[1]) - getattr(dest, rc[1]) < 0:
        # not adjacent
        if abs(getattr(src, rc[1]) - getattr(dest, rc[1])) != 1:
            setattr(src, rc[1], getattr(dest, rc[1]) - 1)
        # if dest is last vertex
        if dest == F[-1]:
            W.remove(dest)
        else:
            return apply_edge((dest, F[F.index(dest) + 1]), W)

    # left/up
    else:
        # not adjacent
        if abs(getattr(src, rc[1]) - getattr(dest, rc[1])) != 1:
            setattr(src, rc[1], getattr(dest, rc[1]) + 1)
        # if dest is first vertex
        if dest == F[0]:
            W.remove(dest)
        else:
            return apply_edge((dest, F[F.index(dest) - 1]), W)

    return W


def adjacent_vertices(v, V):
    "Return list of vertices adjacent to v in V"
    A  = []
    for u in V:
        if u == v:
            for rc in [('row', 'col'), ('col', 'row')]:
                F = filter(lambda x: getattr(x, rc[0]) == getattr(v, rc[0]), V)
                F.sort(key=lambda x: getattr(x, rc[1]))
                i = F.index(u)
                if i - 1 >= 0:
                    A.append(F[i - 1])
                if i + 1 < len(F):
                    A.append(F[i + 1])
    return A


def find_edges(V):
    "Return the edges in V -- the legal row/col moves"
    E = []
    for u in V:
        for v in adjacent_vertices(u, V):
            if u.row == v.row and abs(u.col - v.col) > 1:
                E.append((u, v))
            if u.col == v.col and abs(u.row - v.row) > 1:
                E.append((u, v))
    return E


def _solve(V, G, P, s):
    "Internal `solve'. Clients should use `solve()'"
    if len(V) == 1:
        return Status.SUCCESS

    E = find_edges(V)
    s.edges_discovered += len(E)

    for e in E:
        if int(time.clock()) > 7:
            raise PuzzleTooExpensiveError
        s.edges_searched += 1
        W = apply_edge(e, V)
        G.append(W)
        P.append(e)
        if _solve(W, G, P, s):
            s.solution_depth += 1
            return Status.SUCCESS
        else:
            s.backtrack_depth += 1
            G.pop()
            P.pop()

    return Status.FAILURE


def solve(p):
    """Solve puzzle p.

    p should be a graph in json string format.

    A 2-tuple of json strings `(G, P)' is returned if a solution is found.

    If p cannot be parsed or if a solution is not found, a 2-tuple of empty
    strings is returned.

    If the puzzle is deemed `TOO_EXPENSIVE', the 2-tuple [], 'TOO_EXPENSIVE'
    is returned.

    G is an array of graphs representing the puzzle transitions.

    P is an array of `paths' that should be followed in order to reach
    the solution represented by (thus len(G) == len(P)).

    A path is a 2-tuple of vertices ((x0, y0), (x1, y1)) representing a
    given move in G (e.g. move (x0, y0) -> (x1, y1)).

    """

    logging.info('solve: %s' % p)

    db = FlingDatabase()

    try:
        V = json.loads(p, object_hook=Vertex.json_hook)
    except ValueError:
        return '', ''
    except:
        return '', ''

    G, P = db.get_solution(V)

    if P == Status.NO_SOLUTION:
        return '', ''
    elif P:
        return (json.dumps(G, cls=VertexEncoder, separators=(',', ':')),
                json.dumps(P, cls=VertexEncoder, separators=(',', ':')))
    else:
        try:
            if _solve(V, G, P, Stats()):
                db.put_solution(V, G, P)
                return (json.dumps(G, cls=VertexEncoder, separators=(',', ':')),
                        json.dumps(P, cls=VertexEncoder, separators=(',', ':')))
            else:
                db.put_solution(V, [], Status.NO_SOLUTION)
                return '', ''
        except PuzzleTooExpensiveError:
            logging.error('PuzzleTooExpensiveError: %s' % p)
            return '', Status.TOO_EXPENSIVE
        except:
            logging.error('Unknown Error: %s' % p)
            return '', ''


if __name__ == '__main__':
#    V = [Vertex(0, 0),
#         Vertex(0, 1),
#         Vertex(0, 2),
#         Vertex(1, 1),
#         Vertex(2, 1),
#         Vertex(2, 3),
#         Vertex(3, 2),
#         Vertex(3, 6),
#         Vertex(4, 2),
#         Vertex(4, 3),
#         Vertex(4, 6),
#         Vertex(5, 4),
#         Vertex(5, 5),
#         Vertex(6, 0)]
#    solve(json.dumps(sorted(V), cls=VertexEncoder, separators=(',', ':')))

    V = '[{"c":5,"r":0},{"c":1,"r":1},{"c":6,"r":2},{"c":1,"r":4},{"c":2,"r":4},{"c":3,"r":4},{"c":4,"r":4},{"c":6,"r":4},{"c":1,"r":5},{"c":2,"r":5},{"c":0,"r":6},{"c":2,"r":6},{"c":3,"r":6},{"c":2,"r":7}]'
    solve(V)

    V = json.loads(V, object_hook=Vertex.json_hook)
    G, P = FlingDatabase().get_solution(V)

    print_graph(V)
    print_solution(G, P)
