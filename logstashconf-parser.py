import lark
from lark import Transformer
import os
import pprint
import pdb
import json

# define the grammar
f = open("logstash.lark", "r")
logstash_grammar = f.read()


# initialize parser and transformer
logstash_parser = lark.Lark(logstash_grammar, parser='earley')


# set directory path
dir_path = './pipelines'

# Function to iterate over the parse tree
def iterate_tree(node, depth=0):
    if not hasattr(node, 'data'):
        #print("  " * depth + str(node.data) )
        #if node.data == "input":
        #    print("input")
    #else:
        print("  " * depth + str(node) )
    
    if hasattr(node, 'children'):
        for child in node.children:
            iterate_tree(child, depth + 1)
            
class MyTransformer(Transformer):
    def array(self, items):
        return list(items)
#    def pair(self, key_value):
#        k, v = key_value
#        return k, v
#    def hash(self, items):
#        return dict(items)
    #pair = tuple
    #hash = dict
    array = list
    null = lambda self, _: None
    true = lambda self, _: True
    false = lambda self, _: False

    
    

def extract_plugin_id(node):
    """Function to extract plugin id from a node"""
    if isinstance(node, lark.Tree) and node.data == 'pair':
        k, v = node.children
        if isinstance(k, lark.Token) and k.value == 'id':
            return v.value.strip('"')
    return None

def extract_plugin_address(node):
    """Function to extract plugin id from a node"""
    if len(node.children)==2:
        node=node.children[1]
        if isinstance(node, lark.Tree) and node.data == 'pair':
            k, v = node.children
            if isinstance(k, lark.Token) and k.value == 'address':
                #print(v.value.strip('"'))
                return v.value.strip('"')
    return None

def extract_plugin_send_to(node):
    """Function to extract plugin id from a node"""
    if len(node.children)==2:
        node=node.children[1]
        if isinstance(node, lark.Tree) and node.data == 'pair':
            k, v = node.children
            if isinstance(k, lark.Token) and k.value == 'send_to':
                return v.value.strip('"').strip('[]')
    return None

def mermaid_node_identifier(node, block_type, file):
    if hasattr(node, 'data') and node.data in ['ifo']:
        block_type = node.children[0].value  # Save the block type (input, filter, output)
    if hasattr(node, 'data') and node.data in ['plugin']:
        plugin_counter[block_type] += 1  # Increment the counter for this block type
        plugin_id = ""
        for child in node.children:
            id_val = extract_plugin_id(child)
            if id_val:
                plugin_id = "-" + id_val
                break
        if block_type == "filter":
            if file != "":
                return f"{block_type}-{node.children[0].value}-{plugin_counter[block_type]}{plugin_id}-{file}", block_type, plugin_counter
        else:
            return f"{block_type}-{node.children[0].value}{plugin_id}", block_type, plugin_counter

    return f"node_{id(node)}", block_type, plugin_counter



    
def to_mermaid(node, parent=None, f_output=None, file=None, block_type="", last_blocktype=""):
    """Recursive function to convert Lark tree into Mermaid Markdown"""
    node_id, block_type,plugin_counter = mermaid_node_identifier(node, block_type, file)
    
    if hasattr(node, 'data'):
        if node.data in ['plugin']:
            
            if block_type == "input":
                block_connections['input'].append(node_id)
                if extract_plugin_address(node) != None:
                    input_pipeline_addresses[extract_plugin_address(node)] = node_id
            elif block_type == "filter":                    
                if block_connections['input'] and not block_connections['filter']:
                    for input_node in block_connections['input']:
                        f_output.write(f"{input_node}-->{node_id}\n")
                else:
                    f_output.write(f"{block_connections['filter'][-1]} --> {node_id}\n")
                block_connections['filter'].append(node_id)
            elif block_type == "output":

                if block_connections['filter']:
                    f_output.write(f"{block_connections['filter'][-1]} --> {node_id}\n")
                    
                elif block_connections['input'] and not block_connections['filter']:
                    f_output.write(f"{block_connections['input'][-1]} --> {node_id}\n")
                if extract_plugin_send_to(node) != None:
                    output_pipeline_addresses[extract_plugin_send_to(node)] = node_id
                block_connections['output'].append(node_id)
    last_blocktype=block_type
    if isinstance(node, lark.Tree):
        for child in node.children:
            if isinstance(child, lark.tree.Tree) and child.data not in ['pair']:
                to_mermaid(child, node_id if node.data in ['plugin'] else parent, f_output, file,  block_type, last_blocktype)

    return node_id, block_type

def to_mermaid_pipeline_connnections(input_pipeline_addresses,output_pipeline_addresses,):
    for inputaddr in input_pipeline_addresses:
        for outputaddr in output_pipeline_addresses:
            if inputaddr == outputaddr:
                f_output.write(f"{output_pipeline_addresses[outputaddr]} --> {input_pipeline_addresses[inputaddr]}\n")

            

input_pipeline_addresses = {}
output_pipeline_addresses = {}

# Create or open the markdown file to write the mermaid diagram
with open('pipelines.md', 'w') as f_output:
    for root, dirs, files in os.walk(dir_path):
        f_output.write('```mermaid\n')
        f_output.write('flowchart TD\n')  # Add diagram type (flowchart)
        
        for file in files:
            if file.endswith('.conf'):
                # Reset plugin_counter and block_connections for each file
                plugin_counter = {
                    'input': 0,
                    'filter': 0,
                    'output': 0,
                }
                block_connections = {
                    'input': [],
                    'filter': [],
                    'output': [],
                }
                
                with open(os.path.join(root, file), 'r') as f:                    
                    data = f.read()
                    tree = logstash_parser.parse(data)
                    transform = MyTransformer().transform(tree)
                    # Start generating mermaid diagram
                    to_mermaid(transform, f_output=f_output,file=file)
        to_mermaid_pipeline_connnections(input_pipeline_addresses,output_pipeline_addresses)
        f_output.write('```\n')

#print(input_pipeline_addresses)
#print(output_pipeline_addresses)