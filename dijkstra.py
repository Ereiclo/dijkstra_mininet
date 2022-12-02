import random
import heapq
# --------------------------------------------
#               WEIGHT GENERATORS
# --------------------------------------------
def generator_fib():
    prev    = 0
    current = 1
    while True:
        yield current
        prev, current = current, prev+current

def generator_rand(low, high):
    while True:
        yield random.randint(low,high)

# --------------------------------------------
#                    UTILITY
# --------------------------------------------
def init_graph(n):
    return  [[-1 if x!=y else 0 for x in range(n)] for y in range(n)]

def print_graph(g):
    print("GRAPH")
    for row in g:
        for cell in row:
            print(cell, end="\t")
        print()

# --------------------------------------------
#              TORUS GENERATORS
# --------------------------------------------

def generate_torus1d(k, weight_generator):
    n = k
    graph = init_graph(n)

    for i in range(k):
        node_a =  i
        node_b = (i+1) % k
        weight = next(weight_generator)
        graph[node_a][node_b] = weight
        graph[node_b][node_a] = weight
        #print("a:{}<->b:{} - W:{} ".format(node_a, node_b, weight))
    
    return graph

def generate_torus2d(k, weight_generator):
    n = k**2
    graph = init_graph(n)

    for y in range(k):
        for x in range(k):
            node_a = (y*k) +  x       
            node_b = (y*k) + (x+1) % k
            weight = next(weight_generator)
            graph[node_a][node_b] = weight
            graph[node_b][node_a] = weight
            #print("a:{}<->b:{} - W:{} ".format(node_a, node_b, weight))

    for x in range(k):
        for y in range(k):
            node_a = x + k * y
            node_b = x + k * ((y+1) % k)
            weight = next(weight_generator)
            graph[node_a][node_b] = weight
            graph[node_b][node_a] = weight
            #print("a:{}<->b:{} - W:{} ".format(node_a, node_b, weight))
    
    return graph

# --------------------------------------------
#                    DIJKSTRA
# --------------------------------------------
def dijkstra_graph(src, dst, graph):
    n = len(graph)
    distance = [-1 if v!= src else 0 for v in range(n)]
    visited = [False for _ in range(n)]
    parent = [-1 for _ in range(n)]
    priorityqueue  = []

    heapq.heappush(priorityqueue, (0, src))

    while priorityqueue:
        _, node = heapq.heappop(priorityqueue)
        
        if visited[node] == True:
            continue
        visited[node] = True

        for i in range(n):
            edge =  graph[node][i]
            if edge != -1:
                dist = distance[node] + edge
                if distance[i] == -1:
                    distance[i] = dist
                    parent[i] = node
                    heapq.heappush(priorityqueue, (distance[i],i))
                elif distance[i] > dist:
                    distance[i] = dist
                    parent[i] = node
                    heapq.heappush(priorityqueue, (distance[i],i))
    

    if distance[dst] == -1:
        return [], -1
    else:
        node = dst
        route = []
        while node != -1:
            route.append(node)
            node = parent[node]
        route.reverse()
        return route, distance[dst]



# --------------------------------------------
#                     MAIN
# --------------------------------------------


if __name__ == "__main__":
    fib1 = generator_fib()
    fib2 = generator_fib()
    #ran1 = generator_rand(0,10)
    #ran2 = generator_rand(0,10)

    print("TORUS 1D:")
    g1 = generate_torus1d(9, fib1)
    # g1 = generate_torus2d(9, ran1)
    print_graph(g1)
    print("TORUS 2D:")
    g2 = generate_torus2d(3, fib2)
    #g2 = generate_torus2d(3, ran2)
    print_graph(g2)

    print(dijkstra_graph(3-1,7-1,g1))
    print(dijkstra_graph(3-1,7-1,g2))
