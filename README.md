I needed a visualization for my pipelines. As i found nothing useful i wrote this script. It will link pipeline to pipeline communication as a connection in the graph. Have a look at the pipelines dir and the resulting Graph. This script ignores conditionals, as they make graphs to complex for now.

>python3 logstashconf-parser.py

Will read through the pipelines directory and create a mermaid diagram that displays the dataflow of the pipelines:

[pipelines.md](./pipelines.md)

You need python3 and lark to run this. Install lark with:
> pip install lark

to get the newest version. 
