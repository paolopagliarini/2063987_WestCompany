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
        frontend_formatter = Docker("Frontend Formatter")
        actuator_control_service = Docker("Actuator Control Service")

    with Cluster("Frontend"):
        frontend = React("Frontend")
    
    sim >> Edge(color="darkgreen") >> ingestor
    ingestor >> Edge(color='darkgreen', style='dotted') >> sim

    ingestor >> Edge(color='purple') >> broker
    broker >> Edge(color='purple', style='dotted') >> ingestor
    
    broker >> Edge(color='blue') >> frontend

    broker >> frontend_formatter
    broker >> actuator_control_service

    frontend_formatter >> Edge(style='dotted') >> broker
    actuator_control_service >> Edge(style='dotted') >> broker