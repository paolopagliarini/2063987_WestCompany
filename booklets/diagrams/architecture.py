from diagrams import Diagram, Cluster, Edge
from diagrams.generic.compute import Rack
from diagrams.aws.management import SystemsManager
from diagrams.onprem.container import Docker
from diagrams.onprem.queue import Kafka
from diagrams.onprem.queue import Activemq
from diagrams.programming.framework import React
from diagrams.aws.analytics import Glue

graph_attr = {
    "fontsize": "16",
    "splines": "ortho",
    "nodesep": "1.2",
    "ranksep": "1.5",
    "overlap": "false",
    "sep": "+25",
    "compound": "true"
}

with Diagram(
    "Project Architecture", 
    filename="booklets/diagrams/asset/Diagram", 
    show=False, 
    direction="TB",      
    graph_attr=graph_attr
):
    with Cluster("Environment Simulator"):
        sim = SystemsManager("IoT Simulator")

    with Cluster("Data Handling"):
        ingestor = Glue("Ingestor")
        broker = Activemq("Event Broker")
    
    with Cluster("Services"):
        service_a = Docker("Service A")
        service_b = Docker("Service B")

    with Cluster("Frontend"):
        frontend = React("Frontend")

    service_a >> Edge(style="dashed", color="red", constraint="false") >> sim
    service_b >> Edge(style="dashed", color="red", constraint="false") >> sim
    
    sim >> Edge(color="darkgreen") >> ingestor
    ingestor >> broker
    
    broker >> service_a
    broker >> service_b
    broker >> Edge(color="blue") >> frontend