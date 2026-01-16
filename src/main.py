import sys

from textnode import TextNode, TextType
from htmlnode import generate_pages_recursive, prepare_directory




def main():
    if len(sys.argv) > 1:
        basepath = sys.argv[1]
    else:
        basepath = '/'
    
    prepare_directory('./static','./docs')
    generate_pages_recursive('./content', 'template.html', './docs', basepath)

            
if __name__ == "__main__":
    main()