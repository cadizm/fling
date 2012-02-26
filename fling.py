#!/usr/bin/env python

#
# M. Cadiz (michael.cadiz AT gmail)
# Sat Feb 25 16:09:49 PST 2012
#

#
# TODO: Python Imaging Library (PIL) to parse
# initial graph position from an image?
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


class Status:
    FAILURE = 0
    SUCCESS = 1
    NO_SOLUTION = "NO_SOLUTION"


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
        self.conn = sqlite3.connect('fling.db')
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
        p = json.dumps(sorted(V), cls=VertexEncoder, separators=(',', ':'))
        c = self.conn.cursor()

        c.execute("select * from fling where puzzle = ? limit 1", (p,))
        r = c.fetchone()
        c.close()

        if r:
            if r['solution'] == Status.NO_SOLUTION:
                return ([], Status.NO_SOLUTION)
            else:
                return (json.loads(r['graph'], object_hook=Vertex.json_hook),
                        json.loads(r['solution'], object_hook=Vertex.json_hook))
        else:
            return ([], [])

    def put_solution(self, V, G, P):
        (p, g, s) = (json.dumps(sorted(V), cls=VertexEncoder, separators=(',', ':')), '', P)

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
        return Vertex(v['row'], v['col'])


class VertexEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Vertex):
            return { 'row': o.row, 'col': o.col }
        else:
            return json.JSONEncoder(self, o)


def cellstr(row, col, V):
    for v in V:
        if v.row == row and v.col == col:
            return "%2s" % (v.__hash__())
    return "  "


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


def solve(V, G, P, s):
    if len(V) == 1:
        return Status.SUCCESS

    E = find_edges(V)
    s.edges_discovered += len(E)

    for e in E:
        s.edges_searched += 1
        W = apply_edge(e, V)
        G.append(W)
        P.append(e)
        if solve(W, G, P, s):
            s.solution_depth += 1
            return Status.SUCCESS
        else:
            s.backtrack_depth += 1
            G.pop()
            P.pop()

    return Status.FAILURE


if __name__ == '__main__':

    V = [Vertex(0, 0),
         Vertex(0, 5),
         Vertex(3, 5),
         Vertex(4, 3),
         Vertex(4, 4),
         Vertex(5, 1),
         Vertex(5, 4),
         Vertex(5, 6),
         Vertex(6, 1),
         Vertex(6, 2),
         Vertex(7, 0),
         Vertex(7, 1),
         Vertex(7, 2)]

    print_graph(V)

    db = FlingDatabase()
    (G, P) = db.get_solution(V)

    if P == Status.NO_SOLUTION:
        print "Using cached..."
        print "No solution found"
    elif P:
        print "Using cached solution..."
        print_solution(G, P)
    else:
        print "Solving..."
        if solve(V, G, P, Stats()):
            db.put_solution(V, G, P)
            print_solution(G, P)
        else:
            db.put_solution(V, [], Status.NO_SOLUTION)
            print "No solution found"
