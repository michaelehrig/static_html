import re
import os
import shutil

from textnode import TextType, TextNode
from enum import Enum

def delete_directory(directory_path):
    if not os.path.exists(directory_path):
        os.mkdir(directory_path)
        return
    else:
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    print(f"Removed file: {filename}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Removed subdirectory: {filename}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

def copy_directory(source, destination):
    try:
        # Check if the source directory exists
        if not os.path.exists(source):
            print(f"Error: Source directory not found at '{source}'")
            return
        
        if not os.path.exists(destination):
            print(f'Creating directory: {destination}')
            os.mkdir(destination)

        directory_content = os.listdir(source)

        for content in directory_content:
            content_source = os.path.join(source, content)
            content_destination = os.path.join(destination, content)
            if os.path.isfile(content_source):
                shutil.copy(content_source,content_destination)
            else:
                copy_directory(content_source, content_destination) 

    except shutil.Error as e:
        print(f"Directory copying failed: {e}")
    except OSError as e:
        print(f"Operating system error: {e}")
        
def prepare_directory(source, destination):
    delete_directory(destination)
    copy_directory(source, destination)
    return

class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"

class HTMLNode:
    def __init__(self, tag=None, value=None, children=None, props=None):
        self.tag = tag
        self.value = value
        self.children = children
        self.props = props
        
    def to_html(self):
        raise NotImplementedError
    
    def props_to_html(self):
        if self.props != None and self.props != {}:
            formatted = ""
            for key in self.props.keys():
                formatted += f' {key}="{self.props[key]}"' 
            return formatted
        else:
            return ""

    def __repr__(self):
        return f"HTMLNode \n Tag: {self.tag}, Value: {self.value}, Children: {self.children}, Props: {self.props}"    

class LeafNode(HTMLNode):
    def __init__(self, tag, value, props=None):
        super().__init__(tag, value, None, props)
        
    def to_html(self):
        if self.value == None:
            raise ValueError
        if self.tag == None:
            return self.value
        return "<" + self.tag + self.props_to_html() + ">" + self.value + "</" + self.tag + ">"

    def __repr__(self):
        return f"LeafNode \n Tag: {self.tag}, Value: {self.value}, Props: {self.props}"    

class ParentNode(HTMLNode):
    def __init__(self, tag, children, props=None):
        super().__init__(tag, None, children, props)
        
    def to_html(self):
        if self.tag == None:
            raise ValueError("tag missing in parent node")
        elif self.children == None:
            raise ValueError("children missing in parent node")

        output = "<" + self.tag + ">"
        for child in self.children:
            output += child.to_html()
        output += f"</{self.tag}>\n"
        
        return output

    def __repr__(self):
        return f"ParentNode \n Tag: {self.tag}, Children: {self.children}, Props: {self.props}"    

def text_node_to_html_node(text_node):
    if text_node.text_type == TextType.PLAIN:
        return LeafNode(None, text_node.text)
    elif text_node.text_type == TextType.BOLD:
        return LeafNode("b", text_node.text)
    elif text_node.text_type == TextType.ITALIC:
        return LeafNode("i", text_node.text)
    elif text_node.text_type == TextType.CODE:
        return LeafNode("code", text_node.text)
    elif text_node.text_type == TextType.LINK:
        return LeafNode("a", text_node.text, {"href" : text_node.url})
    elif text_node.text_type == TextType.IMAGE:
        return LeafNode("img", text_node.text , {"src" : text_node.url})
    else:
        raise ValueError("LeafType unknown")
    
def split_nodes_delimiter(old_nodes, delimiter, text_type):
    node_list = []
    for node in old_nodes:
        if node.text_type == TextType.PLAIN:
            split_node_text = node.text.split(delimiter)
            if len(split_node_text) % 2 == 0:
                raise ValueError("Invalid markdown syntax")
             
            type_checker = lambda a: TextType.PLAIN if a % 2 == 0 else text_type
            node_list.extend([TextNode(part, type_checker(count)) for count, part in enumerate(split_node_text)])
        else:
            node_list.append(node)
    return node_list

def extract_markdown_images(text):
   return re.findall(r"!\[(.*?)\]\((.*?)\)", text)

def extract_markdown_links(text):
   return re.findall(r"(?<!!)\[(.*?)\]\((.*?)\)", text)

def split_nodes_image(old_nodes):
    node_list = []
    for current_node in old_nodes:
        if current_node.text_type != TextType.PLAIN:
            node_list.append(current_node)
        else:
            current_text = current_node.text        

            images = extract_markdown_images(current_text)
            if images == []:
                node_list.append(TextNode(current_text, TextType.PLAIN))
            else:
                for image_alt, image_link in images:
                    sections = current_text.split(f"![{image_alt}]({image_link})", 1)
                    if sections[0] != "":
                        node_list.append(TextNode(sections[0], TextType.PLAIN))
                    
                    node_list.append(TextNode(image_alt, TextType.IMAGE, url=image_link))
                    current_text = sections[1]

                if current_text != "":
                    node_list.append(TextNode(current_text, TextType.PLAIN))
                        
    return node_list

def split_nodes_link(old_nodes):
    node_list = []
    for current_node in old_nodes:
        if current_node.text_type != TextType.PLAIN:
            node_list.append(current_node)
        else:
            current_text = current_node.text        

            links = extract_markdown_links(current_text)
            if links == []:
                node_list.append(TextNode(current_text, TextType.PLAIN))
            else:
                for link_text, link_url in links:
                    sections = current_text.split(f"[{link_text}]({link_url})", 1)
                    if sections[0] != "":
                        node_list.append(TextNode(sections[0], TextType.PLAIN))
                    
                    node_list.append(TextNode(link_text, TextType.LINK, url=link_url))
                    current_text = sections[1]

                if current_text != "":
                    node_list.append(TextNode(current_text, TextType.PLAIN))
                        
    return node_list

def text_to_textnodes(text):
    nodes = [TextNode(text, TextType.PLAIN)]
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "*", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_image(nodes)
    return nodes

def markdown_to_blocks(markdown):
    sections = markdown.split("\n\n")
    sections = [s.strip() for s in sections]
    sections = [s for s in sections if s != ""]
    return sections

def block_to_block_type(block):
    if block.startswith(('# ', '## ', '### ', '#### ', '##### ', '###### ')) and not "\n" in block:
        return BlockType.HEADING
    if block.startswith('```\n') and block.endswith('```'):
        return BlockType.CODE
    if block.startswith('> '):
        block_lines = block.split('\n')
        correct_start = True
        for line in block_lines:
            if not line.startswith('> ') and not line == '>':
                correct_start = False
        if correct_start:
            return BlockType.QUOTE
    if block.startswith('- ') and not re.search(r"\n(?!- )", block):
        return BlockType.UNORDERED_LIST
    if block.startswith('1. ') and not re.search(r"\n(?!\d+\. )", block):
        verify = all([int(num.strip().strip('.')) == i + 2 for i,num in enumerate(re.findall(r"\n\d+\. ", block))])
        if verify:
            return BlockType.ORDERED_LIST
    return BlockType.PARAGRAPH

def text_to_children(text):
    text_nodes = text_to_textnodes(text)
    html_nodes = []
    for text_node in text_nodes:
        html_nodes.append(text_node_to_html_node(text_node))
    return html_nodes

def markdown_to_html_node(markdown):
    blocks = markdown_to_blocks(markdown)
    block_nodes = []
    for block in blocks:
        if block_to_block_type(block) == BlockType.PARAGRAPH:
            block = block.replace('\n',' ')
            block_nodes.append(ParentNode('p', text_to_children(block)))
        elif block_to_block_type(block) == BlockType.HEADING:
            heading_type = str(len(re.findall(r"\#+ ", block)[0].strip()))
            block_nodes.append(ParentNode(f'h{heading_type}', text_to_children(block.lstrip('#').lstrip())))
        elif block_to_block_type(block) == BlockType.CODE:
            block = block.lstrip('```').rstrip('```').lstrip()
            block_nodes.append(ParentNode('pre',[ParentNode('code', [LeafNode(None, block)])]))
        elif block_to_block_type(block) == BlockType.ORDERED_LIST:
            block = block.lstrip('1. ')
            item_sequence = re.split(r"\n\d+\. ", block)
            sequence_nodes = []
            for item in item_sequence:
                sequence_nodes.append(ParentNode('li',text_to_children(item)))
            block_nodes.append(ParentNode('ol', sequence_nodes))
        elif block_to_block_type(block) == BlockType.UNORDERED_LIST:
            block = block.lstrip('- ')
            item_sequence = block.split("\n- ")
            sequence_nodes = []
            for item in item_sequence:
                sequence_nodes.append(ParentNode('li',text_to_children(item)))
            block_nodes.append(ParentNode('ul', sequence_nodes))
        elif block_to_block_type(block) == BlockType.QUOTE:
            block = block.lstrip('> ')
            item_sequence = block.split("\n>")
            sequence_nodes = []
            for item in item_sequence:
                item = item.lstrip()
                sequence_nodes.extend(text_to_children(item))
            block_nodes.append(ParentNode('blockquote', sequence_nodes))
        
    return ParentNode('div', block_nodes)

def extract_title(html):
    titles = re.findall(r"\<h1\>(.+)\<\/h1\>", html)
    if titles == []:
        raise Exception('No title found')
    else: 
        return titles[0]

def generate_page(from_path, template_path, dest_path, basepath):
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")
    try:
        with open(from_path, 'r', encoding='utf-8') as f:
            markdown = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{from_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
 
    try:
        with open(template_path, 'r', encoding='utf-8') as t:
            template = t.read()
    except FileNotFoundError:
        print(f"Error: The file '{template_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    html = markdown_to_html_node(markdown).to_html()
    html = html.replace('href="/', f'href="{basepath}')
    html = html.replace('src="/', f'src="{basepath}')
    title = extract_title(html)
    template = template.replace("{{ Title }}", title).replace("{{ Content }}", html)

    try:
        with open(dest_path, 'w', encoding='utf-8') as d:
            d.write(template)
    except FileNotFoundError:
        print(f"Error: The file '{dest_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_pages_recursive(dir_path_content, template_path, dest_path_path, basepath):
    try:
        # Check if the source directory exists
        if not os.path.exists(dir_path_content):
            print(f"Error: Source directory not found at '{dir_path_content}'")
            return
        
        if not os.path.exists(dest_path_path):
            print(f'Creating directory: {dest_path_path}')
            os.mkdir(dest_path_path)

        directory_content = os.listdir(dir_path_content)

        for content in directory_content:
            content_source = os.path.join(dir_path_content, content)
            if os.path.isfile(content_source):
                base, extension = os.path.splitext(content)
                destination = base + '.html'
                content_destination = os.path.join(dest_path_path, destination)
                generate_page(content_source, template_path, content_destination, basepath)
            else:
                content_destination = os.path.join(dest_path_path, content)
                generate_pages_recursive(content_source, template_path, content_destination, basepath) 
    except OSError as e:
        print(f"Operating system error: {e}")