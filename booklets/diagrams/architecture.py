from diagrams import Diagram, Cluster, Edge
from diagrams.generic.compute import Rack
from diagrams.aws.management import SystemsManager
from diagrams.onprem.container import Docker
from diagrams.onprem.queue import Kafka
from diagrams.onprem.queue import Activemq
from diagrams.programming.framework import React
from diagrams.aws.analytics import Glue
from diagrams.onprem.database import PostgreSQL

graph_attr = {
    "fontsize": "16",
    "splines": "ortho",
    "nodesep": "1.2",
    "ranksep": "2",
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
        automation_engine = Docker("Automation Engine")
        actuator_control_service = Docker("Actuator Control Service")
        notification_service = Docker("Notification Service")
        data_history_service = Docker("Data History Service")
        rule_manager_service = Docker("Rule Manager Service")
    
    db = PostgreSQL("Database")

    with Cluster("Frontend"):
        frontend = React("Frontend")
    
    sim >> Edge(color="darkgreen") >> ingestor
    ingestor >> Edge(color='darkgreen', style='dotted') >> sim

    ingestor >> Edge(color='purple') >> broker
    broker >> Edge(color='purple', style='dotted') >> ingestor
    
    broker >> Edge(color='blue') >> frontend

    # DHS
    broker >> Edge(color='red', label='Normalized Event') >> data_history_service
    data_history_service >> Edge(color='brown') >> db

    ## ACS
    broker >> Edge(color='red', label='Actuator Command') >> actuator_control_service
    actuator_control_service >> Edge(color='grey', label='Available Actuators') >> sim
    actuator_control_service >> Edge(color='brown', label='Actuator Commands Logs') >> db
    db >> Edge(color='brown', style='dotted') >> actuator_control_service

    ## AE 
    broker >> Edge(color='red') >> automation_engine
    automation_engine >> Edge(color='red', style='dotted', label='Rule Triggered') >> broker
    automation_engine >> Edge(color='brown') >> db
    db >> Edge(color='brown', style='dotted') >> automation_engine

    ## NS
    broker >> Edge(color='red') >> notification_service
    notification_service >> Edge(color='blue') >> frontend