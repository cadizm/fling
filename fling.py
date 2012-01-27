#!/usr/bin/env python

#
# M. Cadiz (michael.cadiz AT gmail)
# Wed Jan 25 00:05:49 PST 2012
#

#
# TODO: Python Imaging Library (PIL) to parse
# initial grid position from an image?
#
# Cache input vertices and return known solutions (memoize)?
#

#    0   1   2   3   4   5   6
#  +---+---+---+---+---+---+---+
# 0| A |   |   |   | B |   |   |
#  +---+---+---+---+---+---+---+
# 1| C |   |   |   |   |   |   |
#  +---+---+---+---+---+---+---+
# 2| D |   | E |   |   |   |   |
#  +---+---+---+---+---+---+---+
# 3|   |   |   |   |   | F | G |
#  +---+---+---+---+---+---+---+
# 4|   |   |   |   |   |   | H |
#  +---+---+---+---+---+---+---+
# 5|   |   |   | I |   | J |   |
#  +---+---+---+---+---+---+---+
# 6|   | K |   |   | L |   |   |
#  +---+---+---+---+---+---+---+
# 7|   |   |   |   |   |   |   |
#  +---+---+---+---+---+---+---+

import copy


class Stats:
    def __init__(self):
        self.edgesDiscovered = 0
        self.edgesSearched = 0
        self.solutionDepth = 0
        self.backtrackDepth = 0


class Status:
    FAILURE = 0
    SUCCESS = 1


class Vertex:
    def __init__(self, name, row, col):
        self.name = name
        self.row = row
        self.col = col

    def __eq__(self, other):
        return self.name == other.name and \
            self.row == other.row and self.col == other.col

    def __ne__(self, other):
        return self.name != other.name or \
            self.row != other.row or self.col != other.col

    def __str__(self):
        return "%s(%d,%d)" % (self.name, self.row, self.col)

    def __hash__(self):
        return self.row * 7 + self.col  # 7 columns


def cellstr(row, col, L):
    for n in L:
        if n.row == row and n.col == col:
            return n.name
    return " "


def drawGrid(L):
    print "+---+---+---+---+---+---+---+"
    for row in range(8):
        for col in range(7):
            print "| %s" % (cellstr(row, col, L)),
        print "|\n+---+---+---+---+---+---+---+"
    print


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

    V = [Vertex("A", 0, 0),
         Vertex("B", 0, 4),
         Vertex("C", 1, 0),
         Vertex("D", 2, 0),
         Vertex("E", 2, 2),
         Vertex("F", 3, 5),
         Vertex("G", 3, 6),
         Vertex("H", 4, 6),
         Vertex("I", 5, 3),
         Vertex("J", 5, 5),
         Vertex("K", 6, 1),
         Vertex("L", 6, 4)]

    h = reduce(lambda x, y: "%s-%s" % (x, y), sorted([v.__hash__() for v in V]))

    G = []
    P = []
    s = Stats()

    drawGrid(V)

    if solve(V, G, P, s):
        if len(G) != len(P):
            print "Error constructing path"
        else:
            for i, p in enumerate(P):
                print "%s -> %s\n" % (p[0], p[1])
                drawGrid(G[i])
            print """Edges discovered : %d
Edges searched   : %d
Solution depth   : %d
Backtrack depth  : %d""" % (s.edgesDiscovered, s.edgesSearched, s.solutionDepth, s.backtrackDepth)
    else:
        print "No solution found"
