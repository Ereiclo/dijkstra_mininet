#!/usr/bin/python
import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from dijkstra import generate_torus2d,generator_fib,print_graph,dijkstra_graph,generate_torus1d

       

# g = generate_torus1d(9,generator_fib())
g = generate_torus2d(3,generator_fib())
ip_links = [[None for j in range(len(g[0]))] for i in range(len(g))]
ip = ["" for i in range(len(g))]


def new_route(ip,gw,intf):
    via = ""
    if gw != "":
        via =  "via " + gw + " "

    return "ip route add " + ip + " " + via + "dev " + intf


def make_route(net,route,u,v):


    _,_,ip_v,_ = ip_links[route[-2]][route[-1]]


    for i in range(0,len(route)-1):

        r_actual = f"r{route[i]}"

        ip_a,ether,ip_b,_ = ip_links[route[i]][route[i+1]]

        if(i == len(route)-2):
            net[r_actual].cmd(new_route(ip[v],"",ether))
            net[r_actual].cmd(new_route(ip_v,"",ether))
        else:
            net[r_actual].cmd(new_route(ip[v],ip_b,ether))
            net[r_actual].cmd(new_route(ip_v,ip_b,ether))
    
           
    


def create_routing_table(net,u,v):
    route,_ = dijkstra_graph(u,v,g)

    # print(ip[u],ip[v])

    print(f"u: {u}, v: {v}")
    print(route)
    # print(route[::-1])

    print(f"[{ip_links[0][1][0]}, ",end="")
    for i in range(1,len(route)-1):
        _,_,ip_,_ = ip_links[route[i-1]][route[i]]
        print(f"{ip_}, ",end="")
    print(f" {ip[route[-1]]}]")


    make_route(net,route,u,v)
    make_route(net,route[::-1],v,u)
    

 



class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):
    def build(self, **_opts):

        ether_counters = [0 for i in range(len(g))]
        ip_counters = 1

        for u in range(len(g)):
            r_u = f"r{u}"    
            self.addHost(r_u,cls=LinuxRouter,ip=None)

        for u in range(len(g[0])):
            r_u = f"r{u}"
            print(r_u + " esta conectado con: ")
            for v in range(len(g)):
                print(f"r{v} ",end="")
                if g[u][v] == -1 or g[u][v] == 0 or ip_links[u][v] != None:
                    continue

                r_v = f"r{v}"

                ether_u = f"r{u}-eth{ether_counters[u]}"
                ether_v = f"r{v}-eth{ether_counters[v]}"
                ip_u = f"10.0.{ip_counters}.0"
                ip_v = f"10.0.{ip_counters}.1"
                subnet = "/24"

                self.addLink(r_u,r_v,intfName1=ether_u,
                                    intfName2=ether_v,
                                    params1={'ip':ip_u + subnet},
                                    params2={'ip':ip_v + subnet})
                
                if ether_counters[u] == 0:
                    ip[u] = ip_u
                
                if ether_counters[v] == 0:
                    ip[v] = ip_v

                ether_counters[u] += 1
                ether_counters[v] += 1
                ip_counters += 1

                ip_links[u][v] = (ip_u,ether_u,ip_v,ether_v)
                ip_links[v][u] = (ip_v,ether_v,ip_u,ether_u)

            print()



def run():
    topo = NetworkTopo()
    net = Mininet(topo=topo)
    
    for u in range(len(g)):
        for v in range(len(g[0])):
            if u != v:
                create_routing_table(net,u,v)

    net.start()
    CLI(net)
    net.stop()


if __name__ == '__main__':
    run()
