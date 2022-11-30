#!/usr/bin/python
import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink,TCIntf
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from dijkstra import generate_torus2d,generator_fib,print_graph,dijkstra_graph,generate_torus1d

       


g = None #Grafo de la topologia

ip_links = None #Diccionario donde ip_links[u][v] guarda la tupla (ip_u,ether_u,ip_v,ether_v) 
                #para la conexion directa entre u y v 
ip = None #Arreglo que asocia ip[i] la ip para el i-esimo router

#crea la string ip route add (ip) via (gateway) dev (intf)
#esta string es el comando que se le pasa a la terminal de un router
def new_route(ip,gw,intf): 
                            
    via = ""
    if gw != "":
        via =  "via " + gw + " "

    return "ip route add " + ip + " " + via + "dev " + intf 

#crea la ruta entre u y v usando la string new_route() en la consola del router
def make_route(net,route,u,v):


    _,_,ip_v,_ = ip_links[route[-2]][route[-1]] #conseguir la ip de v para la última conexion del camino


    for i in range(0,len(route)-1): #recorrer todo el camino route

        r_actual = f"r{route[i]}" #string para el router route[i]

        ip_a,ether,ip_b,_ = ip_links[route[i]][route[i+1]] #consige la conexion entre ri y ri+1

        if(i == len(route)-2):#si llegamos a los ultimos dos nodos en el camino
                                #no hay necesidad de usar una gateway
            net[r_actual].cmd(new_route(ip[v],"",ether))
            net[r_actual].cmd(new_route(ip_v,"",ether))
        else:
            net[r_actual].cmd(new_route(ip[v],ip_b,ether)) #se agrega la ruta de r_actual hacia ip[v]
            net[r_actual].cmd(new_route(ip_v,ip_b,ether)) #se agrega la ruta de r_actual hacia ip_v
    
           
    


def create_routing_table(net,u,v):
    route,_ = dijkstra_graph(u,v,g)


    #imprimir la ruta de u a v en consola
    print(f"u: {u}, v: {v}")
    print(route)

    print(f"[{ip_links[route[0]][route[1]][0]}, ",end="")
    for i in range(1,len(route)-1):
        _,_,ip_,_ = ip_links[route[i-1]][route[i]]
        print(f"{ip_}, ",end="")
    print(f" {ip[route[-1]]}]")


    #crea el camino u...v
    make_route(net,route,u,v)
    #crea el camino v...u
    make_route(net,route[::-1],v,u)
    

 



class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')#configuraciones para convertir un host a router
                                                #activar forwading 
    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0') #desactivar forwarding cuando se apague el sistema
        super(LinuxRouter, self).terminate()


#Topologia que se crea en base a un grafo g
class NetworkTopo(Topo):
    def build(self, **_opts):

        ether_counters = [0 for i in range(len(g))] #ether_counters[i] es el numero actual para la nueva
                                                    #interfaz del router i
        ip_counters = 1

        for u in range(len(g)): #crear todos los routers (nodos) que hay en el grafo g 
            r_u = f"r{u}"    
            self.addHost(r_u,cls=LinuxRouter,ip=None)

        for u in range(len(g[0])): #recorrer todas las aristas {u,v} del grafo g y hacer la conexion fisica
                                    # u<->v correspondiente
            r_u = f"r{u}"
            print(r_u + " esta conectado con: ")
            for v in range(len(g)):
                if g[u][v] != -1:#imprimir con quien se conecta solo si existe la conexion
                    print(f"r{v} ",end="")
                if g[u][v] == -1 or g[u][v] == 0 or ip_links[u][v] != None:#si la arista ya se reviso
                                                                        #o no hay conexion, continuar
                    continue                                             #con la siguiente iteracion
                    

                r_v = f"r{v}"

                ether_u = f"r{u}-eth{ether_counters[u]}" #nombre que se asociara para la interfaz
                                                            #de u en la conexion
                ether_v = f"r{v}-eth{ether_counters[v]}"#nombre que se asociara para interfaz
                                                            #de v en la conexion
                ip_u = f"10.0.{ip_counters}.0"          #subnet creada para la conexion u<->v
                ip_v = f"10.0.{ip_counters}.1"
                subnet = "/24"#mascara
                peso = g[u][v]#peso de la arista

                # print(1000/peso,peso/50,str(peso*2) + 'ms',end=" ")


                #crear el link con un bandwidth de 1000/peso y delay peso*2 ms
                #hacer que los links con aristas de mayor peso tengan menos troughtput
                self.addLink(r_u,r_v,intfName1=ether_u,
                                    intfName2=ether_v,
                                    params1={'ip':ip_u + subnet},
                                    # params2={'ip':ip_v + subnet},cls=TCLink,bw=1000/peso,loss=peso/50,delay= str(peso*2) + 'ms')#delay='500ms')
                                    params2={'ip':ip_v + subnet},cls=TCLink,bw=1000/peso,loss=0,delay= str(peso*2) + 'ms')#delay='500ms')

                #si es la primera vez que creamos una interfaz para u
                #guardar la ip de esa interfaz como la ip del router u
                if ether_counters[u] == 0:
                    ip[u] = ip_u
                
                #si es la primera vez que creamos una interfaz para v
                #guardar la ip de esa interfaz como la ip del router v
                if ether_counters[v] == 0:
                    ip[v] = ip_v

                
                ether_counters[u] += 1 #aumentar el numero de la siguiente interfaz para u
                ether_counters[v] += 1 #aumentar el numero de la siguiente interfaz para u
                ip_counters += 1 #aumentar ip de la subnet para un link entre dos nodos

                ip_links[u][v] = (ip_u,ether_u,ip_v,ether_v) #guardar la conexion fisica u,v
                ip_links[v][u] = (ip_v,ether_v,ip_u,ether_u) #guardar la conexion fisica v,u

            print()



def run():
    topo = NetworkTopo()
    net = Mininet(topo=topo)#crear una instancia de mininet con la topologia NetworkTopo
    
    for u in range(len(g)): #por cada par u v buscar el camino óptimo
        for v in range(len(g[0])):
            if u != v: #si no son el mismo nodo
                create_routing_table(net,u,v) #crear la tabla con el camino optimo entre u y v

    net.start() #iniciar mininet
    CLI(net)
    net.stop()#terminar mininet


if __name__ == '__main__':
    t1 = generate_torus1d(9,generator_fib()) #generar torus1d
    t2 = generate_torus2d(3,generator_fib()) #generar torus2d


    g = t2

    if len(sys.argv) > 1 :

        if sys.argv[1] == "1d":
            g = t1
            print("Creando torus 1d...")
        elif sys.argv[1] == "2d":
            print("Creando torus 2d...")
        else:
            print("Parametro desconocido usando valor por defecto (2d)")
    else:
        print("Creando valor por defecto (2d)...")


    ip_links =  [[None for j in range(len(g[0]))] for i in range(len(g))]
    ip = ["" for i in range(len(g))]


    run()
