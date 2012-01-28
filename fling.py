#!/usr/bin/env python

#
# M. Cadiz (michael.cadiz AT gmail)
# Sat Jan 28 14:40:55 PST 2012
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


def cellstr(row, col, V):
    for v in V:
        if v.row == row and v.col == col:
            return "%2s" % (v.__hash__())
    return "  "


def printGraph(V):
    print "+----+----+----+----+----+----+----+"
    for row in range(8):
        for col in range(7):
            print "| %s" % (cellstr(row, col, V)),
        print "|\n+----+----+----+----+----+----+----+"
    print


def printSolution(G, P):
    for i, p in enumerate(P):
        print "%2s -> %2s\n" % (p[0], p[1])
        printGraph(G[i])


class Stats:
    def __init__(self):
        self.edgesDiscovered = 0
        self.edgesSearched = 0
        self.solutionDepth = 0
        self.backtrackDepth = 0

    def printStats(self):
        print """Edges discovered : %d
Edges searched   : %d
Solution depth   : %d
Backtrack depth  : %d""" % (self.edgesDiscovered, self.edgesSearched,
                            self.solutionDepth, self.backtrackDepth)


class FlingDatabase():
    def __init__(self):
        self.conn = sqlite3.connect('/Users/cadizm/var/fling.db')
        self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()

        c.execute("""create table if not exists fling
                    (id integer primary key asc,
                     puzzle text,
                     graph text,
                     solution text)""")

        self.conn.commit()
        c.close()


    def getSolution(self, V):
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


    def putSolution(self, V, G, P):
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
    def fromhash(h):
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


def applyEdge(e, V):
#    print "applying %s -> %s" % (e[0], e[1])

    W = copy.deepcopy(V)
    src = W[W.index(e[0])]
    dest = W[W.index(e[1])]

    if src.row == dest.row:  # row
        rc = ('row', 'col')
    else:  # col
        rc = ('col', 'row')

    F = filter(lambda x: getattr(x, rc[0]) == getattr(src, rc[0]), V)
    F.sort(key=lambda x: getattr(x, rc[1]))

    if getattr(src, rc[1]) - getattr(dest, rc[1]) < 0:  # right/down
        if abs(getattr(src, rc[1]) - getattr(dest, rc[1])) != 1:  # not adjacent
            setattr(src, rc[1], getattr(dest, rc[1]) - 1)
        if dest == F[-1]:  # if dest is last vertex
            W.remove(dest)
        else:
            return applyEdge((dest, F[F.index(dest) + 1]), W)

    else:  # left/up
        if abs(getattr(src, rc[1]) - getattr(dest, rc[1])) != 1:  # not adjacent
            setattr(src, rc[1], getattr(dest, rc[1]) + 1)
        if dest == F[0]:  # if dest is first vertex
            W.remove(dest)
        else:
            return applyEdge((dest, F[F.index(dest) - 1]), W)

    return W


# return list of vertices adjacent to v in V
def adjacentVertices(v, V):
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


# edges are the legal row/col moves
def findEdges(V):
    E = []
    for u in V:
        for v in adjacentVertices(u, V):
            if u.row == v.row and abs(u.col - v.col) > 1:
                E.append((u, v))
            if u.col == v.col and abs(u.row - v.row) > 1:
                E.append((u, v))
    return E


def solve(V, G, P, s):
    if len(V) == 1:
        return Status.SUCCESS

    E = findEdges(V)
    s.edgesDiscovered += len(E)

    for e in E:
        s.edgesSearched += 1
        W = applyEdge(e, V)
        G.append(W)
        P.append(e)
        if solve(W, G, P, s):
            s.solutionDepth += 1
            return Status.SUCCESS
        else:
            s.backtrackDepth += 1
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

    printGraph(V)

    db = FlingDatabase()
    (G, P) = db.getSolution(V)

    if P == Status.NO_SOLUTION:
        print "Using cached..."
        print "No solution found"
    elif P:
        print "Using cached solution..."
        printSolution(G, P)
    else:
        print "Solving..."
        if solve(V, G, P, Stats()):
            db.putSolution(V, G, P)
            printSolution(G, P)
        else:
            db.putSolution(V, [], Status.NO_SOLUTION)
            print "No solution found"
