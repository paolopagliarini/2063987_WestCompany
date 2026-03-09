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
    "nodesep": "0.8",
    "ranksep": "1.5",
    "overlap": "false",
    "sep": "+25",
    "compound": "true",
    "rankdir": "TB"
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

    ingestor = Glue("Ingestor")
    broker = Activemq("Event Broker")
    
    with Cluster("Services"):
        rule_manager_service = Docker("Rule Manager Service")
        automation_engine = Docker("Automation Engine")
        actuator_control_service = Docker("Actuator Control Service")
        notification_service = Docker("Notification Service")
        data_history_service = Docker("Data History Service")
        
        # Force horizontal arrangement of services
        rule_manager_service - Edge(style="invis") - automation_engine - Edge(style="invis") - actuator_control_service - Edge(style="invis") - notification_service - Edge(style="invis") - data_history_service
    
    db = PostgreSQL("Database")

    with Cluster("Frontend"):
        frontend = React("Frontend")
    
    sim >> Edge(color="purple") >> ingestor

    ingestor >> Edge(color='purple') >> broker


    # DHS
    broker >> Edge(color='orange') >> data_history_service
    data_history_service >> Edge(color='orange') >> db
    data_history_service >> Edge(color='blue') >> frontend
    db >> Edge(color='orange', style='dotted') >> data_history_service

    ## ACS
    broker >> Edge(color='darkgreen') >> actuator_control_service
    actuator_control_service >> Edge(color='darkgreen') >> sim
    actuator_control_service >> Edge(color='brown') >> db
    db >> Edge(color='brown', style='dotted') >> actuator_control_service
    actuator_control_service >> Edge(color='brown') >> frontend

    ## AE 
    broker >> Edge(color='dark') >> automation_engine
    automation_engine >> Edge(color='darkgreen') >> broker
    db >> Edge(color='green') >> automation_engine
    automation_engine >> Edge(color='blue', style='dotted') >> frontend

    ## NS
    broker >> Edge(color='red') >> notification_service
    notification_service >> Edge(color='red') >> frontend

    ## RMS 
    broker >> Edge(color='darkgreen') >> rule_manager_service
    rule_manager_service >> Edge(color='green') >> db
    rule_manager_service >> Edge(color='blue', style='dotted') >> frontend

    ## Frontend
    frontend >> Edge(color='darkgreen') >> actuator_control_service
    frontend >> Edge(color='green') >> rule_manager_service